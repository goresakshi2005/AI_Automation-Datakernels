import re
from pathlib import Path

from playwright.sync_api import Page

from config import SCREENSHOT_DIR

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


def capture_screenshot(
    page: Page,
    test_id: str,
    step_number: int,
    label: str = "",
) -> str:
    """
    Save a screenshot under:
        screenshots/run_<RUN_ID>/<test_id>/<test_id>_step-NN[_label].png
    Returns the absolute path as a string (safe for JSON serialization).
    """
    test_dir = Path(SCREENSHOT_DIR) / test_id
    test_dir.mkdir(parents=True, exist_ok=True)

    clean = _normalize_label(test_id, label)
    suffix = f"_{clean}" if clean else ""
    filename = f"{test_id}_step-{step_number:02d}{suffix}.png"
    filepath = test_dir / filename

    page.screenshot(path=str(filepath), full_page=False)
    return str(filepath)