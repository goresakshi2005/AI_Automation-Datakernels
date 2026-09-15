"""
Part 4 — AI Vision verification using Google Gemini.

Design:
  * Screenshot is sent as an image to a vision-capable Gemini model.
  * Strict structured prompt asks for JSON: {status, confidence, observation}.
  * Few-shot examples + hallucination-protection rules are included.
  * Response is validated; malformed output becomes UNCERTAIN (never PASS).
  * API / key / quota errors never crash the test suite — they become UNCERTAIN.
  * Fallback model list is tried in order on 404 (model-not-found).
  * Rate limiter enforces a minimum gap between calls.
  * Quota (429) and server (503) errors short-circuit the fallback loop
    because retrying them across all models wastes the daily budget.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Optional

from config import (
    AI_ENABLED,
    AI_MODEL,
    AI_MODEL_FALLBACKS,
    AI_CONFIDENCE_THRESHOLD,
    AI_MAX_RETRIES,
    AI_MIN_SECONDS_BETWEEN_CALLS,
    GEMINI_API_KEY,
)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
@dataclass
class AIVerification:
    status: str = "NOT RUN"
    confidence: Optional[float] = None
    observation: Optional[str] = None


# ---------------------------------------------------------------------------
# Lazy client
# ---------------------------------------------------------------------------
_GENAI_CLIENT = None


def _get_genai_client():
    global _GENAI_CLIENT
    if _GENAI_CLIENT is not None:
        return _GENAI_CLIENT
    if not AI_ENABLED or not GEMINI_API_KEY:
        return None
    try:
        from google import genai  # type: ignore
        _GENAI_CLIENT = genai.Client(api_key=GEMINI_API_KEY)
        return _GENAI_CLIENT
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Rate limiter (simple, process-wide)
# ---------------------------------------------------------------------------
_rate_lock = Lock()
_last_call_ts = 0.0


def _enforce_rate_limit() -> None:
    """Sleep just enough so two calls never fire closer than the configured gap."""
    global _last_call_ts
    if AI_MIN_SECONDS_BETWEEN_CALLS <= 0:
        return
    with _rate_lock:
        now = time.monotonic()
        wait = AI_MIN_SECONDS_BETWEEN_CALLS - (now - _last_call_ts)
        if wait > 0:
            time.sleep(wait)
        _last_call_ts = time.monotonic()


# ---------------------------------------------------------------------------
# System instruction
# ---------------------------------------------------------------------------
SYSTEM_INSTRUCTION = """You are a UI test verification system.

Your job is to compare the attached screenshot with the expected visual state.

You must only judge what is visibly supported by the screenshot.

Never invent hidden UI state.
Never assume backend behavior.
Never assume an element exists if it is not visible.
Do not infer functionality that cannot be visually verified.
Never mark PASS based only on the test description.
Never mark FAIL because the UI looks different from your personal design preference.
Do not comment on colors, spacing, fonts, or aesthetics unless they hide required content.

Return ONLY valid JSON matching the requested schema.
"""


FEW_SHOT_EXAMPLES = """
EXAMPLE 1 — PASS
Expected visual state: "The booking confirmation container should be clearly visible."
Situation: The screenshot clearly shows the booking confirmation heading, content, and booking reference.
Output:
{"status":"PASS","confidence":0.98,"observation":"The booking confirmation is clearly visible with a booking reference."}

EXAMPLE 2 — FAIL
Expected visual state: "The booking confirmation container should be clearly visible."
Situation: The screenshot shows the payment form with a validation error, and no confirmation.
Output:
{"status":"FAIL","confidence":0.96,"observation":"The booking confirmation is absent; the payment form is still displayed."}

EXAMPLE 3 — UNCERTAIN
Expected visual state: "The email validation error should be visible below the email field."
Situation: The screenshot is cropped and the email field/error area is not visible.
Output:
{"status":"UNCERTAIN","confidence":0.92,"observation":"The email validation area is outside the visible screenshot."}
"""


def _build_user_prompt(
    test_id: str,
    test_name: str,
    category: str,
    step_number: int,
    step_command: str,
    step_target: Optional[str],
    step_value: Optional[str],
    expected_result: str,
    step_expectation: str,
) -> str:
    header = (
        f"Test ID: {test_id}\n"
        f"Test Name: {test_name}\n"
        f"Category: {category}\n"
        f"Step Number: {step_number}\n"
        f"Current Step: {step_command}\n"
        f"Step Target: {step_target or '(none)'}\n"
        f"Step Value: {step_value or '(none)'}\n"
        f"\n"
        f"Expected Visual State (for THIS step only):\n"
        f"{step_expectation}\n"
        f"\n"
        f"Overall Test Expected Result (for context, NOT for this step):\n"
        f"{expected_result}\n"
    )

    footer = """
