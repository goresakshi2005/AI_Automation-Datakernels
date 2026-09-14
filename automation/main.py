import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from config import (
    BASE_URL,
    EXCEL_FILE,
    HEADLESS,
    SCREENSHOT_DIR,
)
from excel_reader import load_test_cases
from step_parser import parse_step
from executor import execute_step, settle_after_step
from screenshot_manager import capture_screenshot
from models import StepResult, TestExecutionResult
from waits import wait_for_animations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _human_step_label(parsed: dict, raw: str) -> str:
    cmd = parsed.get("command", "?")
    tgt = parsed.get("target")
    val = parsed.get("value")
    if cmd == "FILL" and tgt is not None:
        return f"{cmd}: {tgt} = {val if val else ''}"
    if tgt:
        return f"{cmd}: {tgt}"
    return raw.strip()


def _briefly_settle_for_failure(page) -> None:
    """Give the app a moment to render an error UI before the FAILED screenshot."""
    try:
        page.wait_for_timeout(200)
        wait_for_animations(page, timeout=1_000)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Single test-case runner
# ---------------------------------------------------------------------------
def run_one_test(browser, test_case) -> TestExecutionResult:
    context = browser.new_context()
    page = context.new_page()

    raw_lines = [ln for ln in test_case.raw_steps.splitlines() if ln.strip()]
    parsed_steps = []
    for line in raw_lines:
        p = parse_step(line)
        if p:
            parsed_steps.append((line.strip(), p))

    step_results: list[StepResult] = []
    test_status = "PASS"
    failure_reason = None
    test_start = time.perf_counter()

    total = len(parsed_steps)

    for idx, (raw_step, parsed) in enumerate(parsed_steps, start=1):
        next_parsed = parsed_steps[idx][1] if idx < total else None

        sr = StepResult(
            step_number=idx,
            command=parsed.get("command", "?"),
            raw_step=raw_step,
            target=parsed.get("target"),
            value=parsed.get("value"),
        )

        step_start = time.perf_counter()
        try:
            # 1. Execute the action
            execute_step(page, parsed)

            # 2. Wait for the app to reach a relevant, stable state (Bug #1 fix)
            settle_after_step(page, parsed, next_parsed)

            # 3. Screenshot after EVERY step
            label = ""
            if parsed.get("command") == "SCREENSHOT" and parsed.get("target"):
                label = parsed["target"]
            sr.screenshot_path = capture_screenshot(
                page, test_case.test_id, idx, label
            )

            sr.status = "PASS"
            print(f"  [OK]  Step {idx}/{total}  {_human_step_label(parsed, raw_step)}")

        except Exception as e:
            sr.status = "FAIL"
            sr.error_message = str(e)
            test_status = "FAIL"
            failure_reason = (
                f"Step {idx} ({parsed.get('command')}): {e}"
            )

            # Failure screenshot
            _briefly_settle_for_failure(page)
            try:
                sr.screenshot_path = capture_screenshot(
                    page, test_case.test_id, idx, "FAILED"
                )
            except Exception:
                pass

            print(f"  [FAIL] Step {idx}/{total}  {_human_step_label(parsed, raw_step)}")
            print(f"         -> {e}")
            if sr.screenshot_path:
                print(f"         -> screenshot: {sr.screenshot_path}")

        finally:
            sr.duration_ms = int((time.perf_counter() - step_start) * 1000)
            step_results.append(sr)

        # Stop executing further steps of this test on failure, but
        # DO NOT abort the whole run - the caller moves to the next test.
        if sr.status == "FAIL":
            break

    test_duration_ms = int((time.perf_counter() - test_start) * 1000)

    if test_status == "PASS":
        print(f"  PASS  ({len(step_results)} steps, {test_duration_ms/1000:.1f}s)")
    else:
        print(f"  FAIL  ({len(step_results)} steps, {test_duration_ms/1000:.1f}s)")

    context.close()

    return TestExecutionResult(
        test_id=test_case.test_id,
        test_name=test_case.test_name,
        category=test_case.category,
        expected_result=test_case.expected_result,
        status=test_status,
        step_results=step_results,
        failure_reason=failure_reason,
        duration_ms=test_duration_ms,
        ai_status="NOT RUN",
        ai_observation=None,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def run_tests() -> list[TestExecutionResult]:
    print("=" * 60)
    print("AI HOTEL TEST AUTOMATION - PART 3 (Stage 1)")
    print("=" * 60)
    print(f"Excel:     {EXCEL_FILE}")
    print(f"Base URL:  {BASE_URL}")
    print(f"Headless:  {HEADLESS}")
    print(f"Run ID:    {Path(SCREENSHOT_DIR).name}")
    print(f"Shots ->   {SCREENSHOT_DIR}")
    print("")

    try:
        test_cases = load_test_cases()
    except Exception as e:
        print(f"[FATAL] Failed to load test cases: {e}")
        return []

    print(f"Tests found: {len(test_cases)}\n")

    results: list[TestExecutionResult] = []
    passed = failed = 0

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=HEADLESS)
        except Exception as e:
            print(f"[FATAL] Browser launch failed: {e}")
            return []

        for tc in test_cases:
            print(f"Running {tc.test_id} - {tc.test_name}")
            try:
                result = run_one_test(browser, tc)
            except Exception as e:
                print(f"  [ERROR] {tc.test_id} crashed at orchestrator level: {e}")
                result = TestExecutionResult(
                    test_id=tc.test_id,
                    test_name=tc.test_name,
                    category=tc.category,
                    expected_result=tc.expected_result,
                    status="FAIL",
                    step_results=[],
                    failure_reason=f"Orchestrator error: {e}",
                    ai_status="NOT RUN",
                )
            results.append(result)
            if result.status == "PASS":
                passed += 1
            else:
                failed += 1
            print("")

        browser.close()

    # ----- Summary ----------------------------------------------------------
    print("=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Total:    {len(results)}")
    print(f"Passed:   {passed}")
    print(f"Failed:   {failed}")
    print(f"Skipped:  0")
    print("")
    print(f"Screenshots: {SCREENSHOT_DIR}")
    print("AI Verification: NOT IMPLEMENTED YET (Part 3 Stage 2)")
    print("=" * 60)

    return results


if __name__ == "__main__":
    run_tests()