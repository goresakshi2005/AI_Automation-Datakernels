import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from config import (
    BASE_URL,
    EXCEL_FILE,
    HEADLESS,
    SCREENSHOT_DIR,
    AI_ENABLED,
    AI_VERIFY_EVERY_SCREENSHOT,
    AI_MAX_CALLS_PER_RUN,
)
from excel_reader import load_test_cases
from excel_writer import write_results
from step_parser import parse_step
from executor import execute_step, settle_after_step
from screenshot_manager import capture_screenshot
from models import StepResult, TestExecutionResult
from waits import wait_for_animations
from ai_verifier import (
    verify_step,
    get_step_visual_expectation,
    aggregate_final_status,
)


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
         content produced by the CURRENT action).
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
    return None


def _briefly_settle_for_failure(page) -> None:
    """Give the app a moment to render an error UI before the FAILED screenshot."""
    try:
        page.wait_for_timeout(200)
        wait_for_animations(page, timeout=1_000)
    except Exception:
        pass


def _should_verify_with_ai(cmd: str, next_parsed: dict | None, is_last_step: bool) -> bool:
    """
    Decide whether to send this step's screenshot to AI.

    When AI_VERIFY_EVERY_SCREENSHOT=True, every screenshot is verified
    (high quota cost — only feasible on a paid Gemini plan).

    When False (default, free-tier friendly), verify only the checkpoints
    that actually prove the test result:

      * SCREENSHOT steps       (explicit checkpoint in the test data)
      * The final step         (belt-and-braces, in case there's no SCREENSHOT)
      * ASSERT_VISIBLE *or* WAIT_FOR immediately before a SCREENSHOT step
                              (the exact frame where the error/confirmation
                               is being asserted)

    Everything else is skipped — this reduces per-test calls from ~11 to ~3.
    """
    if not AI_ENABLED:
        return False
    if AI_VERIFY_EVERY_SCREENSHOT:
        return True

    if cmd == "SCREENSHOT":
        return True
    if is_last_step:
        return True

    nxt = (next_parsed or {}).get("command")
    # The step right before the SCREENSHOT is the one that proves the result.
    if cmd in ("ASSERT_VISIBLE", "ASSERT_TEXT", "WAIT_FOR") and nxt == "SCREENSHOT":
        return True

    return False
    
