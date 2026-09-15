"""
Part 6 — Word report generation.

Consumes the list[TestExecutionResult] produced by main.py and writes a
professional test_report.docx with:

  * Title + metadata
  * Summary (dynamic — no hardcoded counts)
  * Test Results Overview table
  * Detailed section per test (ID, name, category, expected, actual,
    status, AI verdict, step table, screenshots)
  * Footer text

Design notes
------------
* Never invents data. Missing values become "N/A" or "Not available".
* Missing/unreadable screenshots degrade gracefully to a text line.
* Never crashes the test suite — main.py wraps the call in try/except.
* Uses the existing TestExecutionResult / StepResult models. No duplicate.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def _safe_str(value, default: str = "N/A") -> str:
    if value is None:
        return default
    s = str(value).strip()
    return s if s else default


def _status_plain(status: str) -> str:
    """Normalise a status string for display."""
    return _safe_str(status, "NOT RUN").upper()


def _add_kv(document: Document, key: str, value: str, bold_value: bool = False) -> None:
    p = document.add_paragraph()
    p.add_run(f"{key}: ").bold = True
    run = p.add_run(value)
    if bold_value:
        run.bold = True


def _add_page_break(document: Document) -> None:
    document.add_page_break()


def _format_confidence(conf: Optional[float]) -> str:
    if conf is None:
        return "N/A"
    try:
        return f"{int(round(float(conf) * 100))}%"
    except Exception:
        return "N/A"


def _resolve_screenshot_path(raw_path: Optional[str]) -> Optional[Path]:
    """Accept absolute or relative paths; return an existing Path or None."""
    if not raw_path:
        return None
    p = Path(raw_path)
    if not p.is_absolute():
        p = Path.cwd() / p
    return p if p.exists() and p.is_file() else None


# ---------------------------------------------------------------------------
# Actual result synthesis (derived from real execution data only)
# ---------------------------------------------------------------------------
def _compose_actual_result(result) -> str:
    status = _status_plain(getattr(result, "status", ""))
    det = _status_plain(getattr(result, "deterministic_status", "") or "")
    ai_status = _status_plain(getattr(result, "ai_status", "") or "")
    ai_obs = getattr(result, "ai_observation", None)
    failure = getattr(result, "failure_reason", None)

    if status == "PASS":
        if ai_status == "PASS":
            return (
                "The expected workflow completed successfully, all deterministic "
                "Playwright checks passed, and AI visual verification confirmed "
                "the expected state."
            )
        if ai_status == "UNCERTAIN":
            base = (
                "The expected workflow completed successfully and all "
                "deterministic Playwright checks passed. AI visual verification "
                "was UNCERTAIN"
            )
            if ai_obs:
                base += f": {ai_obs}"
            else:
                base += "."
            return base
        if ai_status in ("NOT RUN", "", "N/A"):
            return (
                "The expected workflow completed successfully and all "
                "deterministic Playwright checks passed. AI visual verification "
                "was not run for this test."
            )
        return "The expected workflow completed successfully."

    if status == "FAIL":
        if failure:
            return f"The test failed during execution. {failure}"
        if det == "FAIL":
            return "The test failed during execution: one or more deterministic Playwright checks did not pass."
        if ai_status == "FAIL" and ai_obs:
            return f"The test failed. AI visual verification reported: {ai_obs}"
        return "The test failed during execution."

    return "Test did not complete."


# ---------------------------------------------------------------------------
# Header / summary / overview
# ---------------------------------------------------------------------------
def _write_header(doc: Document) -> None:
    title = doc.add_heading("AI Automated Test Report", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = meta.add_run(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    run.italic = True
    run.font.size = Pt(10)

    for line in (
        "Application: Hotel Booking System",
        "Automation Framework: Playwright + Python",
        "AI Verification: Google Gemini",
    ):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(line)
        r.font.size = Pt(10)

    doc.add_paragraph()


def _write_summary(doc: Document, results: Iterable) -> None:
    results = list(results)
    total = len(results)
    passed = sum(1 for r in results if _status_plain(r.status) == "PASS")
    failed = sum(1 for r in results if _status_plain(r.status) == "FAIL")
    pass_rate = f"{(passed / total * 100):.1f}%" if total > 0 else "0.0%"

    ai_pass = sum(int(getattr(r, "ai_pass_count", 0) or 0) for r in results)
    ai_fail = sum(int(getattr(r, "ai_fail_count", 0) or 0) for r in results)
    ai_unc  = sum(int(getattr(r, "ai_uncertain_count", 0) or 0) for r in results)

    doc.add_heading("Summary", level=1)

    table = doc.add_table(rows=1, cols=2)
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    hdr[0].text = "Metric"
    hdr[1].text = "Result"

    rows = [
        ("Total Tests", str(total)),
        ("Passed", str(passed)),
        ("Failed", str(failed)),
        ("Pass Rate", pass_rate),
    ]
    if ai_pass or ai_fail or ai_unc:
        rows.extend([
            ("AI PASS Checkpoints", str(ai_pass)),
            ("AI FAIL Checkpoints", str(ai_fail)),
            ("AI UNCERTAIN Checkpoints", str(ai_unc)),
        ])

    for k, v in rows:
        cells = table.add_row().cells
        cells[0].text = k
        cells[1].text = v


def _write_overview(doc: Document, results: Iterable) -> None:
    results = list(results)
    doc.add_heading("Test Results Overview", level=1)

    table = doc.add_table(rows=1, cols=4)
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    for i, name in enumerate(("Test ID", "Test Name", "Category", "Status")):
        hdr[i].text = name

    for r in results:
        cells = table.add_row().cells
        cells[0].text = _safe_str(getattr(r, "test_id", None))
        cells[1].text = _safe_str(getattr(r, "test_name", None))
        cells[2].text = _safe_str(getattr(r, "category", None))
        cells[3].text = _status_plain(getattr(r, "status", ""))


# ---------------------------------------------------------------------------
# Step table + screenshots
# ---------------------------------------------------------------------------
def _write_step_table(doc: Document, result) -> None:
    step_results = list(getattr(result, "step_results", None) or [])
    if not step_results:
        doc.add_paragraph("No steps were executed for this test.")
        return

    table = doc.add_table(rows=1, cols=5)
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    for i, name in enumerate(("Step", "Action", "Status", "AI Status", "Confidence")):
        hdr[i].text = name

    for sr in step_results:
        cells = table.add_row().cells
        cells[0].text = str(getattr(sr, "step_number", ""))
        cells[1].text = _safe_str(getattr(sr, "raw_step", None), "")
        cells[2].text = _status_plain(getattr(sr, "status", ""))
        cells[3].text = _status_plain(getattr(sr, "ai_status", "") or "NOT RUN")
        cells[4].text = _format_confidence(getattr(sr, "ai_confidence", None))


def _write_ai_section(doc: Document, result) -> None:
    ai_status = getattr(result, "ai_status", None)
    ai_obs = getattr(result, "ai_observation", None)

    doc.add_heading("AI Verification", level=3)
    _add_kv(doc, "AI Status", _status_plain(ai_status) if ai_status else "NOT RUN")
    if ai_obs:
        _add_kv(doc, "AI Observation", str(ai_obs))

    # Per-step AI observations (if any)
    per_step = [
        sr for sr in (getattr(result, "step_results", None) or [])
        if getattr(sr, "ai_observation", None)
    ]
    if per_step:
        doc.add_paragraph("Per-step AI observations:").runs[0].italic = True
        for sr in per_step:
            p = doc.add_paragraph(style="List Bullet")
            p.add_run(
                f"Step {getattr(sr, 'step_number', '?')} — "
                f"{_safe_str(getattr(sr, 'raw_step', None), '')} "
            ).bold = True
            p.add_run(
                f"[{_status_plain(sr.ai_status or 'NOT RUN')}, "
                f"{_format_confidence(getattr(sr, 'ai_confidence', None))}] "
                f"{sr.ai_observation}"
            )


def _write_screenshots(doc: Document, result) -> None:
    doc.add_heading("Screenshots", level=3)

    step_results = list(getattr(result, "step_results", None) or [])
    if not step_results:
        doc.add_paragraph("No screenshots available.")
        return

    added_any = False
    for sr in step_results:
        raw = getattr(sr, "screenshot_path", None)
        step_num = getattr(sr, "step_number", "?")
        raw_step = _safe_str(getattr(sr, "raw_step", None), "")

        doc.add_paragraph(
            f"Step {step_num} — {raw_step}"
        ).runs[0].bold = True

        resolved = _resolve_screenshot_path(raw)

        if raw is None:
            doc.add_paragraph("No screenshot captured for this step.").runs[0].italic = True
            continue

        if resolved is None:
            p = doc.add_paragraph()
            p.add_run("Screenshot unavailable: ").italic = True
            p.add_run(str(raw))
            continue

        try:
            doc.add_picture(str(resolved), width=Inches(6.0))
            # Center the image
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            added_any = True
        except Exception as e:
            p = doc.add_paragraph()
            p.add_run(f"Could not embed screenshot ({type(e).__name__}): ").italic = True
            p.add_run(str(raw))

    if not added_any:
        doc.add_paragraph("(No screenshot files were found on disk.)").runs[0].italic = True


# ---------------------------------------------------------------------------
# Detailed per-test section
# ---------------------------------------------------------------------------
def _write_test_section(doc: Document, result) -> None:
    test_id = _safe_str(getattr(result, "test_id", None))
    test_name = _safe_str(getattr(result, "test_name", None))
    category = _safe_str(getattr(result, "category", None))
    expected = _safe_str(getattr(result, "expected_result", None), "Not available")
    status = _status_plain(getattr(result, "status", ""))

    doc.add_heading(f"{test_id} — {test_name}", level=2)

    _add_kv(doc, "Test ID", test_id)
    _add_kv(doc, "Test Name", test_name)
    _add_kv(doc, "Category", category)
    _add_kv(doc, "Status", status, bold_value=True)

    # Expected / Actual as their own headings for readability
    doc.add_heading("Expected Result", level=3)
    doc.add_paragraph(expected)

    doc.add_heading("Actual Result", level=3)
    doc.add_paragraph(_compose_actual_result(result))

    if status == "FAIL" and getattr(result, "failure_reason", None):
        doc.add_heading("Failure Details", level=3)
        p = doc.add_paragraph()
        p.add_run("Failure Reason: ").bold = True
        p.add_run(str(result.failure_reason))

    _write_ai_section(doc, result)

    doc.add_heading("Steps", level=3)
    _write_step_table(doc, result)

    _write_screenshots(doc, result)


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
def _write_footer(doc: Document) -> None:
    section = doc.sections[0]
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("AI-Powered Automated Testing System — Hotel Booking System")
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def generate_word_report(results, output_path) -> Path:
    """
    Generate the Word report.

    Returns the Path that was written. Raises on unexpected errors — the
    caller (main.py) is expected to catch them so report failures never
    break the test suite.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results = list(results or [])

    doc = Document()
    _write_footer(doc)

    _write_header(doc)
    _write_summary(doc, results)

    doc.add_paragraph()
    _write_overview(doc, results)

    doc.add_paragraph()
    doc.add_heading("Detailed Test Results", level=1)

    if not results:
        doc.add_paragraph("No test results were available.")
    else:
        for idx, r in enumerate(results):
            if idx > 0:
                _add_page_break(doc)
            _write_test_section(doc, r)

    doc.save(str(output_path))
    return output_path


