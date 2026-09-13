from playwright.sync_api import Page
from config import DEFAULT_TIMEOUT

def wait_for_visible(page: Page, test_id: str, timeout: int = DEFAULT_TIMEOUT):
    """Waits for an element with the given test_id to be visible."""
    page.get_by_test_id(test_id).wait_for(state="visible", timeout=timeout)

def wait_for_hidden(page: Page, test_id: str, timeout: int = DEFAULT_TIMEOUT):
    """Waits for an element with the given test_id to be hidden."""
    page.get_by_test_id(test_id).wait_for(state="hidden", timeout=timeout)

def wait_for_page_ready(page: Page):
    """Waits for the page to reach network idle state."""
    page.wait_for_load_state("networkidle")