Analyze the attached screenshot.

Return ONLY this JSON structure:
{
  "status": "PASS",
  "confidence": 0.97,
  "observation": "Short factual observation under 200 characters."
}

Rules:
1. status must be exactly one of: PASS, FAIL, UNCERTAIN.
2. confidence must be a number between 0.0 and 1.0.
3. PASS means the expected visual state is clearly visible in THIS screenshot.
4. FAIL means the screenshot clearly contradicts or does not satisfy the expected visual state.
5. UNCERTAIN means there is insufficient visual evidence.
6. Never invent elements, text, errors, buttons, pages, or states that are not visible.
7. Never assume a backend/database operation succeeded.
8. Never assume an element is visible if it is cropped or hidden.
9. If the screenshot is too blurry, cropped, blank, or otherwise insufficient, return UNCERTAIN.
10. Keep observation under 200 characters.
11. Return JSON only. Do not wrap JSON in Markdown code fences.
"""

    return header + "\n" + FEW_SHOT_EXAMPLES + "\n" + footer


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------
_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _strip_markdown_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = _JSON_FENCE_RE.sub("", text).strip()
    return text


def parse_ai_response(raw_text: str) -> AIVerification:
    if not raw_text or not raw_text.strip():
        return AIVerification("UNCERTAIN", None, "AI returned empty output.")

    cleaned = _strip_markdown_fences(raw_text)
    try:
        data = json.loads(cleaned)
    except Exception:
        return AIVerification("UNCERTAIN", None, "AI returned invalid structured output.")

    if not isinstance(data, dict):
        return AIVerification("UNCERTAIN", None, "AI returned non-object JSON.")

    status = str(data.get("status", "")).strip().upper()
    if status not in ("PASS", "FAIL", "UNCERTAIN"):
        return AIVerification("UNCERTAIN", None, f"Unexpected status: {status!r}")

    try:
        confidence = float(data.get("confidence"))
    except (TypeError, ValueError):
        return AIVerification("UNCERTAIN", None, "Invalid confidence value.")

    if not (0.0 <= confidence <= 1.0):
        return AIVerification("UNCERTAIN", None, "Confidence out of range.")

    observation = str(data.get("observation", "")).strip()
    if len(observation) > 200:
        observation = observation[:197] + "..."

    return AIVerification(status, confidence, observation or None)


# ---------------------------------------------------------------------------
# Step-level visual expectation
# ---------------------------------------------------------------------------
def get_step_visual_expectation(
    test_id: str,
    test_name: str,
    category: str,
    command: str,
    target: Optional[str],
    value: Optional[str],
    overall_expected_result: str,
) -> str:
    cmd = (command or "").upper()
    tgt = (target or "").strip()
    val = (value or "").strip()
    cat = (category or "").lower()
    is_validation = "validation" in cat or "-error" in tgt.lower()

    if cmd == "WAIT_FOR" and tgt.endswith("-error"):
        return (
            f"A validation error message must be visibly displayed below the "
            f"{tgt.replace('-error', '').replace('-', ' ')} field."
        )
    if cmd == "ASSERT_VISIBLE" and tgt.endswith("-error"):
        return f"The validation error message ({tgt}) must be clearly visible."

    if cmd == "OPEN":
        if tgt in ("/", ""):
            return "The hotel booking home page with the search form should be visible."
        if tgt == "/bookings":
            return "The 'My Bookings' page should be visible."
        return f"The page at {tgt} should be loaded and visible."

    if cmd == "FILL":
        field = tgt.replace("-", " ")
        if val:
            return (
                f"The form should remain visible and the '{field}' field "
                f"should contain '{val}'."
            )
        return f"The form should remain visible and the '{field}' field should be empty."

    if cmd == "CLICK":
        if tgt == "search-button":
            return "The application should navigate to the search results page showing available room cards."
        if tgt == "view-details-1":
            return "The room details page should be visible with the room name, type, and price."
        if tgt == "book-now-button":
            return "The booking form should be visible with the guest information section."
        if tgt == "confirm-booking-button":
            if is_validation:
                return "The form should remain visible with a validation error message displayed."
            return "The booking confirmation page should be visible."
        return f"After clicking {tgt}, the expected result should be visible."

    if cmd == "WAIT_FOR":
        if tgt.startswith("room-card"):
            return "Search results should display available room cards."
        if tgt == "room-name":
            return "The room details page should be visible with the room name."
        if tgt == "first-name-input":
            return "The booking form should be visible with guest information fields."
        if tgt == "booking-confirmation":
            return "The booking confirmation page should be visible."
        if tgt.startswith("booking-card"):
            return "The 'My Bookings' page should list at least one booking card."
        return f"The element '{tgt}' should be visibly present."

    if cmd == "ASSERT_VISIBLE":
        if tgt == "booking-confirmation":
            return "The booking confirmation container should be clearly visible."
        if tgt.startswith("room-card"):
            return "The room card should be clearly visible in the search results."
        if tgt == "room-name":
            return "The room name heading should be clearly visible."
        if tgt.startswith("booking-card"):
            return "At least one booking card should be clearly visible."
        return f"The element '{tgt}' should be clearly visible."

    if cmd == "ASSERT_TEXT":
        return f"The element '{tgt}' should visibly contain the text '{val}'."

    if cmd == "SCREENSHOT":
        if tgt and "validation" in tgt.lower():
            return "A validation error message should be clearly visible."
        return overall_expected_result or "The expected final state should be visible."

    if cmd in ("SELECT", "CLEAR"):
        return f"The form should remain visible and the '{tgt}' field should reflect the change."

    return f"The UI should reflect the effect of: {command} {tgt or ''}".strip()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _read_image_bytes(screenshot_path: str) -> Optional[bytes]:
    p = Path(screenshot_path)
    if not p.exists():
        return None
    try:
        return p.read_bytes()
    except Exception:
        return None


def _safe_error(exc: Exception) -> str:
    msg = str(exc)
    if GEMINI_API_KEY:
        msg = msg.replace(GEMINI_API_KEY, "***REDACTED***")
    msg = " ".join(msg.split())
    if len(msg) > 240:
        msg = msg[:237] + "..."
    return f"{type(exc).__name__}: {msg}" if msg else type(exc).__name__


def _error_code(exc: Exception) -> int:
    """Best-effort extraction of the HTTP-ish code from a google-genai error."""
    text = str(exc)
    for code in (429, 503, 500, 404, 403, 401):
        if f"{code}" in text[:200] or f"code': {code}" in text:
            return code
    if "RESOURCE_EXHAUSTED" in text:
        return 429
    if "UNAVAILABLE" in text:
        return 503
    if "NOT_FOUND" in text:
        return 404
    return 0


# ---------------------------------------------------------------------------
# Single model call
# ---------------------------------------------------------------------------
def _call_model_once(client, model_name: str, image_bytes: bytes, user_prompt: str) -> str:
    from google.genai import types  # type: ignore

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.0,
        response_mime_type="application/json",
    )

    response = client.models.generate_content(
        model=model_name,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            user_prompt,
        ],
        config=config,
    )

    text = getattr(response, "text", None)
    if not text and getattr(response, "candidates", None):
        try:
            parts = response.candidates[0].content.parts
            text = "".join(getattr(p, "text", "") or "" for p in parts)
        except Exception:
            text = None
    return text or ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def verify_step(
    screenshot_path: str,
    test_id: str = "",
    test_name: str = "",
    category: str = "",
    step_number: int = 0,
    step_command: str = "",
    step_target: Optional[str] = None,
    step_value: Optional[str] = None,
    expected_result: str = "",
    step_expectation: str = "",
) -> AIVerification:
    if not AI_ENABLED:
        return AIVerification("NOT RUN", None, "AI verification is disabled (AI_ENABLED=False).")

    if not GEMINI_API_KEY:
        return AIVerification(
            "UNCERTAIN", None,
            "AI verification unavailable: GEMINI_API_KEY / GOOGLE_API_KEY is not configured.",
        )

    image_bytes = _read_image_bytes(screenshot_path)
    if image_bytes is None:
        return AIVerification("UNCERTAIN", None, "Screenshot file is missing or unreadable.")

    client = _get_genai_client()
    if client is None:
        return AIVerification(
            "UNCERTAIN", None,
            "AI verification unavailable: google-genai SDK not installed or client failed.",
        )

    if not step_expectation:
        step_expectation = get_step_visual_expectation(
            test_id, test_name, category,
            step_command, step_target, step_value, expected_result,
        )

    user_prompt = _build_user_prompt(
        test_id, test_name, category, step_number,
        step_command, step_target, step_value,
        expected_result, step_expectation,
    )

    models_to_try: list[str] = []
    for m in [AI_MODEL] + list(AI_MODEL_FALLBACKS):
        if m and m not in models_to_try:
            models_to_try.append(m)

    last_error = "unknown error"
    last_code = 0

    for model_name in models_to_try:
        for attempt in range(AI_MAX_RETRIES + 1):
            try:
                _enforce_rate_limit()
                raw_text = _call_model_once(client, model_name, image_bytes, user_prompt)
                parsed = parse_ai_response(raw_text)

                if parsed.status != "UNCERTAIN":
                    return parsed

                if attempt < AI_MAX_RETRIES:
                    continue
                last_error = f"model {model_name}: {parsed.observation}"
                break

            except Exception as e:
                code = _error_code(e)
                last_code = code
                last_error = f"model {model_name}: {_safe_error(e)}"

                # 429 / 503 -> quota or server-side issue; trying other models
                # will just burn the daily budget. Stop immediately.
                if code in (429, 503):
                    if code == 429:
                        return AIVerification(
                            "UNCERTAIN", None,
                            "AI quota exhausted (429). Reduce AI_VERIFY_EVERY_SCREENSHOT "
                            "or wait for quota reset. " + last_error,
                        )
                    return AIVerification(
                        "UNCERTAIN", None,
                        "AI service temporarily unavailable (503). " + last_error,
                    )

                # 404 -> wrong model name; try next fallback.
                # Anything else -> try next fallback too.
                break

    return AIVerification(
        "UNCERTAIN", None,
        f"AI verification unavailable. {last_error}",
    )


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------
def aggregate_final_status(
    deterministic_status: str,
    step_results,
    confidence_threshold: float = AI_CONFIDENCE_THRESHOLD,
):
    if deterministic_status != "PASS":
        return ("FAIL", "FAIL", "Deterministic Playwright checks failed.")

    if not AI_ENABLED:
        return ("PASS", "NOT RUN", "AI verification disabled.")

    counts = {"PASS": 0, "FAIL": 0, "UNCERTAIN": 0, "NOT RUN": 0}
    high_conf_fails = []

    for sr in step_results:
        s = (sr.ai_status or "NOT RUN").upper()
        if s not in counts:
            s = "NOT RUN"
        counts[s] += 1
        if (
            s == "FAIL"
            and sr.ai_confidence is not None
            and sr.ai_confidence >= confidence_threshold
        ):
            high_conf_fails.append(sr)

    if high_conf_fails:
        final_step_num = max((sr.step_number for sr in step_results), default=0)
        fails_on_final = [f for f in high_conf_fails if f.step_number == final_step_num]

        # Only let AI override the deterministic result when the failure is
        # on the final frame OR when at least two independent checkpoints fail.
        if fails_on_final or len(high_conf_fails) >= 2:
            worst = max(high_conf_fails, key=lambda x: x.ai_confidence or 0)
            return (
                "FAIL", "FAIL",
                f"High-confidence AI visual mismatch at step {worst.step_number} "
                f"({int((worst.ai_confidence or 0) * 100)}%): {worst.ai_observation or ''}".strip(),
        )
        # Otherwise: record the uncertainty but don't fail the run.
        return (
            "PASS", "UNCERTAIN",
            f"Deterministic checks passed. {len(high_conf_fails)} isolated AI FAIL(s) below the 2-hit threshold.",
        )

    if counts["FAIL"] > 0:
        return (
            "PASS", "UNCERTAIN",
            f"Deterministic checks passed. {counts['FAIL']} low-confidence AI FAIL(s) ignored.",
        )

    if counts["UNCERTAIN"] > 0:
        return (
            "PASS", "UNCERTAIN",
            f"Deterministic checks passed; AI was UNCERTAIN on {counts['UNCERTAIN']} checkpoint(s).",
        )

    if counts["PASS"] > 0:
        return (
            "PASS", "PASS",
            f"All {counts['PASS']} AI visual checkpoint(s) passed.",
        )

    return ("PASS", "NOT RUN", "No AI checkpoints evaluated.")