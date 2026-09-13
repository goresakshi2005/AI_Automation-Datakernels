from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class TestStep:
    step_number: int
    command: str
    target: Optional[str] = None
    value: Optional[str] = None
    status: str = "NOT RUN"
    screenshot: Optional[str] = None
    error: Optional[str] = None

@dataclass
class TestCase:
    test_id: str
    test_name: str
    category: str
    raw_steps: str
    expected_result: str
    status: str = "NOT RUN"
    ai_observation: Optional[str] = None
    
    # For execution
    steps: List[TestStep] = field(default_factory=list)
    actual_result: Optional[str] = None
    screenshots: List[str] = field(default_factory=list)
    error: Optional[str] = None
    
    # Part 3 placeholders
    ai_status: Optional[str] = None
    ai_confidence: Optional[str] = None

@dataclass
class TestExecutionResult:
    test_id: str
    test_name: str
    status: str
    expected_result: str
    actual_result: str
    steps: List[Dict[str, Any]]
    screenshots: List[str]
    error: Optional[str]
    ai_status: Optional[str] = None
    ai_confidence: Optional[str] = None
    ai_observation: Optional[str] = None
