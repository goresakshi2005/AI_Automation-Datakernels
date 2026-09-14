import re
from pathlib import Path

from playwright.sync_api import Page

from config import (
    SCREENSHOT_DIR,
    SCROLL_BEFORE_SCREENSHOT,
    SCROLL_TIMEOUT_MS,
    SCROLL_SETTLE_MS,
)

_INVALID = re.compile(r"[^A-Za-z0-9._-]+")


def _safe(text: str) -> str:
    return _INVALID.sub("_", text).strip("_")


def _normalize_label(test_id: str, label: str) -> str:
    """
    Turn "TC-001_step-26_success" -> "success" so the final filename
    stays clean:  TC-001_step-26_success.png
    """
    if not label:
        return ""
    prefix = f"{test_id}_"
    if label.startswith(prefix):
        label = label[len(prefix):]
    label = re.sub(r"^step-\d+_?", "", label)
    return _safe(label)


# ---------------------------------------------------------------------------
# Focus / scroll helpers  (the real Bug #1 fix for small error elements)
# ---------------------------------------------------------------------------
def _candidate_testids(test_id: str) -> list[str]:
    """
    Given a focus testid, return a list of fallbacks to try, in order.

    For a validation-error testid like `booking-guests-error`, we also try
    the corresponding input (`booking-guests-input`). Scrolling to the input
    naturally shows the error message sitting directly beneath it, which is
    a good second-best framing when the tiny error element itself is hard
    to centre cleanly.
    """
    candidates = [test_id]
    if test_id.endswith("-error"):
        candidates.append(test_id[: -len("-error")] + "-input")
    return candidates


def _force_center_scroll(page: Page, test_id: str) -> bool:
    """
    Scroll the element with the given data-testid to the CENTRE of the
    viewport.

    Why centre and not 'into view'?
      Playwright's default `scroll_into_view_if_needed()` uses the browser's
      minimum-scroll behaviour. For a small element (like a one-line error
      paragraph) this can leave the element pinned to the very bottom of
      the viewport, clipped, or hidden behind the sticky navbar. Centring
      guarantees it's fully visible regardless of viewport size.

    Returns True on success, False if the element couldn't be found / shown.
    """
    try:
        loc = page.get_by_test_id(test_id).first
        if loc.count() == 0:
            return False
        # Ensure it's attached + visible before scrolling to it.
        loc.wait_for(state="visible", timeout=SCROLL_TIMEOUT_MS)
        loc.evaluate(
            "el => el.scrollIntoView({block: 'center', inline: 'nearest', "
            "behavior: 'instant'})"
        )
        page.wait_for_timeout(SCROLL_SETTLE_MS)
        return True
    except Exception:
        return False


def _focus_element(page: Page, test_id: str) -> None:
    """Try each candidate testid in order; stop at first success."""
    if not test_id:
        return
    for candidate in _candidate_testids(test_id):
        if _force_center_scroll(page, candidate):
            return
    # If nothing worked, don't fail the screenshot - just proceed with the
    # current viewport. (A missing focus target is not a test failure.)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def capture_screenshot(
    page: Page,
    test_id: str,
    step_number: int,
    label: str = "",
    scroll_target: str | None = None,
) -> str:
    """
    Save a screenshot under:
        screenshots/run_<RUN_ID>/<test_id>/<test_id>_step-NN[_label].png

    If `scroll_target` is provided, that element (or a nearby fallback) is
    centred in the viewport before the screenshot.
    """
    if SCROLL_BEFORE_SCREENSHOT and scroll_target:
        _focus_element(page, scroll_target)

    test_dir = Path(SCREENSHOT_DIR) / test_id
    test_dir.mkdir(parents=True, exist_ok=True)

    clean = _normalize_label(test_id, label)
    suffix = f"_{clean}" if clean else ""
    filename = f"{test_id}_step-{step_number:02d}{suffix}.png"
    filepath = test_dir / filename

    page.screenshot(path=str(filepath), full_page=False)
    return str(filepath)