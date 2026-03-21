# Skill: Export System Patterns
## Purpose
Patterns for PDF export (ReportLab), CSV export, JSON export, corrected EDI
writer, and deterministic fix suggestion logic.

## Key Knowledge

### Deterministic Fix Patterns
These are the only three error types with auto-fixable values. All other errors
require human intervention. Never call the LLM to generate fixes.

```python
# Date format fix: MMDDYYYY → CCYYMMDD
def fix_date(raw: str) -> str | None:
    digits = re.sub(r"[^0-9]", "", raw)
    if len(digits) == 8:
        try: return datetime.strptime(digits, "%m%d%Y").strftime("%Y%m%d")
        except ValueError: return None

# ZIP code fix: strip non-digits
def fix_zip(raw: str) -> str | None:
    digits = re.sub(r"[^0-9]", "", raw)
    return digits if len(digits) in (5, 9) else None

# CLM amount fix: sum the SV1-02 values in the associated 2400 loops
def fix_clm_amount(error, parsed) -> str | None:
    total = sum SV1-02 values in Loop 2400 associated with this CLM
    return f"{total:.2f}" if total > 0 else None
```

### ReportLab PDF Pattern
```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def generate_pdf(parsed, validation) -> bytes:
    from io import BytesIO
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    # Add title, metadata table, validation summary, error table
    doc.build(elements)
    return buffer.getvalue()
```

### EDI Writer (Round-Trip) Pattern
```python
def write_edi(parsed: ParsedEDI) -> str:
    lines = []
    ed = parsed.delimiter_element
    st = parsed.delimiter_segment
    for seg in parsed.raw_segments:
        elements = [seg.id] + [e.value for e in seg.elements]
        lines.append(ed.join(elements) + st)
    return "\n".join(lines)
# After writing, parse the output and confirm same transaction_type and segment count.
```

## MUST_NOT
- MUST_NOT call the LLM for fix suggestions — all fixes are rule-based.
- MUST_NOT attempt to fix errors other than the three types listed above.
- MUST_NOT forget the round-trip test on the EDI writer.

## Discovered During Implementation
