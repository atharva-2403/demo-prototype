from parser.models import ParsedEDI
from validator.models import ValidationError
import re
from datetime import datetime

def fix_date(raw: str) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"[^0-9]", "", raw)
    if len(digits) == 8:
        try:
            return datetime.strptime(digits, "%m%d%Y").strftime("%Y%m%d")
        except ValueError:
            return None
    return None

def fix_zip(raw: str) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"[^0-9]", "", raw)
    return digits if len(digits) in (5, 9) else None

def fix_clm_amount(error: ValidationError, parsed: ParsedEDI) -> str | None:
    if error.expected:
        return error.expected
    return None

def suggest_fix(error: ValidationError, parsed: ParsedEDI) -> str | None:
    if error.error_code == "INVALID_DATE_FORMAT":
        return fix_date(error.raw_value)
    elif error.error_code == "INVALID_ZIP":
        return fix_zip(error.raw_value)
    elif error.error_code == "CLM_AMOUNT_MISMATCH":
        return fix_clm_amount(error, parsed)
    return None