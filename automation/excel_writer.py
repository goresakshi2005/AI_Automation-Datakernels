"""
Writes test execution results back into the Excel workbook.

Two things happen:
  1. `test_results.xlsx` is always created as a copy of the source with
     Status + AI Observation populated.
  2. The original `sample_test_cases.xlsx` is updated *in place* unless
     it's locked (open in Excel) - in which case we warn and continue.
"""
from pathlib import Path

from openpyxl import load_workbook

from config import EXCEL_FILE, RESULTS_FILE, WRITE_BACK_TO_SOURCE


def _load_source():
    src = Path(EXCEL_FILE)
    if not src.exists():
        raise FileNotFoundError(f"Source workbook not found: {src}")
    return load_workbook(src)


def _format_ai_observation(result) -> str:
    """Build a concise AI Observation string for Excel."""
    ai_status = (result.ai_status or "NOT RUN").upper()
    counts = (
        f"PASS:{result.ai_pass_count} "
        f"FAIL:{result.ai_fail_count} "
        f"UNCERTAIN:{result.ai_uncertain_count}"
    )

    # Try to surface the most informative per-step observation.
    best_obs = None
    for sr in result.step_results:
        if sr.ai_status == "FAIL" and sr.ai_observation:
            best_obs = sr.ai_observation
            break
    if best_obs is None:
        for sr in result.step_results:
            if sr.ai_status == "UNCERTAIN" and sr.ai_observation:
                best_obs = sr.ai_observation
                break
    if best_obs is None:
        for sr in result.step_results:
            if sr.ai_status == "PASS" and sr.ai_observation:
                best_obs = sr.ai_observation
                break

    if result.ai_observation:
        summary = result.ai_observation
    else:
        summary = "No AI summary available."

    return f"[{ai_status}] ({counts}) {summary}"[:500]


def _update_sheet(ws, results) -> int:
    headers = [c.value for c in ws[1]]
    required = ["Test ID", "Status", "AI Observation"]
    missing = [h for h in required if h not in headers]
    if missing:
        raise ValueError(
            f"Workbook is missing required column(s) {missing}. "
            f"Found: {headers}"
        )

    col_id = headers.index("Test ID") + 1
    col_status = headers.index("Status") + 1
    col_ai = headers.index("AI Observation") + 1

    result_map = {r.test_id: r for r in results}
    updated = 0

    for row in range(2, ws.max_row + 1):
        raw_id = ws.cell(row=row, column=col_id).value
        if raw_id is None:
            continue
        tid = str(raw_id).strip()
        if not tid:
            continue
        res = result_map.get(tid)
        if res is None:
            continue

        ws.cell(row=row, column=col_status).value = res.status
        ws.cell(row=row, column=col_ai).value = _format_ai_observation(res)
        updated += 1

    return updated


def write_results(results) -> None:
    """Populate Status + AI Observation from `results` and save."""
    if not results:
        print("[excel_writer] No results to write.")
        return

    try:
        wb = _load_source()
    except Exception as e:
        print(f"[excel_writer] Cannot open source workbook: {e}")
        return

    ws = wb.active
    try:
        updated = _update_sheet(ws, results)
    except Exception as e:
        print(f"[excel_writer] Failed to update sheet: {e}")
        return

    if updated == 0:
        print("[excel_writer] No matching Test IDs found; nothing written.")
        return

    # ---- 1. Always write the results copy ---------------------------------
    try:
        results_path = Path(RESULTS_FILE)
        results_path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(results_path)
        print(f"[excel_writer] Wrote results copy:  {results_path}")
    except PermissionError:
        print(
            f"[excel_writer] Permission denied writing {RESULTS_FILE}. "
            f"Close the file in Excel and re-run."
        )
    except Exception as e:
        print(f"[excel_writer] Failed to write {RESULTS_FILE}: {e}")

    # ---- 2. Best-effort update of the source file -------------------------
    if WRITE_BACK_TO_SOURCE and Path(EXCEL_FILE).resolve() != Path(RESULTS_FILE).resolve():
        try:
            wb.save(EXCEL_FILE)
            print(f"[excel_writer] Updated source file: {EXCEL_FILE}")
        except PermissionError:
            print(
                f"[excel_writer] Could not update {EXCEL_FILE} "
                f"(likely open in Excel). Results copy is still valid."
            )
        except Exception as e:
            print(f"[excel_writer] Could not update {EXCEL_FILE}: {e}")

    print(f"[excel_writer] Updated {updated} row(s).")