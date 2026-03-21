from validator.models import ValidationResult, ValidationError, Severity

def get_mock_validation_result() -> ValidationResult:
    return ValidationResult(
        transaction_type="837P",
        is_valid=False,
        error_count=1,
        warning_count=0,
        errors=[
            ValidationError(
                error_code="INVALID_NPI",
                severity=Severity.ERROR,
                loop_id="2010AA",
                segment_id="NM1",
                element_position=9,
                raw_value="1234567890",
                expected="10-digit Luhn NPI",
                plain_english="The NPI '{raw_value}' is invalid.",
                line_number=8,
                auto_fix_available=False,
                suggested_fix=None
            )
        ]
    )