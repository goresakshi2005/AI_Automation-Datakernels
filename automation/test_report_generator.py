"""
Unit tests for the Part 6 Word report generator.

Uses fake TestExecutionResult objects. Does NOT require Playwright,
Gemini, or the running website.

Run:
    python test_report_generator.py
"""
import sys
import tempfile
from pathlib import Path

from docx import Document

from models import StepResult, TestExecutionResult
from report_generator import generate_word_report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _fake_result(
    test_id: str,
    status: str = "PASS",
    ai_status: str = "PASS",
    ai_confidence: float = 0.97,
    with_ai: bool = True,
    with_screenshot: bool = False,
    screenshot_path: str | None = None,
    category: str = "Happy Path",
    expected: str = "Expected workflow completes",
) -> TestExecutionResult:
    steps = [
        StepResult(
            step_number=1, command="OPEN", raw_step="OPEN: /",
            status="PASS", ai_status="NOT RUN",
        ),
        StepResult(
            step_number=2, command="CLICK", raw_step="CLICK: search-button",
            status="PASS",
            ai_status=ai_status if with_ai else None,
            ai_confidence=ai_confidence if with_ai else None,
            ai_observation="Concrete observation." if with_ai else None,
            screenshot_path=screenshot_path,
        ),
    ]
    if status == "FAIL":
        steps[1].status = "FAIL"
        steps[1].error_message = "Simulated failure"

    return TestExecutionResult(
        test_id=test_id,
        test_name=f"Fake test {test_id}",
        category=category,
        expected_result=expected,
        status=status,
        step_results=steps,
        failure_reason="Simulated failure" if status == "FAIL" else None,
        ai_status=ai_status if with_ai else "NOT RUN",
        ai_observation="Aggregate summary." if with_ai else None,
        ai_pass_count=1 if ai_status == "PASS" else 0,
        ai_fail_count=1 if ai_status == "FAIL" else 0,
        ai_uncertain_count=1 if ai_status == "UNCERTAIN" else 0,
        deterministic_status=status,
    )


def _check(condition: bool, message: str) -> bool:
    print(f"  [{'OK' if condition else 'FAIL'}] {message}")
    return condition


def _run(name: str, fn) -> bool:
    print(f"\n>>> {name}")
    try:
        return fn()
    except Exception as e:
        print(f"  [FAIL] Test raised: {type(e).__name__}: {e}")
        return False


# ---------------------------------------------------------------------------
# Individual tests
# ---------------------------------------------------------------------------
def test_single_pass(tmpdir: Path) -> bool:
    out = tmpdir / "single_pass.docx"
    results = [_fake_result("TC-001", status="PASS")]
    generate_word_report(results, out)

    doc = Document(out)
    text = "\n".join(p.text for p in doc.paragraphs)
    table_text = "\n".join(
        cell.text for table in doc.tables for row in table.rows for cell in row.cells
    )
    blob = text + "\n" + table_text

    ok = True
    ok &= _check(out.exists(), "DOCX created")
    ok &= _check(out.stat().st_size > 0, "DOCX not empty")
    ok &= _check("TC-001" in blob, "contains TC-001")
    ok &= _check("Summary" in text, "contains Summary section")
    ok &= _check("Pass Rate" in blob, "contains Pass Rate")
    ok &= _check("PASS" in blob, "contains PASS status")
    return ok


def test_fail_result(tmpdir: Path) -> bool:
    out = tmpdir / "fail.docx"
    results = [_fake_result("TC-005", status="FAIL", ai_status="NOT RUN")]
    generate_word_report(results, out)

    doc = Document(out)
    blob = "\n".join(p.text for p in doc.paragraphs)
    blob += "\n" + "\n".join(
        cell.text for table in doc.tables for row in table.rows for cell in row.cells
    )

    ok = True
    ok &= _check("TC-005" in blob, "contains TC-005")
    ok &= _check("FAIL" in blob, "contains FAIL status")
    ok &= _check("Simulated failure" in blob, "contains failure reason")
    return ok


def test_multiple_tests(tmpdir: Path) -> bool:
    out = tmpdir / "multi.docx"
    results = [
        _fake_result("TC-001", status="PASS"),
        _fake_result("TC-002", status="PASS"),
        _fake_result("TC-003", status="FAIL", ai_status="NOT RUN"),
    ]
    generate_word_report(results, out)

    doc = Document(out)
    blob = "\n".join(p.text for p in doc.paragraphs)
    blob += "\n" + "\n".join(
        cell.text for table in doc.tables for row in table.rows for cell in row.cells
    )

    ok = True
    for tid in ("TC-001", "TC-002", "TC-003"):
        ok &= _check(tid in blob, f"contains {tid}")
    ok &= _check("3" in blob, "summary shows 3 total tests")
    ok &= _check("66.7%" in blob, "pass rate 66.7% computed")
    return ok


