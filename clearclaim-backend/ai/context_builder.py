import re
from parser.models import ParsedEDI
from validator.models import ValidationResult

def mask_phi(text: str) -> str:
    # Mask SSN patterns (9 digits with or without dashes)
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED_PHI]', text)
    # Be careful not to redact valid non-PHI 9-digit numbers like some zip codes or standard codes, 
    # but in a strict HIPAA environment we mask 9-digit sequences that could be SSNs
    text = re.sub(r'\b\d{9}\b', '[REDACTED_PHI]', text)
    # Mask typical Date of Birth patterns (e.g., YYYYMMDD if they look like a typical DOB)
    # For safety, we mask any 8 digit string that starts with 19 or 20 as it could be a DOB (YYYYMMDD)
    text = re.sub(r'\b(19|20)\d{2}(0[1-9]|1[012])(0[1-9]|[12][0-9]|3[01])\b', '[REDACTED_PHI]', text)
    # Also mask MM/DD/YYYY or YYYY-MM-DD
    text = re.sub(r'\b(19|20)\d{2}[-/.](0[1-9]|1[012])[-/.](0[1-9]|[12][0-9]|3[01])\b', '[REDACTED_PHI]', text)
    text = re.sub(r'\b(0[1-9]|1[012])[-/.](0[1-9]|[12][0-9]|3[01])[-/.](19|20)\d{2}\b', '[REDACTED_PHI]', text)
    return text

def _build_metadata_section(parsed: ParsedEDI) -> str:
    lines = [
        "### Section 1: File Metadata",
        "",
        "| Property | Value |",
        "|---|---|",
        f"| File Name | {parsed.file_name} |",
        f"| Transaction Type | {parsed.transaction_type} |",
        f"| Sender ID | {parsed.sender_id} |",
        f"| Receiver ID | {parsed.receiver_id} |",
        f"| Interchange Date | {parsed.interchange_date} |",
        f"| Segment Count | {len(parsed.raw_segments)} |"
    ]
    return "\n".join(lines)

def _build_validation_summary_section(validation: ValidationResult) -> str:
    lines = [
        "### Section 2: Validation Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Is Valid | {validation.is_valid} |",
        f"| Error Count | {validation.error_count} |",
        f"| Warning Count | {validation.warning_count} |"
    ]
    return "\n".join(lines)

def _build_errors_section(validation: ValidationResult) -> str:
    if not validation.errors:
        return "### Section 3: Validation Errors\n\nNo errors found."
        
    lines = ["### Section 3: Validation Errors\n"]
    for i, err in enumerate(validation.errors[:20], 1):
        lines.append(f"#### Error {i}: {err.error_code}\n")
        lines.append(f"- **Severity:** {err.severity.value.upper()}")
        lines.append(f"- **Location:** Loop `{err.loop_id}` -> Segment `{err.segment_id}` -> Element `{err.element_position}`")
        lines.append(f"- **Line Number:** {err.line_number}")
        lines.append(f"- **Value Found:** `{err.raw_value}`")
        lines.append(f"- **Expected:** {err.expected}")
        lines.append(f"- **Auto-Fix Available:** {'Yes' if err.auto_fix_available else 'No'}")
        if err.suggested_fix:
            lines.append(f"- **Suggested Fix:** `{err.suggested_fix}`")
        lines.append(f"\n**Explanation:** {err.plain_english}\n")
        
    if len(validation.errors) > 20:
        lines.append(f"\n*(Note: {len(validation.errors) - 20} more errors not shown due to context limits)*")
        
    return "\n".join(lines)

def _build_loop_structure_section(parsed: ParsedEDI) -> str:
    lines = ["### Section 4: Loop Structure\n"]
    def _traverse(loop, depth=0):
        indent = "  " * depth
        lines.append(f"{indent}- **{loop.loop_id}** ({loop.loop_name})")
        for child in loop.children:
            _traverse(child, depth + 1)
    
    for l in parsed.loops:
        _traverse(l)
        
    if not parsed.loops:
        lines.append("No loops detected.")
    return "\n".join(lines)

def _build_key_segments_section(parsed: ParsedEDI) -> str:
    lines = ["### Section 5: Key Segments\n", "```text"]
    for seg in parsed.raw_segments[:20]:
        labels = []
        for el in seg.elements[:3]: # show first 3 elements for brevity
            labels.append(f"{el.label}: {el.value}")
        details = " | ".join(labels)
        lines.append(f"Line {seg.line_number:>4}  [{seg.loop_id:<8}]  {seg.id:<6}  {details}")
    
    if len(parsed.raw_segments) > 20:
        lines.append(f"\n... ({len(parsed.raw_segments) - 20} more segments not shown)")
    
    lines.append("```")
    return "\n".join(lines)

def parsed_edi_to_markdown(parsed: ParsedEDI, validation: ValidationResult) -> str:
    sections = [
        _build_metadata_section(parsed),
        _build_validation_summary_section(validation),
        _build_errors_section(validation),
        _build_loop_structure_section(parsed),
        _build_key_segments_section(parsed),
    ]
    raw_markdown = "\n\n---\n\n".join(sections)
    return mask_phi(raw_markdown)