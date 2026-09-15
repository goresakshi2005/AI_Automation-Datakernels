from pathlib import Path
from datetime import datetime
import os

# ---------------------------------------------------------------------------
# Load .env automatically (before reading any env vars below)
# ---------------------------------------------------------------------------
# python-dotenv reads KEY=value pairs from a .env file and exposes them via
# os.getenv() for the lifetime of this Python process. This runs BEFORE any
# os.getenv() call below, so the API key is available even when the shell
# doesn't have GOOGLE_API_KEY set.
#
# Precedence: real shell env vars WIN over .env (load_dotenv does not
# override existing vars by default). If you want .env to always win,
# pass override=True to load_dotenv().
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

try:
    from dotenv import load_dotenv  # type: ignore

    # Preferred location: automation/.env (next to this file)
    _env_file = BASE_DIR / ".env"
    if _env_file.exists():
        load_dotenv(_env_file)
    else:
        # Fallback: project-root .env (one level up)
        _env_file_root = PROJECT_ROOT / ".env"
        if _env_file_root.exists():
            load_dotenv(_env_file_root)
except ImportError:
    # python-dotenv not installed — fall back to shell env vars only.
    # Install with: python -m pip install python-dotenv
    pass


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
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
REPORT_FILE = TEST_CASES_DIR / "test_report.docx"
WRITE_BACK_TO_SOURCE = True

# ---------------------------------------------------------------------------
# PART 4 — AI Vision Verification (Gemini)
# ---------------------------------------------------------------------------
AI_ENABLED = True

# Primary model — gemini-2.5-flash was deprecated; using recommended replacement.
AI_MODEL = os.getenv("AI_MODEL", "gemini-3.6-flash")

# EMPTY fallback list: when the primary model hits quota (429), stop
# immediately instead of cascading through other models. Preview models
# have smaller quotas and would each burn another call, potentially
# triggering Google's anti-abuse throttling at the account / IP level.
AI_MODEL_FALLBACKS = []

AI_CONFIDENCE_THRESHOLD = 0.80
AI_MAX_RETRIES = 1
AI_REQUEST_TIMEOUT_MS = 30_000

# ---------------------------------------------------------------------------
# Cost / quota controls  (Part 4 — free-tier friendly)
# ---------------------------------------------------------------------------
# Selects how many screenshots get sent to Gemini.
#
#   "final_only"  →  1 call per test  (~15 per run)   ← safest for free tier
#   "minimal"     →  2 calls per test (~30 per run)   ← balanced
#   "standard"    →  3 calls per test (~45 per run)   ← original behavior
#   "every"       →  all screenshots  (~200+ per run) ← paid tier only
#
AI_VERIFY_STRATEGY = "final_only"

# Legacy flag — kept for backwards compatibility. When True, overrides
# AI_VERIFY_STRATEGY and behaves like "every".
AI_VERIFY_EVERY_SCREENSHOT = False

# Hard cap on AI calls per run (0 = unlimited). Protects against runaway
# retries; the run continues normally once this is hit.
AI_MAX_CALLS_PER_RUN = 40

# If the remaining budget drops to or below this number, skip AI entirely
# for the rest of the run (deterministic results are still produced).
AI_RESERVE_LAST_CALLS = 3

# Minimum seconds between consecutive AI calls (RPM guard).
# 8s ≈ 7.5 RPM — conservative for free tier to avoid 503 errors.
AI_MIN_SECONDS_BETWEEN_CALLS = 8.0

# Reads GEMINI_API_KEY first, falls back to GOOGLE_API_KEY.
# Both come from either the shell env or automation/.env (loaded above).
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")