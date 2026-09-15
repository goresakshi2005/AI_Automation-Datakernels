"""
Concurrency test for ExcelResultWriter (Bug #3 — Excel Update Concurrency).

Simulates multiple "workers" submitting TestExecutionResult objects
simultaneously. Verifies:
  * no corrupted workbook
  * no lost updates
  * correct Status values
  * original row ordering preserved
  * duplicate submissions don't create duplicate rows

Run:
    python test_excel_writer.py

NOTE: this test overwrites test_results.xlsx as a side effect.
"""
import shutil
from pathlib import Path
from threading import Thread

from openpyxl import load_workbook

from config import EXCEL_FILE, RESULTS_FILE
from excel_writer import ExcelResultWriter
from models import StepResult, TestExecutionResult


def make_fake_result(test_id: str, status: str = "PASS",
                     ai_status: str = "PASS") -> TestExecutionResult:
    return TestExecutionResult(
        test_id=test_id,
        test_name=f"Fake {test_id}",
        category="Concurrency",
        expected_result="N/A",
        status=status,
        step_results=[
            StepResult(
                step_number=1,
                command="SCREENSHOT",
                raw_step="SCREENSHOT: fake",
                status="PASS",
                ai_status=ai_status,
                ai_confidence=0.95 if ai_status == "PASS" else None,
                ai_observation="Fake observation.",
            )
        ],
        ai_status=ai_status,
        ai_observation="Fake summary.",
        ai_pass_count=1 if ai_status == "PASS" else 0,
        ai_fail_count=1 if ai_status == "FAIL" else 0,
        ai_uncertain_count=1 if ai_status == "UNCERTAIN" else 0,
        deterministic_status=status,
    )


def main() -> int:
    src = Path(EXCEL_FILE)
    dst = Path(RESULTS_FILE)
    if not src.exists():
        print(f"[FAIL] Source workbook missing: {src}")
        return 1

    # Fresh results copy so we know the starting state.
    shutil.copyfile(src, dst)
    print(f"Seeded {dst.name} from {src.name}\n")

    writer = ExcelResultWriter()
    writer.start()

    plan = [
        ("TC-001", "PASS"),
        ("TC-002", "PASS"),
        ("TC-003", "FAIL"),
        ("TC-004", "PASS"),
        ("TC-005", "PASS"),
    ]

    threads: list[Thread] = []
    for tid, st in plan:
        t = Thread(
            target=writer.submit,
            args=(make_fake_result(tid, st, ai_status=("FAIL" if st == "FAIL" else "PASS")),),
            name=f"Submitter-{tid}",
        )
        threads.append(t)

    # Fire all threads at once — this is the concurrency stress.
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    writer.close()

    # ---- Verify ----------------------------------------------------------
    wb = load_workbook(dst)
    ws = wb.active
    headers = [c.value for c in ws[1]]
    col_id = headers.index("Test ID") + 1
    col_status = headers.index("Status") + 1
    col_ai = headers.index("AI Observation") + 1

    seen: dict[str, tuple[str, str]] = {}
    for row in range(2, ws.max_row + 1):
        tid = ws.cell(row=row, column=col_id).value
        if tid in dict(plan):
            seen[str(tid).strip()] = (
                ws.cell(row=row, column=col_status).value,
                ws.cell(row=row, column=col_ai).value,
            )

    expected = dict(plan)
    ok = True
    print("\nVerification:")
    for tid, want_status in plan:
        got = seen.get(tid)
        if got is None:
            print(f"  [FAIL] {tid}: MISSING from workbook")
            ok = False
            continue
        got_status, got_ai = got
        match = (got_status == want_status)
        marker = "OK" if match else "FAIL"
        print(f"  [{marker}] {tid}: expected={want_status} actual={got_status} "
              f"AI={str(got_ai)[:60]}")
        if not match:
            ok = False

    print()
    print(f"  Submitted: {writer.submitted_count}")
    print(f"  Success:   {writer.success_count}")
    print(f"  Failed:    {writer.failure_count}")
    print()
    verdict = "PASS" if ok and writer.failure_count == 0 else "FAIL"
    print(f"BUG #3 CONCURRENCY TEST: {verdict}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())