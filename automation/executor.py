import traceback
from playwright.sync_api import Page, expect
from typing import Dict, Any

from config import BASE_URL
from waits import wait_for_visible

def execute_step(page: Page, parsed_step: Dict[str, Any]) -> None:
    """
    Executes a single parsed step using Playwright.
    Raises an exception if the step fails.
    """
    command = parsed_step.get("command")
    target = parsed_step.get("target")
    value = parsed_step.get("value")

    if not command:
        raise ValueError("Invalid step: No command found.")

    if command == "OPEN":
        url = BASE_URL + (target if target else "/")
        page.goto(url)
    
    elif command == "FILL":
        if not target:
            raise ValueError(f"Target missing for command {command}")
        # value can be empty string in case of empty input validation
        val = value if value is not None else ""
        locator = page.get_by_test_id(target)
        locator.fill(val)
        
    elif command == "CLICK":
        if not target:
            raise ValueError(f"Target missing for command {command}")
        locator = page.get_by_test_id(target)
        locator.click()
        
    elif command == "WAIT_FOR":
        if not target:
            raise ValueError(f"Target missing for command {command}")
        wait_for_visible(page, target)
        
    elif command == "ASSERT_VISIBLE":
        if not target:
            raise ValueError(f"Target missing for command {command}")
        locator = page.get_by_test_id(target)
        expect(locator).to_be_visible()
        
    elif command == "ASSERT_TEXT":
        if not target:
            raise ValueError(f"Target missing for command {command}")
        locator = page.get_by_test_id(target)
        expect(locator).to_contain_text(value if value else "")
        
    elif command == "SELECT":
        if not target:
            raise ValueError(f"Target missing for command {command}")
        locator = page.get_by_test_id(target)
        locator.select_option(value)
        
    elif command == "CLEAR":
        if not target:
            raise ValueError(f"Target missing for command {command}")
        locator = page.get_by_test_id(target)
        locator.clear()
        
    elif command == "SCREENSHOT":
        # Handled by main runner logic since it needs test context (test_id, step_number)
        pass
        
    else:
        raise ValueError(f"Unsupported command: {command}")