# ---------------------------------------------------------------------------
# Single test-case runner
# ---------------------------------------------------------------------------
def run_one_test(browser, test_case, ai_call_budget=None) -> TestExecutionResult:
    context = browser.new_context()
    page = context.new_page()

    raw_lines = [ln for ln in test_case.raw_steps.splitlines() if ln.strip()]
    parsed_steps = []
    for line in raw_lines:
        p = parse_step(line)
        if p:
            parsed_steps.append((line.strip(), p))

    step_results: list[StepResult] = []
    deterministic_status = "PASS"
    failure_reason = None
    test_start = time.perf_counter()
    total = len(parsed_steps)

    # Tracks the "focus element" across steps so SCREENSHOT steps inherit
    # the previous step's framing (e.g. a validation error).
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
            last_focus = None
            scroll_target = None
        elif cmd == "SCREENSHOT":
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
            if sr.screenshot_path:
                print(f"         shot: {sr.screenshot_path}")

        except Exception as e:
            sr.status = "FAIL"
            sr.error_message = str(e)
            deterministic_status = "FAIL"
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

        # ---------------- AI Vision verification ---------------------------
        is_last_step = (idx == total)
        if sr.screenshot_path and _should_verify_with_ai(cmd, next_parsed, is_last_step):
            budget_ok = (
                ai_call_budget is None
                or ai_call_budget["remaining"] > 0
            )

            if not budget_ok:
                sr.ai_status = "NOT RUN"
                sr.ai_observation = "AI call budget for this run exhausted."
                print(f"         AI: NOT RUN - run budget exhausted")
            else:
                if ai_call_budget is not None:
                    ai_call_budget["remaining"] -= 1

                expectation = get_step_visual_expectation(
                    test_id=test_case.test_id,
                    test_name=test_case.test_name,
                    category=test_case.category,
                    command=cmd or "",
                    target=parsed.get("target"),
                    value=parsed.get("value"),
                    overall_expected_result=test_case.expected_result,
                )

                ai_result = verify_step(
                    screenshot_path=sr.screenshot_path,
                    test_id=test_case.test_id,
                    test_name=test_case.test_name,
                    category=test_case.category,
                    step_number=idx,
                    step_command=cmd or "",
                    step_target=parsed.get("target"),
                    step_value=parsed.get("value"),
                    expected_result=test_case.expected_result,
                    step_expectation=expectation,
                )

                sr.ai_status = ai_result.status
                sr.ai_confidence = ai_result.confidence
                sr.ai_observation = ai_result.observation

                conf_str = (
                    f"{int(ai_result.confidence * 100)}%"
                    if ai_result.confidence is not None
                    else "n/a"
                )
                print(f"         AI: {ai_result.status} ({conf_str}) "
                      f"- {ai_result.observation or ''}")

        elif sr.screenshot_path:
            sr.ai_status = "NOT RUN"

        sr.duration_ms = int((time.perf_counter() - step_start) * 1000)
        step_results.append(sr)

        # Stop executing further steps of THIS test on failure, but the
        # caller moves on to the next test.
        if sr.status == "FAIL":
            break

    test_duration_ms = int((time.perf_counter() - test_start) * 1000)

    # ---------------- Final aggregation (deterministic + AI) --------------
    final_status, ai_status, ai_summary = aggregate_final_status(
        deterministic_status=deterministic_status,
        step_results=step_results,
    )

    ai_pass = sum(1 for s in step_results if s.ai_status == "PASS")
    ai_fail = sum(1 for s in step_results if s.ai_status == "FAIL")
    ai_unc  = sum(1 for s in step_results if s.ai_status == "UNCERTAIN")
    ai_nr   = sum(1 for s in step_results if (s.ai_status or "NOT RUN") == "NOT RUN")

    print(
        f"  {final_status}  ({len(step_results)} steps, {test_duration_ms/1000:.1f}s) "
        f"| AI: {ai_status} [PASS:{ai_pass} FAIL:{ai_fail} UNCERTAIN:{ai_unc} NOT RUN:{ai_nr}]"
    )

    context.close()

    return TestExecutionResult(
        test_id=test_case.test_id,
        test_name=test_case.test_name,
        category=test_case.category,
        expected_result=test_case.expected_result,
        status=final_status,
        step_results=step_results,
        failure_reason=failure_reason,
        duration_ms=test_duration_ms,
        ai_status=ai_status,
        ai_observation=ai_summary,
        ai_pass_count=ai_pass,
        ai_fail_count=ai_fail,
        ai_uncertain_count=ai_unc,
        ai_not_run_count=ai_nr,
        deterministic_status=deterministic_status,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def run_tests() -> list[TestExecutionResult]:
    print("=" * 60)
    print("AI HOTEL TEST AUTOMATION - PART 4 (AI VISION)")
    print("=" * 60)
    print(f"Excel:      {EXCEL_FILE}")
    print(f"Base URL:   {BASE_URL}")
    print(f"Headless:   {HEADLESS}")
    print(f"Run ID:     {Path(SCREENSHOT_DIR).name}")
    print(f"Shots ->    {SCREENSHOT_DIR}")
    print(f"AI Enabled: {AI_ENABLED}")
    print(f"AI Verify Every Screenshot: {AI_VERIFY_EVERY_SCREENSHOT}")
    if AI_MAX_CALLS_PER_RUN > 0:
        print(f"AI Call Budget This Run:    {AI_MAX_CALLS_PER_RUN}")
    else:
        print(f"AI Call Budget This Run:    unlimited")
    print("")

    try:
        test_cases = load_test_cases()
    except Exception as e:
        print(f"[FATAL] Failed to load test cases: {e}")
        return []

    print(f"Tests found: {len(test_cases)}\n")

    # Shared AI call budget across the whole run.
    ai_call_budget = {
        "remaining": AI_MAX_CALLS_PER_RUN if AI_MAX_CALLS_PER_RUN > 0 else 10**9
    }

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
                result = run_one_test(browser, tc, ai_call_budget)
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
                    ai_observation="Orchestrator error before AI verification.",
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
    print(f"AI Verification: {'ENABLED' if AI_ENABLED else 'DISABLED'}")
    if AI_MAX_CALLS_PER_RUN > 0:
        used = AI_MAX_CALLS_PER_RUN - ai_call_budget["remaining"]
        print(f"AI Calls Used:   {used} / {AI_MAX_CALLS_PER_RUN}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    run_tests()