# Skill: Testing Patterns
## Purpose
Patterns for writing pytest tests, constructing EDI sample files, and
validating context_builder.py Markdown output.

## Key Knowledge

### pytest Invocation
```bash
pytest tests/test_parser.py -v           # Verbose output, one test per line
pytest tests/ -v --tb=short             # All tests, short traceback on failure
pytest tests/test_validator.py::test_catches_invalid_npi -v  # Single test
```

### Sample EDI File Construction
A minimal valid 837P looks like this (use * as element delimiter, ~ as terminator):
```
ISA*00*          *00*          *ZZ*SENDERID       *ZZ*RECEIVERID     *230115*1200*^*00501*000000001*0*P*:~
GS*HC*SENDERID*RECEIVERID*20230115*1200*1*X*005010X222A1~
ST*837*0001~
BHT*0019*00*BATCH001*20230115*1200*CH~
NM1*41*2*HOSPITAL NAME*****XX*1234567893~
PER*IC*CONTACT NAME*TE*5555555555~
NM1*40*2*PAYER NAME*****PI*PAYERID~
HL*1**20*1~
NM1*85*2*BILLING PROVIDER*****XX*1234567893~
N3*123 MAIN ST~
N4*ANYTOWN*CA*90210~
HL*2*1*22*0~
SBR*P*18*GROUP001****CI~
NM1*IL*1*LASTNAME*FIRSTNAME****MI*MEMBER001~
CLM*PAT001*350***11:B:1*Y*A*Y*I~
DTP*472*RD8*20230110-20230110~
SV1*HC:99213*150*UN*1***1~
LX*1~
SV1*HC:99214*200*UN*1***1~
SE*18*0001~
GE*1*1~
IEA*1*000000001~
```
NPI 1234567893 passes Luhn checksum. CLM02 = 350 = sum(150 + 200). ✓

### Malformed 837I Construction
Start from a valid 837 base, then introduce exactly these 6 mutations:
  1. Remove the NM1*85 segment (Loop 2010AA) entirely.
  2. Change the NPI value to 1234567890 (fails Luhn — last digit should be 3).
  3. Change CLM05-1 from "11" to "XX".
  4. Change DTP03 from "20230115" to "01152023".
  5. Change CLM02 from "350" to "400" (but keep SV1 lines summing to 350).
  6. Change CLM to "CLM*PAT001*400***11:B:1*Y*A*" (remove CLM09 = "I").

### Context Builder Test Pattern
```python
def test_no_raw_json_outside_code_blocks():
    md = parsed_edi_to_markdown(get_mock_parsed_edi(), get_mock_validation_result())
    before_code = md.split("```")[0]   # Only check text before first code block
    assert "{" not in before_code, "Raw JSON found — fix context_builder.py"
```

### Mock Object Pattern
```python
# tests/mocks/mock_validation.py
def get_mock_validation_result() -> ValidationResult:
    return ValidationResult(
        transaction_type="837P",
        is_valid=False,
        error_count=2,
        warning_count=0,
        errors=[
            ValidationError(error_code="INVALID_NPI", severity=Severity.ERROR,
                loop_id="2010AA", segment_id="NM1", element_position=9,
                raw_value="1234567890", expected="10-digit Luhn NPI",
                plain_english="The NPI is invalid.", line_number=8,
                auto_fix_available=False, suggested_fix=None),
            # ... second error ...
        ]
    )
```

## MUST_NOT
- MUST_NOT create more or fewer than 6 errors in malformed_837i.edi.
- MUST_NOT use NPI values that pass Luhn for the invalid NPI test case.
- MUST_NOT skip the round-trip test for the EDI writer.
- MUST_NOT run the demo rehearsal against mock data — use real files.

## Discovered During Implementation
