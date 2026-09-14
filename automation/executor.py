from playwright.sync_api import Page, expect
from typing import Dict, Any

from config import BASE_URL
from waits import wait_for_visible, wait_after_step


def execute_step(page: Page, parsed_step: Dict[str, Any]) -> None:
    """
    Executes a single parsed step. Raises on failure.
    (Unchanged from Part 2 except SCREENSHOT is documented as a no-op here -
     the actual capture happens in main.py so that EVERY step gets a shot.)
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
        val = value if value is not None else ""
        page.get_by_test_id(target).fill(val)

    elif command == "CLICK":
        if not target:
            raise ValueError(f"Target missing for command {command}")
        page.get_by_test_id(target).click()

    elif command == "WAIT_FOR":
        if not target:
            raise ValueError(f"Target missing for command {command}")
        wait_for_visible(page, target)

    elif command == "ASSERT_VISIBLE":
        if not target:
            raise ValueError(f"Target missing for command {command}")
        expect(page.get_by_test_id(target)).to_be_visible()

    elif command == "ASSERT_TEXT":
        if not target:
            raise ValueError(f"Target missing for command {command}")
        expect(page.get_by_test_id(target)).to_contain_text(value if value else "")

    elif command == "SELECT":
        if not target:
            raise ValueError(f"Target missing for command {command}")
        page.get_by_test_id(target).select_option(value)

    elif command == "CLEAR":
        if not target:
            raise ValueError(f"Target missing for command {command}")
        page.get_by_test_id(target).clear()

    elif command == "SCREENSHOT":
        # No-op here. main.py always captures a per-step screenshot.
        pass

    else:
        raise ValueError(f"Unsupported command: {command}")


def settle_after_step(page: Page, parsed: dict, next_parsed: dict | None = None) -> None:
    """Public wrapper so main.py doesn't import waits directly (keeps coupling low)."""
    wait_after_step(page, parsed, next_parsed)