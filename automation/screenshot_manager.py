import os
from playwright.sync_api import Page
from config import SCREENSHOT_DIR

def capture_screenshot(page: Page, test_id: str, step_number: int, step_name: str = "") -> str:
    """
    Captures a screenshot of the current page state.
    Returns the absolute path to the saved screenshot.
    """
    test_dir = os.path.join(SCREENSHOT_DIR, test_id)
    os.makedirs(test_dir, exist_ok=True)
    
    # Format: step-01.png or step-01_home.png
    safe_step_name = f"_{step_name}" if step_name else ""
    filename = f"step-{step_number:02d}{safe_step_name}.png"
    filepath = os.path.join(test_dir, filename)
    
    page.screenshot(path=filepath, full_page=False)
    
    return filepath
