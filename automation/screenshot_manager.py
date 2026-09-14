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


def _try_scroll_into_view(page: Page, test_id: str) -> bool:
    """
    Scroll the element with the given data-testid into the viewport.
    This is the *real* Bug #1 fix: without it, Playwright auto-scrolls
    to the submit button (bottom of the form) and any validation errors
    rendered at the top of the form are simply not in the viewport when
    the screenshot is taken.
    """
    try:
        loc = page.get_by_test_id(test_id).first
        if loc.count() == 0:
            return False
        loc.scroll_into_view_if_needed(timeout=SCROLL_TIMEOUT_MS)
        # Tiny buffer so the scroll position is reflected in the next paint.
        page.wait_for_timeout(SCROLL_SETTLE_MS)
        return True
    except Exception:
        return False


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

    If `scroll_target` is provided, that element is scrolled into view
    (and given a tiny settle buffer) before the screenshot is taken.

    Returns the absolute path as a string (safe for JSON serialization).
    """
    if SCROLL_BEFORE_SCREENSHOT and scroll_target:
        _try_scroll_into_view(page, scroll_target)

    test_dir = Path(SCREENSHOT_DIR) / test_id
    test_dir.mkdir(parents=True, exist_ok=True)

    clean = _normalize_label(test_id, label)
    suffix = f"_{clean}" if clean else ""
    filename = f"{test_id}_step-{step_number:02d}{suffix}.png"
    filepath = test_dir / filename

    page.screenshot(path=str(filepath), full_page=False)
    return str(filepath)