import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

BASE_URL = "http://localhost:5173"
DEFAULT_TIMEOUT = 10000
MAX_RETRIES = 1
SCREENSHOT_DIR = os.path.join(PROJECT_ROOT, "screenshots")
TEST_CASES_DIR = os.path.join(PROJECT_ROOT, "test_cases")
EXCEL_FILE = os.path.join(TEST_CASES_DIR, "sample_test_cases.xlsx")
