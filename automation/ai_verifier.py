"""
Placeholder interface for AI Vision verification (Part 3 Stage 2).

Do NOT call any real AI here yet. This file only defines the shape of the
future integration so that Stage 2 can plug in without touching main.py.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class AIVerification:
    status: str = "NOT RUN"            # PASS / FAIL / UNCERTAIN / NOT RUN
    confidence: Optional[float] = None  # 0.0 - 1.0
    observation: Optional[str] = None


def verify_step(
    screenshot_path: str,
    step_command: str,
    expected_result: str,
) -> AIVerification:
    """
    Stage 2 will replace this body with a structured-prompt call to a Vision API.
    For now: explicitly signal that verification has not run.
    """
    return AIVerification(
        status="NOT RUN",
        confidence=None,
        observation="AI verification not implemented yet (Part 3 Stage 2).",
    )