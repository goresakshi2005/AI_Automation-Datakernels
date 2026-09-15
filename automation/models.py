from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StepResult:
    """Structured result for a single executed step."""
    step_number: int
    command: str
    raw_step: str
    target: Optional[str] = None
    value: Optional[str] = None
    status: str = "NOT RUN"
    screenshot_path: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: int = 0

    # ---- AI Vision hooks (Part 4) -----------------------------------------
    ai_status: Optional[str] = None          # PASS / FAIL / UNCERTAIN / NOT RUN
    ai_confidence: Optional[float] = None    # 0.0 - 1.0
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
    status: str                              # PASS / FAIL (final aggregated)
    step_results: List[StepResult] = field(default_factory=list)
    failure_reason: Optional[str] = None
    duration_ms: int = 0

    # ---- AI Vision summary (Part 4) ---------------------------------------
    ai_status: Optional[str] = None          # PASS / FAIL / UNCERTAIN / NOT RUN
    ai_observation: Optional[str] = None

    # Aggregate counts (for Excel summary)
    ai_pass_count: int = 0
    ai_fail_count: int = 0
    ai_uncertain_count: int = 0
    ai_not_run_count: int = 0

    # Raw deterministic status before AI aggregation
    deterministic_status: Optional[str] = None