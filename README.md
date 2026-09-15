# AI-Powered Automated Testing System

A complete hiring-assignment submission: a **Hotel Booking website** + a **Python/Playwright automation framework** that reads test cases from **Excel**, drives a real browser, takes **a screenshot after every step**, sends each checkpoint to **Google Gemini (AI Vision)** for verification, writes results back into Excel with **thread-safe concurrency handling**, and generates a **Word report with embedded screenshots**.

---

## What's included

| Feature | Where |
|---|---|
| 🌐 **Hotel Booking website** (React + Vite) | `Hotel_Booking/` |
| 🤖 **Playwright automation tool** | `automation/` |
| 📊 **Excel-driven tests** (read + write-back) | `test_cases/sample_test_cases.xlsx` |
| 📸 **Screenshot after every step** | `screenshots/run_<timestamp>/` |
| 🧠 **AI Vision verification** (Google Gemini) | `automation/ai_verifier.py` |
| 🔒 **Concurrency-safe Excel writes** (queue + single writer) | `automation/excel_writer.py` |
| 📄 **Word report** with embedded screenshots | `test_cases/test_report.docx` |
| 🐳 **Docker Compose** (website + automation) | `docker-compose.yml` |

---

## Architecture in one picture

```
        sample_test_cases.xlsx
                 │
                 ▼
        ┌───────────────────┐
        │  main.py (runner) │
        └─────────┬─────────┘
                  │
      ┌───────────┼───────────────┐
      ▼           ▼               ▼
 Playwright   Screenshots    Gemini Vision
 (execute)    (every step)   (verify each)
      │           │               │
      └───────────┴───────────────┘
                  │
                  ▼
         TestExecutionResult
                  │
        ┌─────────┴──────────┐
        ▼                    ▼
 ExcelResultWriter    report_generator
 (thread-safe)        (python-docx)
        │                    │
        ▼                    ▼
 test_results.xlsx   test_report.docx
```

**Design principle:** Playwright decides pass/fail. AI Vision is an *additional* visual check that adds confidence + observations. AI can override with a high-confidence FAIL, but low-confidence noise is ignored.

---

## Quick start (Local)

**Terminal 1 — Website:**
```bash
cd Hotel_Booking
npm install
npm run dev          # → http://localhost:5173
```

**Terminal 2 — Automation:**
```bash
cd automation
python -m venv venv
venv\Scripts\activate               # Windows (source venv/bin/activate on mac/linux)

python -m pip install -r requirements.txt
playwright install chromium

# Set your Gemini key (optional — everything else works without it)
echo GOOGLE_API_KEY=AIzaSy... > .env

python main.py
```

**Outputs after the run:**
- `test_cases/test_results.xlsx` — Status + AI Observation per test
- `test_cases/test_report.docx` — full report with screenshots
- `screenshots/run_<timestamp>/TC-XXX/*.png` — one PNG per executed step

---

## Quick start (Docker)

```bash
# One-time: generate package-lock.json
cd Hotel_Booking && npm install && cd ..

# Build + run
docker compose build
docker compose up
```

Website runs on `5173`. Automation runs headless. Outputs land on your host via volume mounts.

---

## Features in detail

### 🌐 Hotel Booking website (`Hotel_Booking/`)

React + Vite + React Router. Pages: Home / Search Results / Room Details / Booking / Confirmation / My Bookings. Uses `localStorage`. Every interactive element has a stable `data-testid` for automation. Validation rules live in `src/utils/validation.js`.

### 🤖 Automation tool (`automation/`)

Reads test cases from Excel, executes each one in a fresh Playwright context (no localStorage leakage between tests), and produces structured results. The runner is `main.py`.

### 📊 Excel-driven tests

`sample_test_cases.xlsx` has 15 tests. Each **Steps** cell is a machine-readable script:

```
OPEN: /
FILL: email-input = invalid-email
CLICK: confirm-booking-button
WAIT_FOR: email-error
ASSERT_VISIBLE: email-error
SCREENSHOT: validation_error
```

Supported commands: `OPEN`, `FILL`, `CLICK`, `WAIT_FOR`, `ASSERT_VISIBLE`, `ASSERT_TEXT`, `SELECT`, `CLEAR`, `SCREENSHOT`.

### 📸 Screenshots after every step

`Bug #1` fixed. Every action triggers:
```
ACTION  →  wait for real app state  →  centre-scroll focus element  →  screenshot
```
- **Look-ahead wait** for the next step's `WAIT_FOR` target
- **Centre-scroll** so small validation errors are never clipped
- **No `time.sleep()`** as primary synchronization

Saved to `screenshots/run_<YYYYMMDD_HHMMSS>/TC-XXX/TC-XXX_step-NN.png`. Every run gets its own folder — no overwrites.

### 🧠 AI Vision (Gemini)

