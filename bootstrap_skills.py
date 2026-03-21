import os

os.makedirs('skills', exist_ok=True)

skills = {
    "orchestrator.skill.md": """# Skill: Orchestrator
## Purpose
Governs how the Primary Orchestrator Agent delegates tasks, enforces parallelism
rules, and manages the session lifecycle.

## Key Knowledge
- Phase 0 (Skills) and Phase 1 (Scaffolding) are strictly sequential.
- After Phase 1, Subagents A, C, and D-partial run in parallel.
- Subagent B cannot start Phase 3 until Subagent A completes Phase 2.
- Subagent D cannot finish chat.py until Phase 3 is complete.
- The tracker file ClearClaim_Unfinished_Work.md is the single source of truth.
- Skills are stored in clearclaim/skills/ and must all exist before any subagent is invoked.

## Delegation Pattern
When delegating a task, always include:
  1. The subagent system prompt (from Subagent Definitions section)
  2. The task number (e.g. "Task 2.1")
  3. The list of skill file paths to load
  4. The current state of the task checklist
  5. The path to ClearClaim_Unfinished_Work.md for updates

## MUST_NOT
- Never skip Phase 0. Skills must exist before any subagent is invoked.
- Never restart a completed phase on resumption — check the tracker first.
- Never let a subagent proceed past a test failure without logging the error.
- Never stop mid-session without writing to the tracker file.

## Discovered During Implementation
""",
    "edi_core.skill.md": """# Skill: X12 EDI Core
## Purpose
Foundational X12 EDI knowledge shared by all agents that touch EDI data.
This skill encodes the structural rules and gotchas of the X12 format so
subagents do not need to rediscover them from scratch.

## Key Knowledge

### Physical Structure
An X12 file is a set of nested envelopes:
  ISA/IEA  — Interchange (outermost, identifies sender and receiver)
  GS/GE    — Functional Group (groups related transaction sets)
  ST/SE    — Transaction Set (one document: one 837, 835, or 834)
  Loop     — Hierarchical grouping of segments (implicit, not explicit)
  Segment  — One line of data e.g. CLM*PAT001*500***11:B:1*Y*A*Y*I~
  Element  — One field within a segment, separated by element delimiter
  Subelement — Field within a composite element, e.g. CLM05 = "11:B:1"

### The Bootstrapping Problem
X12 files define their own delimiter characters inside the ISA header.
You cannot split the file on any delimiter until you have first read the
ISA header to learn what the delimiters are. Resolution:
  - ISA is always exactly 106 characters long
  - Character at position 3 is the element delimiter (commonly *)
  - Character at ISA16 position + 1 is the segment terminator (commonly ~)
  - First character of ISA16's value is the subelement delimiter (commonly :)
Never hardcode *, ~, or : — always read from ISA positions.

### Loop Boundary Detection
X12 loops have NO explicit open/close markers (unlike XML). Loop boundaries
are inferred from which segment ID and qualifier value appears next.
For example: NM1 with qualifier "85" opens Loop 2010AA (Billing Provider Name).
The next NM1 with a different qualifier implicitly closes 2010AA and opens
the next applicable loop. This is why a state machine with a YAML grammar
is the right parser architecture — not a simple line-by-line reader.

### Transaction Type Detection
GS01 functional identifier: HC = 837 claims, HP = 835 remittance, BE = 834 enrollment
ST01 transaction set code: 837, 835, or 834
For 837P vs 837I: check BHT06 — "CH" = claims (837P), "RP" = encounters (837I)

### Common Segment IDs
ISA = Interchange header | GS = Functional group header | ST = Transaction set header
NM1 = Entity name | CLM = Claim information | SV1 = Professional service line
CLP = Claim level payment | CAS = Claim adjustment | INS = Subscriber information
DTP = Date/time | REF = Reference identification | HL = Hierarchical level
N3/N4 = Address | LX = Service line number | SE/GE/IEA = Closing envelopes

## MUST_NOT
- MUST_NOT hardcode delimiter characters — always bootstrap from ISA.
- MUST_NOT crash the parser on malformed segments — wrap in try/except.
- MUST_NOT use third-party EDI parsing libraries — the state machine is custom.
- MUST_NOT confuse element position (1-indexed) with list index (0-indexed).

## Discovered During Implementation
""",
    "edi_837.skill.md": """# Skill: X12 837 — Medical Claims
## Purpose
Loop grammar, required segments, and validation rules specific to 837P/837I.

## Key Knowledge

### 837P vs 837I Distinction
837P = Professional claims (doctor office visits, CMS-1500 form)
837I = Institutional claims (hospital stays, UB-04 form)
Both share the same outer loop structure but differ in service line segments:
  837P uses SV1 (professional service) — CPT/HCPCS codes
  837I uses SV2 (institutional service) — revenue codes

### Critical Loop IDs (837P)
2000A = Billing Provider (HL with qualifier "20")
2010AA = Billing Provider Name (NM1 with qualifier "85") — REQUIRED
2010AB = Pay-to Address (NM1 with qualifier "87") — optional
2000B = Subscriber (HL with qualifier "22")
2010BA = Subscriber Name (NM1 with qualifier "IL") — REQUIRED
2300  = Claim Information (opened by CLM segment) — REQUIRED
2310B = Rendering Provider (NM1 with qualifier "82") — situational
2400  = Service Line (opened by LX segment, one per procedure)

### Required Segments in Loop 2300
CLM  — Claim Information (REQUIRED — missing = immediate rejection)
  CLM01 = Claim ID, CLM02 = Billed Amount, CLM05 = Facility/Claim info composite
  CLM05-1 = Facility Type Code (must be valid CMS Place of Service code)
  CLM05-3 = Claim Frequency Code (usually "1" for original)
  CLM09 = Release of Information Code (REQUIRED — "Y" or "I")
DTP  — Service dates, using qualifier 472 for service date range
REF  — Reference numbers (prior auth, etc.)

### CLM Amount Validation
CLM02 (total billed amount) MUST equal the sum of all SV1-02 amounts in
the associated Loop 2400 service lines. This is the most common billing error.

### Valid Facility Type Codes (CLM05-1)
11=Office, 12=Home, 21=Inpatient Hospital, 22=Outpatient Hospital, 23=ER,
31=Skilled Nursing, 41=Ambulance Land, 49=Independent Clinic, 50=FQHC,
51=Inpatient Psych, 52=Psych Partial Hospital, 61=Comprehensive IP Rehab,
65=End-Stage Renal, 71=State/Local Public Health, 81=Independent Lab, 99=Other

### The 6 Deliberate Errors in malformed_837i.edi
Error 1: Missing NM1 segment in Loop 2010AA (required billing provider name)
Error 2: NPI value "1234567890" — does not pass Luhn algorithm
Error 3: CLM05-1 = "XX" — not in valid facility code list above
Error 4: DTP03 = "01152023" — MMDDYYYY format instead of CCYYMMDD (20230115)
Error 5: CLM02 total does not match sum of SV1-02 values
Error 6: CLM09 is missing — release of information code is mandatory

## MUST_NOT
- MUST_NOT use 837P loop definitions for 837I files — create separate YAMLs.
- MUST_NOT treat CLM05 as a simple element — it is a composite (subelements).
- MUST_NOT validate CLM amount without first collecting all SV1 lines in 2400.

## Discovered During Implementation
""",
    "edi_835.skill.md": """# Skill: X12 835 — Remittance Advice
## Purpose
Loop grammar, CLP/CAS structure, and validation rules for 835 files.

## Key Knowledge

### What an 835 Does
835 is the Electronic Remittance Advice (ERA) — the insurer's response to
an 837 claim. It explains what was paid, what was adjusted, and why.
Every CLP loop corresponds to one claim from the original 837.

### Critical Loop IDs (835)
1000A = Payer (NM1 with qualifier "PR") — who is paying
1000B = Payee (NM1 with qualifier "PE") — who is receiving payment
2000  = Claim Payment (one per claim paid/adjusted/denied)
2100  = Claim Payment Information (contains CLP segment) — REQUIRED
2110  = Service Payment Information (one per service line, optional)

### CLP Segment Structure
CLP01 = Claim Submitter Control Number (links back to CLM01 in 837)
CLP02 = Claim Status Code: 1=Processed as Primary, 2=Processed as Other,
        3=Forwarded to Additional Payer, 4=Denied
CLP03 = Total Charge Amount (billed)
CLP04 = Payment Amount
CLP05 = Patient Responsibility Amount

### CAS Segment — Adjustment Reason Codes
CAS segments explain why the insurer paid less than billed.
CAS01 = Group Code (REQUIRED — must be one of: PR, CO, OA, PI)
  PR = Patient Responsibility (patient owes this)
  CO = Contractual Obligation (provider agreed to write this off)
  OA = Other Adjustment
  PI = Payer Initiated (insurer's decision)
CAS02 = Claim Adjustment Reason Code (CARC) — numeric code
CAS03 = Adjustment Amount

### 835-to-837 Reconciliation
Match CLP01 (payment) to CLM01 (original claim) by value.
Discrepancy = CLP03 (billed) minus CLP04 (paid) minus CAS adjustment amounts.

## MUST_NOT
- MUST_NOT attempt 835 parsing with 837 loop definitions — they are different.
- MUST_NOT skip CAS group code validation — invalid codes cause processing errors.

## Discovered During Implementation
""",
    "edi_834.skill.md": """# Skill: X12 834 — Benefit Enrollment
## Purpose
Loop grammar, INS segment rules, and validation for 834 enrollment files.

## Key Knowledge

### What an 834 Does
834 is the Benefit Enrollment and Maintenance transaction — employers use it
to tell insurers which employees to add, change, or terminate from coverage.
Errors here can leave employees uninsured without their knowledge.

### Critical Loop IDs (834)
1000A = Sponsor (employer) — NM1 with qualifier "P5"
1000B = Payer (insurer) — NM1 with qualifier "IN"
2000  = Member Level Detail (one per member/subscriber)
2100A = Member Name (NM1 with qualifier "IL")
2200  = Disability Information (situational)
2300  = Health Coverage (one per benefit plan enrolled)
2310  = Additional Member Health Coverage (situational)
2320  = Coordination of Benefits (COB — situational)

### INS Segment Structure (opens Loop 2000)
INS01 = Yes/No Indicator (Y = subscriber, N = dependent)
INS02 = Individual Relationship Code: 18=Self, 01=Spouse, 19=Child
INS03 = Maintenance Type Code (REQUIRED):
  001 = Change (attribute modification)
  021 = Addition (new enrollment)
  024 = Cancellation/Termination
  025 = Reinstatement
  030 = Audit/Compare
  032 = Employee Information Not Applicable
INS04 = Maintenance Reason Code (why this change is happening)

### REF Segment for Member ID
REF with qualifier "0F" carries the subscriber group/member number.
This is the unique identifier for cross-referencing members across files.
Duplicate REF*0F values in the same 834 file is a critical error.

### HD Segment for Health Coverage
HD01 = Maintenance Type Code (must match INS03)
HD03 = Insurance Line Code: HE=Health, DE=Dental, VI=Vision
HD04 = Plan Coverage Description

### DTP Segments for Coverage Dates
DTP with qualifier 348 = Benefit Begin Date
DTP with qualifier 349 = Benefit End Date
Date format must be CCYYMMDD (same as all X12 dates)

### Colour Coding for EnrollmentSummary UI
INS03 = "021" → green row (Addition)
INS03 = "024" → red row (Termination/Cancellation)
INS03 = "001" → yellow row (Change)
All other values → grey row

## MUST_NOT
- MUST_NOT allow duplicate REF*0F values in the same 834 file.
- MUST_NOT skip DTP format validation — wrong dates cause coverage gaps.
- MUST_NOT use INS02 (relationship) when you need INS03 (maintenance type).

## Discovered During Implementation
""",
    "parser.skill.md": """# Skill: X12 State Machine Parser
## Purpose
Implementation patterns and architecture for the ClearClaim EDI state machine.

## Key Knowledge

### Why a State Machine (Not a Line Reader)
X12 loop boundaries are implicit — determined by segment ID + qualifier.
A simple line reader cannot know "which loop am I in" because the loop
grammar is recursive and context-dependent. A state machine with a current
state variable and a YAML-driven transition table is the correct architecture.

### State Machine Pattern
```python
class ParserState:
    def __init__(self):
        self.current_loop_stack = []   # Stack of currently open loops
        self.loop_tree = []            # Final output tree being built

    def transition(self, segment_id: str, qualifier: str, loop_defs: list):
        # Check if this segment opens a new loop at the current depth
        for loop_def in loop_defs:
            if loop_def["opening_segment"] == segment_id:
                qualifier_match = loop_def.get("opening_qualifier")
                if qualifier_match is None or qualifier == qualifier_match["value"]:
                    # Open this loop: push to stack, create EDILoop node
                    new_loop = EDILoop(loop_id=loop_def["loop_id"], ...)
                    self.current_loop_stack.append(new_loop)
                    return new_loop
        # Segment belongs to current open loop — append to it
        return self.current_loop_stack[-1] if self.current_loop_stack else None
```

### YAML Loop Definition Schema
```yaml
loop_id: "2300"
name: "Claim Information"
opening_segment: "CLM"       # Segment ID that opens this loop
opening_qualifier: null       # null = any occurrence opens the loop
                              # {element: 1, value: "85"} = only when qualifier matches
children:
  - loop_id: "2400"
    name: "Service Line"
    opening_segment: "LX"
    opening_qualifier: null
```

### Subelement Delimiter Handling
Composite elements (like CLM05 = "11:B:1") contain subelements separated
by the subelement delimiter. Split composite values on the subelement
delimiter and label each subelement as SEGMENT_POSITION_SUBELEMENT:
  CLM05 → CLM_05_01 = "11", CLM_05_02 = "B", CLM_05_03 = "1"

### Error Resilience Pattern
```python
for line_num, raw_seg in enumerate(segments_raw, 1):
    try:
        # ... parse segment normally ...
    except Exception as e:
        # Never crash — add a placeholder and continue
        parsed_segments.append(EDISegment(
            id="UNPARSEABLE", loop_id="UNKNOWN",
            elements=[], raw_line=raw_seg, line_number=line_num
        ))
```

## MUST_NOT
- MUST_NOT hardcode delimiters — always bootstrap from ISA header first.
- MUST_NOT use third-party EDI libraries — write the state machine from scratch.
- MUST_NOT crash the parser on a malformed segment — always use try/except.
- MUST_NOT write state_machine.py before the loop definition YAML files exist.
- MUST_NOT forget to handle composite elements (subelement delimiter splitting).

## Discovered During Implementation
""",
    "validator.skill.md": """# Skill: YAML-Driven Validation Engine
## Purpose
Schema for YAML rule objects and implementation patterns for the rule engine.

## Key Knowledge

### YAML Rule Schema
Every rule must have these fields:
```yaml
rule_id: "UNIQUE_ID_001"        # Unique across all rule files
description: "Human-readable description of what this rule checks"
applies_to_types: ["837P"]      # Which transaction types this applies to
check_type: "enum"              # See Check Type Catalogue below
severity: "error"               # "error" or "warning"
error_code: "SNAKE_CASE_CODE"   # Code used in ValidationError object
plain_english: "Non-technical explanation with {raw_value} placeholder"
```
Additional fields depend on check_type (see catalogue below).
The plain_english field MUST be actionable — not "Invalid value" but
"The facility code '{raw_value}' is not a CMS Place of Service code.
Common codes: 11 (Office), 21 (Inpatient Hospital)."

### Check Type Catalogue
```
required_segment  — flags if a segment ID is missing from a loop
  Extra fields: loop_id, segment_id

regex             — validates element value against a regex pattern
  Extra fields: segment_id, element_position, pattern
  Optional: condition {when_element, when_value}

enum              — validates element value is in a list of valid values
  Extra fields: segment_id, element_position, valid_values (list)

luhn              — validates NPI using Luhn checksum algorithm
  Extra fields: segment_id, element_position
  Optional: condition {when_element, when_value}

cross_segment_sum — validates one element equals the sum of elements in child loops
  Extra fields: loop_id, source_segment, source_element,
                sum_segment, sum_element, sum_loop

cross_record_unique — validates no two records share the same element value
  Extra fields: segment_id, element_position
  Optional: condition {when_element, when_value}
```

### Rule Engine Implementation Order
Write and test in this order: required_segment → regex → enum → luhn →
cross_segment_sum → cross_record_unique. Each type is more complex than the last.
Do not write the next type until the previous type's tests pass.

### Rule Loading Pattern
```python
def _load_rules(self) -> list:
    rules = []
    # Always load common rules first (NPI, dates, ZIP)
    with open("rules/common.yaml") as f:
        rules.extend(yaml.safe_load(f).get("rules", []))
    # Then load transaction-type-specific rules
    type_map = {"837P": "837p_rules.yaml", ...}
    with open(f"rules/{type_map[self.transaction_type]}") as f:
        rules.extend(yaml.safe_load(f).get("rules", []))
    return rules
```

## MUST_NOT
- MUST_NOT hardcode validation logic as Python conditionals — all rules are YAML.
- MUST_NOT write a vague plain_english message — it must be actionable.
- MUST_NOT write cross_segment_sum rules before simpler types are working.
- MUST_NOT forget to handle the condition field — many rules only apply in context.

## Discovered During Implementation
""",
    "fastapi.skill.md": """# Skill: FastAPI Backend Patterns
## Purpose
Standard patterns for FastAPI routes, Pydantic models, and CORS setup.

## Key Knowledge

### App Setup Pattern
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ClearClaim API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev port — CRITICAL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### File Upload Pattern
```python
from fastapi import UploadFile, File
@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8", errors="replace")
    # ...process text...
    return result
```

### Pydantic Request Body Pattern
```python
from pydantic import BaseModel
class ChatRequest(BaseModel):
    question: str
    parsed_edi: ParsedEDI       # Pydantic model used directly as request body
    conversation_history: list
```

### Binary Response for Exports
```python
from fastapi.responses import Response
@router.post("/export/pdf")
async def export_pdf(req: ExportRequest):
    pdf_bytes = generate_pdf(req.parsed, req.validation)
    return Response(content=pdf_bytes, media_type="application/pdf")
```

## MUST_NOT
- MUST_NOT forget allow_origins includes http://localhost:5173 — missing this
  causes CORS errors that look like backend failures.
- MUST_NOT use synchronous file I/O in async routes — use aiofiles or run in executor.
- MUST_NOT return raw dicts — always return Pydantic models for type safety.

## Discovered During Implementation
""",
    "react.skill.md": """# Skill: React + TypeScript Frontend Patterns
## Purpose
Component patterns, Tailwind usage, and UI patterns for the ClearClaim frontend.

## Key Knowledge

### Mock Data Pattern (for development before backend is ready)
```typescript
// tests/mocks/mock_parsed_edi.ts
export const mockParsedEDI: ParsedEDI = {
  file_name: "test.edi",
  transaction_type: "837P",
  // ... minimal but complete mock matching the interface exactly
};
```
Always develop components against mock data first, then switch to API.

### Collapsible Tree Pattern (SegmentTree)
Use @uiw/react-json-view for the segment tree — it handles recursive
collapsible rendering out of the box. Pass parsed.loops as the data source.
Customise the theme to match Tailwind's slate colour palette.

### Colour Coding Pattern (EnrollmentSummary)
```typescript
const getRowClass = (maintenanceType: string) => {
  if (maintenanceType === "021") return "bg-green-50 border-green-200";
  if (maintenanceType === "024") return "bg-red-50 border-red-200";
  if (maintenanceType === "001") return "bg-yellow-50 border-yellow-200";
  return "bg-gray-50 border-gray-200";
};
```
The INS03 values are from SKILL-EDI-834 — "021"=Addition, "024"=Termination, "001"=Change.

### AI Chat Loading Pattern
```tsx
const [isThinking, setIsThinking] = useState(false);
const handleSend = async () => {
  setIsThinking(true);
  try {
    const response = await sendChatMessage(question, parsed, validation, history);
    // append response
  } catch {
    setError("The AI assistant is temporarily unavailable. Please try again.");
  } finally {
    setIsThinking(false);
  }
};
```

### Tab Navigation Pattern
Use a simple border-bottom approach for tabs — no external library needed.
The three tabs are "tree", "errors", and "summary". Auto-switch to "errors"
when validation.error_count > 0 after file upload.

## MUST_NOT
- MUST_NOT wait for the backend to build components — use mocks from day one.
- MUST_NOT build components in the wrong order — follow the build order in the
  Subagent C system prompt exactly.
- MUST_NOT style colour coding with hardcoded hex values — use Tailwind classes.
- MUST_NOT omit loading state on AIChatPanel — users must see the spinner.

## Discovered During Implementation
""",
    "markdown_context.skill.md": """# Skill: Markdown Context Schema for LLM
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
    return "\\n\\n---\\n\\n".join(sections)
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
""",
    "llm_chat.skill.md": """# Skill: Claude API Chat Integration
## Purpose
Patterns for calling the Anthropic Claude API, structuring system prompts,
and managing conversation history for the ClearClaim AI assistant.

## Key Knowledge

### Client Initialisation
```python
import anthropic, os
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```
Never hardcode the API key. Always read from environment variable.

### API Call Pattern
```python
response = client.messages.create(
    model="claude-sonnet-4-6",    # Always use this model
    max_tokens=1000,              # Sufficient for explanation responses
    system=system_prompt,         # Role + constraints
    messages=messages             # Conversation history list
)
return response.content[0].text
```

### First Message vs Subsequent Messages
First message (history is empty): prepend the full Markdown context document.
Subsequent messages: the context is already in history, just append the question.
```python
if not history:
    messages = [{"role": "user", "content":
        f"Here is the file analysis:\\n\\n{markdown_context}\\n\\nMy question: {question}"}]
else:
    messages = history + [{"role": "user", "content": question}]
```

### System Prompt Design
The system prompt must include these elements:
  1. Role definition ("You are an expert Medical Billing and EDI Consultant")
  2. Business goal ("Explain complex EDI transaction errors in plain, professional English for administrative staff")
  3. Analysis rules (Avoid repeating segment codes, explain business impact, provide 'Next Step')
  4. Data source constraint ("Only answer using the Markdown document provided")
  5. Citation rule ("Always cite Error N from Section 3 when referencing errors")
Never ask the LLM to recall EDI rules from memory — it must reason from the file.
## MUST_NOT
- MUST_NOT hardcode the API key — always use os.getenv("ANTHROPIC_API_KEY").
- MUST_NOT pass raw JSON as context — always use the Markdown from SKILL-MARKDOWN-CTX.
- MUST_NOT use a different model than claude-sonnet-4-6.
- MUST_NOT call the LLM for fix suggestions — that belongs in fix_suggester.py
  and must be rule-based only (see SKILL-EXPORT).

## Discovered During Implementation
""",
    "export.skill.md": """# Skill: Export System Patterns
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
    return "\\n".join(lines)
# After writing, parse the output and confirm same transaction_type and segment count.
```

## MUST_NOT
- MUST_NOT call the LLM for fix suggestions — all fixes are rule-based.
- MUST_NOT attempt to fix errors other than the three types listed above.
- MUST_NOT forget the round-trip test on the EDI writer.

## Discovered During Implementation
""",
    "testing.skill.md": """# Skill: Testing Patterns
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
""",
    "docker.skill.md": """# Skill: Docker Compose Deployment
## Purpose
Patterns for multi-service Docker Compose configuration and production deployment.

## Key Knowledge

### docker-compose.yml Pattern
```yaml
version: '3.8'
services:
  backend:
    build: ./clearclaim-backend
    ports: ["8000:8000"]
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}   # From .env file at root
    volumes:
      - ./clearclaim-backend:/app                # Hot reload during dev

  frontend:
    build: ./clearclaim-frontend
    ports: ["3000:3000"]
    environment:
      - VITE_API_URL=http://localhost:8000/api
    depends_on: [backend]
```

### Backend Dockerfile Pattern
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && pipenv install --system --deploy
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile Pattern
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
RUN npm install -g serve
CMD ["serve", "-s", "dist", "-l", "3000"]
```

### Production Deployment
Frontend → Vercel: add VITE_API_URL environment variable pointing to Render backend URL.
Backend → Render: add ANTHROPIC_API_KEY in Render dashboard environment variables.
Run `docker-compose up` locally to verify both services connect before deploying.

## MUST_NOT
- MUST_NOT commit .env files to Git — add to .gitignore before anything else.
- MUST_NOT hardcode ANTHROPIC_API_KEY in any Dockerfile or docker-compose.yml.
- MUST_NOT forget `depends_on: [backend]` — frontend starts before backend without it.

## Discovered During Implementation
"""
}

for filename, content in skills.items():
    with open(f"skills/{filename}", "w") as f:
        f.write(content)

print("Phase 0 Complete: Created skills directory and 14 skill files.")
