# Skill: Markdown Context Schema for LLM
## Purpose
Defines the exact five-section Markdown schema used to convert ParsedEDI and
ValidationResult objects into LLM-consumable context. This is the most important
skill in the project — it governs the core AI quality constraint.

## Key Knowledge

### Why Markdown Not JSON
LLMs reason over Markdown more accurately than raw JSON because:
- Headers give the model section-level semantic anchors
- Tables let the model reference rows by Property name
- Numbered subsections allow precise citation ("see Error 3")
- Fenced code blocks show raw values without rendering interference
- Nested lists make hierarchy visually explicit

Raw JSON forces the model to infer meaning from brace depth and key names
alone, which produces vague and sometimes inaccurate answers.

### The Five-Section Schema (FIXED ORDER — NEVER CHANGE)
```
Section 1: File Metadata        → Markdown table
Section 2: Validation Summary   → Markdown table
Section 3: Validation Errors    → Numbered subsections (### Error N:)
Section 4: Loop Structure       → Nested Markdown list
Section 5: Key Segments         → Fenced code block, max 20 segments
```

### Section 3 Error Subsection Format
```markdown
### Error 1: ERROR_CODE_HERE

- **Severity:** ERROR
- **Location:** Loop `2300` → Segment `CLM` → Element `2`
- **Line Number:** 15
- **Value Found:** `350.00`
- **Expected:** Sum of service lines
- **Auto-Fix Available:** Yes
- **Suggested Fix:** `425.00`

**Explanation:** Plain English explanation here.
```

### Section 5 Segment Line Format
```
Line   15  [2300    ]  CLM     Claim ID: PAT001 | Billed Amount: 350.00
```
Format: `Line {num:>4}  [{loop_id:<8}]  {seg_id:<6}  {label}: {value} | ...`

### Token Budget Rules
- Cap Section 3 at 20 errors maximum — add "X more errors not shown" note.
- Cap Section 5 at 20 segments maximum — add "X more segments not shown" note.
- Total document should not exceed ~4000 tokens for a typical file.

### The Master Conversion Function
```python
def parsed_edi_to_markdown(parsed: ParsedEDI, validation: ValidationResult) -> str:
    sections = [
        _build_metadata_section(parsed),
        _build_validation_summary_section(validation),
        _build_errors_section(validation),
        _build_loop_structure_section(parsed),
        _build_key_segments_section(parsed),
    ]
    return "\n\n---\n\n".join(sections)
```
This is the ONLY function that chat.py should call. Never inline the conversion.

## MUST_NOT
- MUST_NOT pass raw JSON or Python dicts to the LLM — always call parsed_edi_to_markdown().
- MUST_NOT change the section order — LLM relies on section positions.
- MUST_NOT skip the cap on errors/segments — large files will overflow context.
- MUST_NOT use .json() or .dict() output in the LLM message — these produce JSON.

## Test That Enforces This Skill
test_no_raw_json_outside_code_blocks in tests/test_context_builder.py
This test MUST pass before chat.py is considered complete.

## Discovered During Implementation