def test_with_ai_info(tmpdir: Path) -> bool:
    out = tmpdir / "ai.docx"
    results = [_fake_result("TC-001", ai_status="PASS", ai_confidence=0.98)]
    generate_word_report(results, out)

    doc = Document(out)
    blob = "\n".join(p.text for p in doc.paragraphs)
    blob += "\n" + "\n".join(
        cell.text for table in doc.tables for row in table.rows for cell in row.cells
    )

    ok = True
    ok &= _check("AI Verification" in blob, "AI Verification heading present")
    ok &= _check("98%" in blob, "confidence formatted as 98%")
    ok &= _check("Concrete observation." in blob, "concrete AI observation shown")
    return ok


def test_missing_screenshot(tmpdir: Path) -> bool:
    out = tmpdir / "missing_shot.docx"
    results = [_fake_result(
        "TC-001",
        with_screenshot=True,
        screenshot_path="E:/does/not/exist/nope.png",
    )]
    generate_word_report(results, out)  # must not raise

    doc = Document(out)
    blob = "\n".join(p.text for p in doc.paragraphs)
    ok = True
    ok &= _check(out.exists(), "DOCX created despite missing screenshot")
    ok &= _check("Screenshot unavailable" in blob, "reported missing screenshot")
    return ok


def test_existing_screenshot(tmpdir: Path) -> bool:
    out = tmpdir / "with_shot.docx"

    # Use a tiny valid PNG (1x1 transparent)
    png = tmpdir / "tiny.png"
    png.write_bytes(
        bytes.fromhex(
            "89504E470D0A1A0A0000000D4948445200000001000000010806000000"
            "1F15C4890000000D49444154789C6360000002000001E2210AA4000000"
            "0049454E44AE426082"
        )
    )

    results = [_fake_result(
        "TC-001",
        with_screenshot=True,
        screenshot_path=str(png),
    )]
    generate_word_report(results, out)

    doc = Document(out)
    # python-docx stores embedded images under inline_shapes
    ok = True
    ok &= _check(out.exists(), "DOCX created")
    ok &= _check(len(doc.inline_shapes) >= 1, "at least one image embedded")
    return ok


def test_empty_results(tmpdir: Path) -> bool:
    out = tmpdir / "empty.docx"
    generate_word_report([], out)  # must not raise (no div-by-zero)

    doc = Document(out)
    text = "\n".join(p.text for p in doc.paragraphs)
    blob = text + "\n" + "\n".join(
        cell.text for table in doc.tables for row in table.rows for cell in row.cells
    )

    ok = True
    ok &= _check(out.exists(), "DOCX created for empty results")
    ok &= _check("0.0%" in blob, "pass rate 0.0% for empty")
    ok &= _check("No test results were available" in text, "empty message shown")
    return ok


def test_docx_reopenable(tmpdir: Path) -> bool:
    out = tmpdir / "reopen.docx"
    generate_word_report([_fake_result("TC-001")], out)
    try:
        doc = Document(out)
        ok = _check(len(doc.paragraphs) > 0, "reopened with paragraphs")
    except Exception as e:
        ok = _check(False, f"reopen failed: {e}")
    return ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    print("=" * 60)
    print("REPORT GENERATOR UNIT TESTS")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as td:
        tmpdir = Path(td)

        tests = [
            ("Single PASS result",         lambda: test_single_pass(tmpdir)),
            ("FAIL result",                lambda: test_fail_result(tmpdir)),
            ("Multiple tests + pass rate", lambda: test_multiple_tests(tmpdir)),
            ("AI info display",            lambda: test_with_ai_info(tmpdir)),
            ("Missing screenshot handled", lambda: test_missing_screenshot(tmpdir)),
            ("Existing screenshot embedded", lambda: test_existing_screenshot(tmpdir)),
            ("Empty results",              lambda: test_empty_results(tmpdir)),
            ("DOCX reopenable",            lambda: test_docx_reopenable(tmpdir)),
        ]

        outcomes = []
        for name, fn in tests:
            outcomes.append(_run(name, fn))

    print()
    print("=" * 60)
    passed = sum(1 for o in outcomes if o)
    total = len(outcomes)
    print(f"RESULT: {passed}/{total} tests passed")
    print("=" * 60)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())