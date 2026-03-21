from parser.models import ParsedEDI
from validator.models import ValidationResult

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
    return "\n\n---\n\n".join(sections)