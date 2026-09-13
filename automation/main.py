import traceback
from playwright.sync_api import sync_playwright

from excel_reader import load_test_cases
from step_parser import parse_step
from executor import execute_step
from screenshot_manager import capture_screenshot
from models import TestExecutionResult

def run_tests():
    print("=" * 40)
    print("AI HOTEL TEST AUTOMATION")
    print("=" * 40)
    print("")

    try:
        test_cases = load_test_cases()
    except Exception as e:
        print(f"Failed to load test cases: {e}")
        return

    results = []
    passed = 0
    failed = 0

    with sync_playwright() as p:
        # Note: Set headless=False for manual verification, True for CI
        browser = p.chromium.launch(headless=False)
        
        for test_case in test_cases:
            print(f"Running {test_case.test_id}...")
            
            context = browser.new_context()
            page = context.new_page()
            
            steps = test_case.raw_steps.strip().split('\n')
            
            test_status = "PASS"
            test_error = None
            executed_steps = []
            test_screenshots = []
            
            step_number = 1
            for raw_step in steps:
                if not raw_step.strip():
                    continue
                    
                parsed = parse_step(raw_step)
                if not parsed:
                    continue

                step_result = {
                    "step_number": step_number,
                    "command": parsed.get("command"),
                    "target": parsed.get("target"),
                    "value": parsed.get("value"),
                    "status": "PASS",
                    "screenshot": None,
                    "error": None
                }
                
                try:
                    execute_step(page, parsed)
                    
                    if parsed.get("command") == "SCREENSHOT":
                        target_name = parsed.get("target", f"step_{step_number}")
                        screenshot_path = capture_screenshot(page, test_case.test_id, step_number, target_name)
                        step_result["screenshot"] = screenshot_path
                        test_screenshots.append(screenshot_path)
                    
                except Exception as e:
                    step_result["status"] = "FAIL"
                    step_result["error"] = str(e)
                    test_status = "FAIL"
                    test_error = str(e)
                    
                    try:
                        screenshot_path = capture_screenshot(page, test_case.test_id, step_number, "failure")
                        step_result["screenshot"] = screenshot_path
                        test_screenshots.append(screenshot_path)
                    except:
                        pass
                        
                    executed_steps.append(step_result)
                    break
                    
                executed_steps.append(step_result)
                step_number += 1
                
            print(test_status)
            if test_status == "PASS":
                passed += 1
            else:
                failed += 1
                print(f"  Error: {test_error}")
                
            results.append(TestExecutionResult(
                test_id=test_case.test_id,
                test_name=test_case.test_name,
                status=test_status,
                expected_result=test_case.expected_result,
                actual_result="Success" if test_status == "PASS" else test_error,
                steps=executed_steps,
                screenshots=test_screenshots,
                error=test_error
            ))
            
            context.close()
            
        browser.close()

    print("")
    print("=" * 40)
    print("SUMMARY")
    print("=" * 40)
    print(f"Total Tests: {len(test_cases)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("=" * 40)
    print("Note: AI verification is not enabled in Part 2.")

if __name__ == "__main__":
    run_tests()
