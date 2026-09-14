from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StepResult:
    """Structured result for a single executed step.

    This is the unit that Stage 2 (AI Vision) will consume.
    """
    step_number: int
    command: str                       # e.g. "CLICK", "FILL"
    raw_step: str                      # original line from Excel
    target: Optional[str] = None
    value: Optional[str] = None
    status: str = "NOT RUN"            # PASS / FAIL
    screenshot_path: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: int = 0

    # ---- AI hooks (Stage 2) ------------------------------------------------
    ai_status: Optional[str] = None    # PASS / FAIL / UNCERTAIN / NOT RUN
    ai_confidence: Optional[float] = None
    ai_observation: Optional[str] = None


@dataclass
class TestCase:
    test_id: str
    test_name: str
    category: str
    raw_steps: str
    expected_result: str
    status: str = "NOT RUN"
    ai_observation: Optional[str] = None


@dataclass
class TestExecutionResult:
    test_id: str
    test_name: str
    category: str
    expected_result: str
    status: str                        # PASS / FAIL
    step_results: List[StepResult] = field(default_factory=list)
    failure_reason: Optional[str] = None
    duration_ms: int = 0
    ai_status: Optional[str] = None
    ai_observation: Optional[str] = None