`ai_verifier.py` sends each screenshot to Gemini with:
- **Strict system prompt** — no hallucination, only judge what's visible
- **Structured JSON output** — `{status: PASS|FAIL|UNCERTAIN, confidence: 0.0–1.0, observation}`
- **Few-shot examples** for each status
- **Step-level expectations** — not one-size-fits-all prompts
- **Validation** — malformed output → `UNCERTAIN`, never `PASS`
- **Confidence threshold** — low-confidence FAILs are ignored
- **Quota controls** — `final_only` strategy = 1 call per test (~15 per run)
- **Circuit breaker** — one 429 stops AI for the rest of the run

`Bug #2` fixed.

### 🔒 Concurrency-safe Excel writes

`Bug #3` fixed. When tests complete in parallel (or when future code submits results concurrently):

```
Test workers  →  thread-safe Queue  →  ONE writer thread  →  Excel
```

- Only **one thread** ever touches openpyxl
- Every write **re-loads from disk** (no stale state)
- Rows located by **Test ID**, never by row number
- Excel locked by user → graceful failure, run continues

### 📄 Word report

`report_generator.py` produces a professional `test_report.docx`:
- Title + metadata + summary table (dynamic counts)
- Test results overview
- One section per test: ID, Name, Category, Status, Expected, Actual, AI block, Steps table, **embedded screenshots**
- Missing screenshots degrade gracefully to text
- Report failure never breaks the test run

---

## Bug fixes summary

| Bug | Problem | Fix |
|---|---|---|
| **#1 Screenshot timing** | Screenshots taken before content rendered / element off-screen | Composite waits + centre-scroll before capture |
| **#2 AI prompt quality** | Open-ended prompts → hallucinations, no confidence | Structured JSON, few-shot examples, step-level expectations, confidence threshold |
| **#3 Excel concurrency** | Parallel writes corrupt Excel | Queue + single writer thread + per-test reload |

---

## Configuration highlights (`automation/config.py`)

```python
BASE_URL = "http://localhost:5173"
HEADLESS = False

AI_ENABLED = True
AI_MODEL = "gemini-2.5-flash"
AI_VERIFY_STRATEGY = "final_only"     # 1 AI call per test
AI_MAX_CALLS_PER_RUN = 40
AI_CONFIDENCE_THRESHOLD = 0.80

WRITE_BACK_TO_SOURCE = True           # update sample_test_cases.xlsx in place
```

**To disable AI** (pure Playwright run, zero API calls):
```python
AI_ENABLED = False
```

---

## Verification utilities

```bash
python test_gemini.py            # Gemini key + model diagnostic
python test_excel_writer.py      # Concurrency stress test (Bug #3)
python test_report_generator.py  # Report generator unit tests
python generate_test_cases.py    # Regenerate sample_test_cases.xlsx
```

---

## Directory structure

```
AI Automation - Datakernels/
├── Hotel_Booking/              # Part 1 — React website
├── automation/                 # Parts 2-6 — Python automation
│   ├── main.py                 # Runner
│   ├── config.py               # All tunables
│   ├── excel_reader.py         # Read test cases
│   ├── excel_writer.py         # Concurrency-safe write-back
│   ├── executor.py             # Playwright step execution
│   ├── waits.py                # Bug #1 wait strategy
│   ├── screenshot_manager.py   # Centre-scroll + capture
│   ├── ai_verifier.py          # Gemini Vision integration
│   ├── report_generator.py     # Word report builder
│   └── models.py               # Dataclasses
├── test_cases/
│   ├── sample_test_cases.xlsx  # 15 test cases (input)
│   ├── test_results.xlsx       # Status + AI observations (output)
│   └── test_report.docx        # Full report (output)
├── screenshots/                # One folder per run
├── docker-compose.yml
├── Dockerfile.website
├── Dockerfile.automation
└── README.md
```

---

## Requirements

**Local:** Node.js 18+, Python 3.11+, a free Gemini API key (optional).
**Docker:** Docker Desktop 20+ with Compose v2.

---

## Environment variables

| Var | Purpose |
|---|---|
| `GOOGLE_API_KEY` or `GEMINI_API_KEY` | Gemini API key (loaded from `automation/.env`) |
| `AI_MODEL` | Override default model name |
| `BASE_URL` | Override target URL (used by Docker) |
| `HEADLESS` | `true` / `false` |

---

## Cheat sheet

```bash
# Website
cd Hotel_Booking && npm install && npm run dev

# Automation (once)
cd automation && python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
playwright install chromium

# Run
python main.py

# Verify components
python test_gemini.py
python test_excel_writer.py
python test_report_generator.py

# Docker
docker compose build
docker compose up
docker compose down
```

---

## Assumptions

- **No backend** — the website is intentionally client-side with `localStorage`, per the assignment brief.
- **No TypeScript** — per the brief.
- **Free-tier Gemini** limits daily AI calls. `final_only` + circuit breaker keeps things safe; enable billing for unlimited runs.
- **Sequential Playwright execution** — the Excel writer is already thread-safe and ready for parallel workers if needed.

---

## Tech stack

React · Vite · React Router · Python · Playwright · openpyxl · google-genai · python-docx · python-dotenv · Docker · Docker Compose

---

## License

Hiring-assignment submission — not licensed for redistribution.
