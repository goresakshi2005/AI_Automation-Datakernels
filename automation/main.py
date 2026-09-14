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
from excel_writer import write_results
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


def _compute_scroll_target(parsed: dict, next_parsed: dict | None) -> str | None:
    """
    Decide which element to focus *before* the screenshot for this step.

    Priority:
      1. What the NEXT step is waiting for (that's the freshly rendered
         content produced by the CURRENT action). This is what makes
         validation-error screenshots land on the right element.
      2. Otherwise, this step's own target.
      3. Otherwise, None (SCREENSHOT and OPEN are handled by the caller).
    """
    cmd = parsed.get("command")
    if cmd == "OPEN":
        return None

    if next_parsed and next_parsed.get("command") == "WAIT_FOR":
        return next_parsed.get("target")

    if cmd in ("FILL", "CLICK", "WAIT_FOR", "ASSERT_VISIBLE",
               "ASSERT_TEXT", "SELECT", "CLEAR"):
        return parsed.get("target")

    return None  # SCREENSHOT handled separately by the caller


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

    # Tracks the "focus element" carried across steps so SCREENSHOT steps
    # inherit the previous step's framing (e.g. a validation error).
    last_focus: str | None = None

    for idx, (raw_step, parsed) in enumerate(parsed_steps, start=1):
        next_parsed = parsed_steps[idx][1] if idx < total else None
        cmd = parsed.get("command")

        sr = StepResult(
            step_number=idx,
            command=cmd or "?",
            raw_step=raw_step,
            target=parsed.get("target"),
            value=parsed.get("value"),
        )

        # --- Decide what the viewport should focus on for THIS step -------
        if cmd == "OPEN":
            # New page load -> reset focus, show top of page.
            last_focus = None
            scroll_target = None
        elif cmd == "SCREENSHOT":
            # Reuse the previous step's focus so we don't drift away from
            # the element the test just validated.
            scroll_target = last_focus
        else:
            scroll_target = _compute_scroll_target(parsed, next_parsed)
            if scroll_target:
                last_focus = scroll_target

        step_start = time.perf_counter()
        try:
            # 1. Execute the action
            execute_step(page, parsed)

            # 2. Wait for the app to reach a relevant, stable state (Bug #1 fix)
            settle_after_step(page, parsed, next_parsed)

            # 3. Screenshot after EVERY step. Centre-scroll the focus element
            #    so small validation errors are always fully visible.
            label = ""
            if cmd == "SCREENSHOT" and parsed.get("target"):
                label = parsed["target"]

            sr.screenshot_path = capture_screenshot(
                page, test_case.test_id, idx, label, scroll_target=scroll_target
            )

            sr.status = "PASS"
            print(f"  [OK]  Step {idx}/{total}  {_human_step_label(parsed, raw_step)}")

        except Exception as e:
            sr.status = "FAIL"
            sr.error_message = str(e)
            test_status = "FAIL"
            failure_reason = f"Step {idx} ({cmd}): {e}"

            # Failure screenshot - still try to centre on the failure target.
            _briefly_settle_for_failure(page)
            try:
                sr.screenshot_path = capture_screenshot(
                    page, test_case.test_id, idx, "FAILED",
                    scroll_target=parsed.get("target") or last_focus,
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
    print("AI HOTEL TEST AUTOMATION - PART 3 (Stage 1.2)")
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

    # ----- Excel write-back ------------------------------------------------
    print("-" * 60)
    write_results(results)

    # ----- Summary ---------------------------------------------------------
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