from playwright.sync_api import Page

from config import (
    DEFAULT_TIMEOUT,
    SHORT_TIMEOUT,
    POST_ACTION_SETTLE_MS,
    NETWORK_IDLE_TIMEOUT_MS,
    ANIMATION_SETTLE_TIMEOUT_MS,
)


# ---------------------------------------------------------------------------
# Element-level waits (deterministic, tied to real app state)
# ---------------------------------------------------------------------------
def wait_for_visible(page: Page, test_id: str, timeout: int = DEFAULT_TIMEOUT) -> None:
    page.get_by_test_id(test_id).first.wait_for(state="visible", timeout=timeout)


def wait_for_hidden(page: Page, test_id: str, timeout: int = DEFAULT_TIMEOUT) -> None:
    page.get_by_test_id(test_id).first.wait_for(state="hidden", timeout=timeout)


def wait_for_attached(page: Page, test_id: str, timeout: int = DEFAULT_TIMEOUT) -> None:
    page.get_by_test_id(test_id).first.wait_for(state="attached", timeout=timeout)


def wait_for_url_contains(page: Page, fragment: str, timeout: int = DEFAULT_TIMEOUT) -> None:
    page.wait_for_url(f"**{fragment}**", timeout=timeout)


# ---------------------------------------------------------------------------
# Page-level waits (bounded, best-effort)
# ---------------------------------------------------------------------------
def wait_for_document_ready(page: Page, timeout: int = DEFAULT_TIMEOUT) -> None:
    """React has hydrated and DOM is fully parsed."""
    try:
        page.wait_for_function(
            "() => document.readyState === 'complete'",
            timeout=timeout,
        )
    except Exception:
        pass


def wait_for_network_settled(
    page: Page,
    timeout: int = NETWORK_IDLE_TIMEOUT_MS,
    idle_ms: int = POST_ACTION_SETTLE_MS,
) -> None:
    """
    Bounded 'network quiet' wait. Used sparingly - NOT after every action.
    Never blocks longer than `timeout`.
    """
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass
    # tiny React flush buffer after network goes quiet
    page.wait_for_timeout(idle_ms)


def wait_for_animations(page: Page, timeout: int = ANIMATION_SETTLE_TIMEOUT_MS) -> None:
    """Wait until all CSS/JS animations have stopped running."""
    try:
        page.wait_for_function(
            "() => document.getAnimations().filter(a => a.playState === 'running').length === 0",
            timeout=timeout,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Composite settle used after every step (Bug #1)
# ---------------------------------------------------------------------------
def wait_after_step(page: Page, parsed: dict, next_parsed: dict | None = None) -> None:
    """
    Synchronisation strategy:

        ACTION  ->  WAIT FOR RELEVANT APPLICATION STATE  ->  SCREENSHOT

    Look-ahead trick: if the *next* step is an explicit `WAIT_FOR: X`
    (this is how the Excel test data already encodes "what should appear"),
    we proactively wait for X here so that the CURRENT step's screenshot
    is not taken mid-load.
    """
    command = (parsed or {}).get("command")

    # --- Look-ahead: honour the next step's WAIT_FOR as our settle signal ---
    if next_parsed and next_parsed.get("command") == "WAIT_FOR":
        target = next_parsed.get("target")
        if target:
            try:
                page.get_by_test_id(target).first.wait_for(
                    state="visible", timeout=DEFAULT_TIMEOUT
                )
            except Exception:
                # Don't fail the current step - the WAIT_FOR step itself
                # will produce the correct failure if the element never shows.
                pass

    # --- Command-specific settling -----------------------------------------
    if command == "OPEN":
        wait_for_document_ready(page)
        wait_for_network_settled(page)
        wait_for_animations(page)

    elif command == "CLICK":
        # Click may trigger a route change OR just a local React state update.
        # Bounded network wait covers both, then let animations finish.
        wait_for_network_settled(page, timeout=SHORT_TIMEOUT)
        wait_for_animations(page)

    elif command in ("FILL", "CLEAR", "SELECT"):
        # Controlled inputs re-render synchronously; short settle is enough.
        page.wait_for_timeout(POST_ACTION_SETTLE_MS)

    elif command in ("ASSERT_VISIBLE", "ASSERT_TEXT", "WAIT_FOR"):
        # Element wait already happened inside the command itself.
        wait_for_animations(page, timeout=1_000)

    else:
        # SCREENSHOT or unknown -> just make sure animations are quiet.
        wait_for_animations(page, timeout=1_000)