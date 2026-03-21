import pytest
from ai.context_builder import parsed_edi_to_markdown
from parser.models import ParsedEDI, EDILoop, EDISegment, EDIElement
from validator.models import ValidationResult, ValidationError, Severity

def get_mock_parsed_edi() -> ParsedEDI:
    return ParsedEDI(
        file_name="test.edi",
        transaction_type="837P",
        sender_id="SENDERID",
        receiver_id="RECEIVERID",
        interchange_date="230115",
        transaction_set_count=1,
        delimiter_segment="~",
        delimiter_element="*",
        delimiter_subelement=":",
        loops=[],
        raw_segments=[]
    )

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
                plain_english="The NPI is invalid.",
                line_number=8,
                auto_fix_available=False,
                suggested_fix=None
            )
        ]
    )

def test_no_raw_json_outside_code_blocks():
    md = parsed_edi_to_markdown(get_mock_parsed_edi(), get_mock_validation_result())
    before_code = md.split("```")[0]   # Only check text before first code block
    assert "{" not in before_code, "Raw JSON found — fix context_builder.py"

def test_markdown_contains_all_five_sections():
    md = parsed_edi_to_markdown(get_mock_parsed_edi(), get_mock_validation_result())
    assert "Section 1: File Metadata" in md
    assert "Section 2: Validation Summary" in md
    assert "Section 3: Validation Errors" in md
    assert "Section 4: Loop Structure" in md
    assert "Section 5: Key Segments" in md

def test_error_subsection_formatting():
    md = parsed_edi_to_markdown(get_mock_parsed_edi(), get_mock_validation_result())
    assert "#### Error 1: INVALID_NPI" in md
    assert "- **Value Found:** `1234567890`" in md