if __name__ == "__main__":
    # Manual smoke test with fake data (no Playwright needed).
    from models import StepResult, TestExecutionResult

    fake = [
        TestExecutionResult(
            test_id="TC-001",
            test_name="Complete valid booking flow",
            category="Happy Path",
            expected_result="Booking confirmation displayed",
            status="PASS",
            step_results=[
                StepResult(
                    step_number=1, command="OPEN", raw_step="OPEN: /",
                    status="PASS", ai_status="NOT RUN",
                ),
                StepResult(
                    step_number=2, command="CLICK", raw_step="CLICK: confirm-booking-button",
                    status="PASS", ai_status="PASS", ai_confidence=0.97,
                    ai_observation="The booking confirmation is clearly visible.",
                ),
            ],
            ai_status="PASS",
            ai_observation="All 2 AI visual checkpoint(s) passed.",
            ai_pass_count=1, ai_fail_count=0, ai_uncertain_count=0, ai_not_run_count=1,
            deterministic_status="PASS",
        ),
        TestExecutionResult(
            test_id="TC-002",
            test_name="Search for available rooms",
            category="Happy Path",
            expected_result="Available rooms are displayed",
            status="FAIL",
            step_results=[
                StepResult(
                    step_number=1, command="OPEN", raw_step="OPEN: /",
                    status="PASS", ai_status="NOT RUN",
                ),
                StepResult(
                    step_number=2, command="WAIT_FOR", raw_step="WAIT_FOR: room-card-1",
                    status="FAIL", error_message="Timeout waiting for room-card-1",
                    ai_status="NOT RUN",
                ),
            ],
            failure_reason="Step 2 (WAIT_FOR): Timeout waiting for room-card-1",
            ai_status="NOT RUN",
            deterministic_status="FAIL",
        ),
    ]

    out = Path(__file__).resolve().parent.parent / "test_cases" / "test_report_smoke.docx"
    path = generate_word_report(fake, out)
    print(f"[report_generator] Smoke report: {path}")