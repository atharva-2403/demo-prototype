import os
os.environ["TESTING"] = "1"
import pytest
from parser.state_machine import parse_edi
from validator.rule_engine import RuleEngine

def read_sample(filename):
    path = os.path.join(os.path.dirname(__file__), "sample_files", filename)
    with open(path, "r") as f:
        return f.read()

def test_validator_catches_all_6_errors_in_malformed_837i():
    content = read_sample("malformed_837i.edi")
    parsed = parse_edi(content)
    engine = RuleEngine("837I")
    result = engine.validate(parsed)
    
    assert not result.is_valid
    error_codes = [e.error_code for e in result.errors]
    
    assert "MISSING_BILLING_PROVIDER" in error_codes
    assert "INVALID_NPI" in error_codes
    assert "INVALID_FACILITY_CODE" in error_codes
    assert "INVALID_DATE_FORMAT" in error_codes
    assert "CLM_AMOUNT_MISMATCH" in error_codes
    assert "MISSING_ROI_CODE" in error_codes
    
    assert result.error_count == 6

def test_validator_passes_valid_837p():
    content = read_sample("valid_837p.edi")
    parsed = parse_edi(content)
    engine = RuleEngine("837P")
    result = engine.validate(parsed)
    assert result.is_valid
    assert result.error_count == 0