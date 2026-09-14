from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

BASE_URL = "http://localhost:5173"

# ---------------------------------------------------------------------------
# Browser / timeouts
# ---------------------------------------------------------------------------
HEADLESS = False                       # set True for CI
DEFAULT_TIMEOUT = 10_000               # ms - for elements we *know* must appear
SHORT_TIMEOUT = 3_000                  # ms - for opportunistic / best-effort waits
MAX_RETRIES = 1

# ---------------------------------------------------------------------------
# Wait tuning (Bug #1)
# ---------------------------------------------------------------------------
POST_ACTION_SETTLE_MS = 120            # tiny React re-render buffer after FILL
NETWORK_IDLE_TIMEOUT_MS = 3_000        # bounded wait for background network
ANIMATION_SETTLE_TIMEOUT_MS = 2_000    # bounded wait for CSS animations to end
REACT_CYCLE_TIMEOUT_MS = 800           # bounded wait for React render cycle

# ---------------------------------------------------------------------------
# Screenshot behaviour (Bug #1 - the *real* fix)
# ---------------------------------------------------------------------------
# Scroll the focus element into the viewport before every screenshot.
# Without this, errors at the top of a long form are off-screen after
# Playwright auto-scrolls to the submit button at the bottom.
SCROLL_BEFORE_SCREENSHOT = True
SCROLL_TIMEOUT_MS = 2_000
SCROLL_SETTLE_MS = 80                  # tiny buffer for the scroll to register

# ---------------------------------------------------------------------------
# Per-run screenshot root - prevents overwriting previous runs
# ---------------------------------------------------------------------------
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
SCREENSHOT_DIR = PROJECT_ROOT / "screenshots" / f"run_{RUN_ID}"

# ---------------------------------------------------------------------------
# Excel test cases
# ---------------------------------------------------------------------------
TEST_CASES_DIR = PROJECT_ROOT / "test_cases"
EXCEL_FILE = TEST_CASES_DIR / "sample_test_cases.xlsx"
RESULTS_FILE = TEST_CASES_DIR / "test_results.xlsx"   # copy written after run
WRITE_BACK_TO_SOURCE = True                           # also update original