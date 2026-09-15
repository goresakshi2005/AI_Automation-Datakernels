"""
Excel result persistence with concurrency-safe, per-test writes.

Bug #3 — Excel Update Concurrency
---------------------------------
Test workers MUST NOT write Excel directly. If N workers each did
    load_workbook() -> modify -> save()
simultaneously, openpyxl's read-modify-save cycle would race: one worker's
save would clobber another's, producing lost updates and occasionally
corrupted files. Windows also locks the file during a write, causing
spurious PermissionErrors.

Our fix:
    Test workers -> thread-safe Queue -> SINGLE writer thread -> Excel
Only the writer thread ever touches openpyxl. A module-level Lock is
added as defence-in-depth so that even if another thread (or future code)
calls the synchronous API concurrently, workbook access still serialises.

Public API
----------
    ExcelResultWriter      — queue-backed async writer (preferred)
    write_result(result)   — synchronous single-result write
    write_results(results) — synchronous batch write (backwards compatible)

Two files are maintained:
    test_results.xlsx      — always written (seeded from source on start)
    sample_test_cases.xlsx — updated in place if WRITE_BACK_TO_SOURCE

The Microsoft Office lock file "~$test_results.xlsx" is never read,
written, or renamed — only the two real workbooks above are touched.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from queue import Queue
from threading import Lock, Thread
from typing import Optional

from openpyxl import load_workbook

from config import EXCEL_FILE, RESULTS_FILE, WRITE_BACK_TO_SOURCE


# ===========================================================================
# Module-level lock — defence-in-depth around openpyxl read/update/save.
# The primary serialisation is the single writer thread; this lock protects
# against accidental future direct calls from other threads.
# ===========================================================================
_workbook_lock = Lock()


def _format_ai_observation(result) -> str:
    """
    Build a concise AI Observation string for Excel.

    Preference order (first match wins):
      1. The actual AI observation text from a FAIL step   — most actionable
      2. The actual AI observation text from an UNCERTAIN step — explains why
      3. The actual AI observation text from a PASS step   — concrete evidence
      4. The generic aggregate summary                     — last resort

    Never dumps prompts, screenshots, base64, or model responses.
    """
    ai_status = (getattr(result, "ai_status", None) or "NOT RUN").upper()
    counts = (
        f"PASS:{getattr(result, 'ai_pass_count', 0)} "
        f"FAIL:{getattr(result, 'ai_fail_count', 0)} "
        f"UNCERTAIN:{getattr(result, 'ai_uncertain_count', 0)}"
    )

    # 1. Concrete per-step observation, in priority order (FAIL > UNCERTAIN > PASS)
    concrete = None
    for preferred in ("FAIL", "UNCERTAIN", "PASS"):
        for sr in getattr(result, "step_results", None) or []:
            if getattr(sr, "ai_status", None) == preferred and getattr(sr, "ai_observation", None):
                concrete = sr.ai_observation
                break
        if concrete:
            break

    # 2. Fall back to the aggregate summary only if no concrete obs exists
    summary = concrete or getattr(result, "ai_observation", None) or "No AI summary available."

    # 3. Surface the raw generic summary as a fallback marker if the
    #    aggregate observation itself says something useful (e.g. "quota exhausted")
    if not concrete and getattr(result, "ai_observation", None):
        summary = result.ai_observation

    return f"[{ai_status}] ({counts}) {summary}"[:500]


def _locate_columns(headers):
    """Return 1-based column indices for Test ID / Status / AI Observation."""
    required = ["Test ID", "Status", "AI Observation"]
    missing = [h for h in required if h not in headers]
    if missing:
        raise ValueError(
            f"Workbook is missing required column(s) {missing}. "
            f"Found: {headers}"
        )
    return (
        headers.index("Test ID") + 1,
        headers.index("Status") + 1,
        headers.index("AI Observation") + 1,
    )


def _apply_result_to_sheet(ws, result) -> bool:
    """
    Locate the row whose Test ID matches result.test_id (never by row number)
    and write Status + AI Observation. Returns True on success.
    """
    headers = [c.value for c in ws[1]]
    col_id, col_status, col_ai = _locate_columns(headers)

    target_id = str(result.test_id).strip()
    for row in range(2, ws.max_row + 1):
        raw_id = ws.cell(row=row, column=col_id).value
        if raw_id is None:
            continue
        if str(raw_id).strip() == target_id:
            ws.cell(row=row, column=col_status).value = result.status
            ws.cell(row=row, column=col_ai).value = _format_ai_observation(result)
            return True
    return False


# ===========================================================================
# Low-level file operations (always called under _workbook_lock)
# ===========================================================================
def _seed_results_from_source() -> tuple[bool, str]:
    """Copy the source workbook onto the results path (fresh slate)."""
    source = Path(EXCEL_FILE)
    results = Path(RESULTS_FILE)
    if not source.exists():
        return False, f"Source workbook not found: {source}"
    try:
        results.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, results)
        return True, "OK"
    except PermissionError:
        return False, (
            f"Permission denied seeding {results.name}. "
            f"Close it in Excel and re-run."
        )
    except Exception as e:
        return False, f"Could not seed results file: {e}"


def _apply_one_to_path(path: Path, result) -> tuple[bool, str]:
    """
    Load `path`, update the row matching result.test_id, save back.
    Always re-loads from disk so no stale in-memory state can overwrite
    previously-persisted results.
    """
    if not path.exists():
        return False, f"Workbook not found: {path}"

    try:
        wb = load_workbook(path)
    except Exception as e:
        return False, f"Could not open {path.name}: {e}"

    ws = wb.active
    try:
        matched = _apply_result_to_sheet(ws, result)
    except Exception as e:
        return False, f"Failed to update sheet in {path.name}: {e}"

    if not matched:
        return False, f"Test ID {result.test_id} not found in {path.name}"

    try:
        wb.save(path)
        return True, "OK"
    except PermissionError:
        return False, (
            f"Permission denied writing {path.name}. "
            f"Close the file in Excel and re-run."
        )
    except Exception as e:
        return False, f"Failed to save {path.name}: {e}"


# ===========================================================================
# Synchronous single-result write (the unit the worker thread invokes)
# ===========================================================================
def write_result(result) -> tuple[bool, str]:
    """
    Persist a single TestExecutionResult.

    Order:
      1. If results file doesn't exist yet, seed it from source.
      2. Update test_results.xlsx.
      3. If WRITE_BACK_TO_SOURCE, best-effort update sample_test_cases.xlsx.

    Returns (success, message). `success` reflects the results file, which
    is the primary deliverable.
    """
    results_path = Path(RESULTS_FILE)
    source_path = Path(EXCEL_FILE)

    with _workbook_lock:
        # 1. Seed if missing (first ever write)
        if not results_path.exists():
            ok, msg = _seed_results_from_source()
            if not ok:
                return False, msg

        # 2. Update results file
        results_ok, results_msg = _apply_one_to_path(results_path, result)

        # 3. Best-effort source write-back
        source_ok, source_msg = True, "OK"
        if WRITE_BACK_TO_SOURCE and source_path.resolve() != results_path.resolve():
            source_ok, source_msg = _apply_one_to_path(source_path, result)

        if not results_ok:
            # Results file is the primary output — its failure is the error.
            if not source_ok:
                return False, f"{results_msg} | source: {source_msg}"
            return False, results_msg

        return True, "OK"


# ===========================================================================
# Async queue-backed writer (Part 5 primary API)
# ===========================================================================
class ExcelResultWriter:
    """
    Single-threaded, queue-backed Excel writer.

    Test workers submit() results; only the writer thread calls openpyxl.
    This is the primary mitigation for Bug #3 — no two writes ever overlap.

    Usage:
        writer = ExcelResultWriter()
        writer.start()
        try:
            for tc in test_cases:
                result = run_one_test(...)
                writer.submit(result)
        finally:
            writer.close()   # blocks until queue is drained
    """

    _SENTINEL = object()

    def __init__(self) -> None:
        self.queue: Queue = Queue()
        self.thread: Optional[Thread] = None
        self._running = False

        # Statistics for the final summary
        self.submitted_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.failed_test_ids: list[str] = []
        self.last_error: Optional[str] = None

    # -- lifecycle ----------------------------------------------------------
    def start(self) -> None:
        """Reset the results file (fresh copy of source) and start the worker."""
        if self._running:
            return

        # Reset results file so this run starts clean.
        with _workbook_lock:
            seeded, msg = _seed_results_from_source()
        if seeded:
            print(f"[Excel] Seeded results file from source: {Path(RESULTS_FILE).name}")
        else:
            # Not fatal — the worker will keep trying per-result.
            print(f"[Excel] WARNING: could not seed results file: {msg}")

        self._running = True
        self.thread = Thread(
            target=self._worker,
            name="ExcelResultWriter",
            daemon=True,
        )
        self.thread.start()

    def submit(self, result) -> None:
        """Enqueue a result. Never blocks; worker persists asynchronously."""
        if not self._running:
            self.start()
        self.submitted_count += 1
        status = getattr(result, "status", "UNKNOWN")
        print(f"[Excel] Queued result: {result.test_id} -> {status}")
        self.queue.put(result)

    def close(self, timeout: float = 60.0) -> None:
        """Drain the queue, stop the worker, join the thread."""
        if not self._running:
            return

        # Push the sentinel so the worker knows to exit after draining.
        self.queue.put(self._SENTINEL)
        # wait until every item (including the sentinel) has been processed
        self.queue.join()

        if self.thread is not None:
            self.thread.join(timeout=timeout)

        self._running = False

    # -- worker -------------------------------------------------------------
    def _worker(self) -> None:
        while True:
            try:
                item = self.queue.get()
            except Exception:
                # Extremely unlikely — break the loop rather than spin.
                break

            try:
                if item is self._SENTINEL:
                    return

                try:
                    ok, msg = write_result(item)
                except Exception as e:
                    ok, msg = False, f"Unexpected writer error: {e}"

                if ok:
                    self.success_count += 1
                    print(f"[Excel] Updated {item.test_id} -> {item.status}")
                else:
                    self.failure_count += 1
                    self.failed_test_ids.append(getattr(item, "test_id", "?"))
                    self.last_error = msg
                    print(f"[Excel] Failed to update {item.test_id}: {msg}")

            finally:
                # task_done() must run even if the write raised, otherwise
                # queue.join() in close() would hang.
                self.queue.task_done()

    # -- convenience --------------------------------------------------------
    def has_failures(self) -> bool:
        return self.failure_count > 0


# ===========================================================================
# Backwards-compatible synchronous APIs
# ===========================================================================
def write_one(result) -> bool:
    """Synchronous single-result write; prints status. Returns True on success."""
    ok, msg = write_result(result)
    if ok:
        print(f"[excel_writer] Updated {result.test_id} -> {result.status}")
    else:
        print(f"[excel_writer] Failed to write {result.test_id}: {msg}")
    return ok


def write_results(results) -> None:
    """
    Batch synchronous write — preserved for backwards compatibility and
    ad-hoc/test usage. For the main automation pipeline, prefer
    ExcelResultWriter (progressive per-test persistence).
    """
    if not results:
        print("[excel_writer] No results to write.")
        return

    # Reset results file so the batch behaves like a fresh run.
    with _workbook_lock:
        ok, msg = _seed_results_from_source()
    if not ok:
        print(f"[excel_writer] WARNING: could not seed results file: {msg}")

    successes = 0
    failures = 0
    for r in results:
        ok, msg = write_result(r)
        if ok:
            successes += 1
        else:
            failures += 1
            print(f"[excel_writer] Failed to write {r.test_id}: {msg}")

    print(f"[excel_writer] Batch write complete: {successes} ok, {failures} failed.")