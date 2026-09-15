from pathlib import Path
from datetime import datetime
import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

BASE_URL = "http://localhost:5173"

# ---------------------------------------------------------------------------
# Browser / timeouts
# ---------------------------------------------------------------------------
HEADLESS = False
DEFAULT_TIMEOUT = 10_000
SHORT_TIMEOUT = 3_000
MAX_RETRIES = 1

# ---------------------------------------------------------------------------
# Wait tuning (Bug #1)
# ---------------------------------------------------------------------------
POST_ACTION_SETTLE_MS = 120
NETWORK_IDLE_TIMEOUT_MS = 3_000
ANIMATION_SETTLE_TIMEOUT_MS = 2_000
REACT_CYCLE_TIMEOUT_MS = 800

# ---------------------------------------------------------------------------
# Screenshot behaviour (Bug #1)
# ---------------------------------------------------------------------------
SCROLL_BEFORE_SCREENSHOT = True
SCROLL_TIMEOUT_MS = 2_000
SCROLL_SETTLE_MS = 80

# ---------------------------------------------------------------------------
# Per-run screenshot root
# ---------------------------------------------------------------------------
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
SCREENSHOT_DIR = PROJECT_ROOT / "screenshots" / f"run_{RUN_ID}"

# ---------------------------------------------------------------------------
# Excel test cases
# ---------------------------------------------------------------------------
TEST_CASES_DIR = PROJECT_ROOT / "test_cases"
EXCEL_FILE = TEST_CASES_DIR / "sample_test_cases.xlsx"
RESULTS_FILE = TEST_CASES_DIR / "test_results.xlsx"
WRITE_BACK_TO_SOURCE = True

# ---------------------------------------------------------------------------
# PART 4 — AI Vision Verification (Gemini)
# ---------------------------------------------------------------------------
AI_ENABLED = True

# Primary model — confirmed working on this API key by test_gemini.py.
AI_MODEL = os.getenv("AI_MODEL", "gemini-2.5-flash")

# Fallbacks — only models currently live on the v1beta API.
# (gemini-1.5-*, gemini-2.0-flash, gemini-2.5-flash-lite, gemini-2.5-pro
#  are deprecated for new users and return 404.)
AI_MODEL_FALLBACKS = [
    "gemini-3-flash-preview",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
]

AI_CONFIDENCE_THRESHOLD = 0.80
AI_MAX_RETRIES = 1
AI_REQUEST_TIMEOUT_MS = 30_000

# ---------------------------------------------------------------------------
# Cost / quota controls
# ---------------------------------------------------------------------------
# True:  verify every screenshot (assignment-max setting, high quota cost).
# False: verify only meaningful checkpoints — recommended for free tier.
AI_VERIFY_EVERY_SCREENSHOT = False

# Hard cap on AI calls per run (0 = unlimited).
AI_MAX_CALLS_PER_RUN = 80   # unchanged — but now you'll use ~45

# Minimum seconds between consecutive AI calls (rate-limit guard).
# 4s ≈ 15 RPM ceiling.
AI_MIN_SECONDS_BETWEEN_CALLS = 4.0

# Reads GEMINI_API_KEY first, falls back to GOOGLE_API_KEY.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")