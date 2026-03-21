from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class ValidationError(BaseModel):
    error_code: str
    severity: Severity
    loop_id: str
    segment_id: str
    element_position: int
    raw_value: Optional[str]
    expected: Optional[str]
    plain_english: str
    line_number: int
    auto_fix_available: bool
    suggested_fix: Optional[str]

class ValidationResult(BaseModel):
    transaction_type: str
    is_valid: bool
    error_count: int
    warning_count: int
    errors: List[ValidationError]