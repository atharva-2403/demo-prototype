# ClearClaim — US Healthcare EDI Parser & X12 File Validator
## Complete Implementation Workflow & Task Plan
### Optimised for Gemini CLI Agent Execution with Skills Architecture

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [What Are Skills and Why They Matter](#what-are-skills-and-why-they-matter)
3. [Skills Registry](#skills-registry)
4. [Gemini CLI Agent Architecture](#gemini-cli-agent-architecture)
5. [Agent Execution Instructions](#agent-execution-instructions)
6. [Subagent Definitions](#subagent-definitions)
7. [Unfinished Work Tracker Protocol](#unfinished-work-tracker-protocol)
8. [Environment Setup](#environment-setup)
9. [Phase 0 — Skills Bootstrapping](#phase-0--skills-bootstrapping)
10. [Phase 1 — Project Scaffolding](#phase-1--project-scaffolding)
11. [Phase 2 — Core Parser Engine](#phase-2--core-parser-engine)
12. [Phase 3 — Validation Engine](#phase-3--validation-engine)
13. [Phase 4 — FastAPI Backend](#phase-4--fastapi-backend)
14. [Phase 5 — React Frontend](#phase-5--react-frontend)
15. [Phase 6 — AI Layer and Markdown Context System](#phase-6--ai-layer-and-markdown-context-system)
16. [Phase 7 — Specialized Views](#phase-7--specialized-views)
17. [Phase 8 — Export System](#phase-8--export-system)
18. [Phase 9 — Bonus Features](#phase-9--bonus-features)
19. [Phase 10 — Testing and QA](#phase-10--testing-and-qa)
20. [Phase 11 — Deployment](#phase-11--deployment)
21. [Task Checklist Master Sheet](#task-checklist-master-sheet)
22. [API Contract Reference](#api-contract-reference)
23. [Common Pitfalls and How to Avoid Them](#common-pitfalls-and-how-to-avoid-them)

---

## Project Overview

**ClearClaim** is a web-based EDI parsing and validation platform. It accepts X12 EDI files (837P, 837I, 835, 834), parses their full loop hierarchy, validates them against HIPAA 5010 rules, and uses an LLM to explain errors in plain English and suggest corrections.

**Core deliverable for judges:** Upload four files — valid 837P, malformed 837I (5+ errors), 835 remittance, 834 enrollment — and the system correctly identifies each, renders the parsed tree, lists all errors with explanations, displays specialized summaries, and the AI assistant answers at least 3 contextual questions.

**Critical architectural decisions:** All parsed EDI data passed to the LLM is converted from Python objects to a structured Markdown document before injection into the context window — never raw JSON. The `context_builder.py` module owns this conversion and is a first-class engineering component. Additionally, every agent and subagent operates with a dedicated Skill file that encodes its domain knowledge, constraints, and best practices — eliminating the need to re-derive these from scratch on every invocation.

---

## What Are Skills and Why They Matter

Before reading the rest of this document, it is worth understanding what a Skill is in this context and why the entire system is built around them.

Think of a Skill as a specialised knowledge card for a specific type of task. Just as a human surgeon doesn't need to re-read anatomy textbooks before every operation — they have internalised the knowledge — an agent Skill pre-loads the most important domain knowledge, rules, templates, and constraints for a given capability into a compact, reusable file that any agent or subagent can read at the start of a task.

Without Skills, every subagent invocation requires either including all relevant knowledge in the prompt (making prompts extremely long and expensive) or hoping the model derives the right approach from scratch (which introduces inconsistency). With Skills, each subagent reads one compact Markdown file at the start of its task, immediately has everything it needs, and produces consistent output across sessions.

In this project, Skills serve three purposes. They act as **domain knowledge stores** — encoding X12 EDI rules, HIPAA 5010 specifics, FastAPI patterns, React component patterns, and so on, so subagents don't have to rediscover them. They act as **quality gates** — each Skill contains a `MUST_NOT` section listing the most common mistakes for that domain, which the subagent reads before writing any code. And they act as **interface contracts** — Skills for shared components (like the Markdown context schema) ensure that every subagent that touches that component understands its exact specification.

Skills are stored in `clearclaim/skills/` as Markdown files. They are created during Phase 0 (Skills Bootstrapping) before any implementation begins. They are loaded by subagents at the start of each task by reading the relevant `.skill.md` file. They are updated whenever a subagent discovers a better approach, adds a new pattern, or encounters a new pitfall — making the system smarter with each session.

---

## Skills Registry

This is the master list of all Skills in the ClearClaim project. Every Skill has an ID, a path, an owner (the subagent responsible for creating and maintaining it), and a list of consumers (the subagents that load and use it). Skills are created during Phase 0 before any other work begins.

| Skill ID | File Path | Owner | Consumers | Purpose |
|---|---|---|---|---|
| `SKILL-ORCH` | `skills/orchestrator.skill.md` | Orchestrator | Orchestrator | Delegation patterns, parallelism rules, escalation protocol |
| `SKILL-EDI-CORE` | `skills/edi_core.skill.md` | Subagent A | A, B, D, E | X12 structure, delimiter bootstrapping, loop boundary rules |
| `SKILL-EDI-837` | `skills/edi_837.skill.md` | Subagent A | A, B | 837P and 837I loop grammar, required segments, CLM rules |
| `SKILL-EDI-835` | `skills/edi_835.skill.md` | Subagent A | A, B | 835 loop grammar, CLP structure, CAS/CARC codes |
| `SKILL-EDI-834` | `skills/edi_834.skill.md` | Subagent A | A, B | 834 loop grammar, INS segment, maintenance type codes |
| `SKILL-PARSER` | `skills/parser.skill.md` | Subagent A | A | State machine implementation pattern, edge case handling |
| `SKILL-VALIDATOR` | `skills/validator.skill.md` | Subagent B | B | YAML rule schema, rule engine patterns, check type catalogue |
| `SKILL-FASTAPI` | `skills/fastapi.skill.md` | Subagent B | B | FastAPI route patterns, Pydantic integration, CORS setup |
| `SKILL-REACT` | `skills/react.skill.md` | Subagent C | C | React component patterns, Tailwind usage, TypeScript interfaces |
| `SKILL-MARKDOWN-CTX` | `skills/markdown_context.skill.md` | Subagent D | D, E | Five-section Markdown schema, conversion rules, token budget |
| `SKILL-LLM-CHAT` | `skills/llm_chat.skill.md` | Subagent D | D | Claude API usage, system prompt design, conversation history |
| `SKILL-EXPORT` | `skills/export.skill.md` | Subagent D | D | PDF/CSV/EDI export patterns, ReportLab usage, EDI writer rules |
| `SKILL-TESTING` | `skills/testing.skill.md` | Subagent E | E, A, B, D | pytest patterns, EDI sample file construction, test coverage rules |
| `SKILL-DOCKER` | `skills/docker.skill.md` | Subagent D | D | Docker Compose patterns, multi-service networking, env var handling |

### How Subagents Load Skills

Every subagent system prompt includes a `SKILLS TO LOAD` block that lists which skills to read before starting work. The agent must read these files in order and apply their contents throughout the task. The loading instruction always follows this pattern:

```
SKILLS TO LOAD (read these files BEFORE writing any code):
1. Read skills/edi_core.skill.md — load X12 domain knowledge
2. Read skills/parser.skill.md — load state machine patterns
3. Read skills/testing.skill.md — load test writing patterns
Apply all MUST_NOT rules from each loaded skill throughout your work.
```

Skills are read using whatever file-reading tool Gemini CLI has available (`read_file`, `cat`, or equivalent). If a skill file does not yet exist (which cannot happen after Phase 0 completes), the subagent must halt and notify the Orchestrator rather than proceeding without it.

### How Skills Are Updated

When a subagent completes a task and discovers something not in the relevant Skill — a new pitfall, a better pattern, a constraint that saved time — it appends the finding to the Skill file under a `## Discovered During Implementation` section. This makes the skill richer for the next session or the next subagent that loads it. The Orchestrator adds a `Skill Update` entry to the session log in `ClearClaim_Unfinished_Work.md` whenever a skill is updated.

---

## Gemini CLI Agent Architecture

The system uses a **Primary Orchestrator Agent** that reads this document, maintains the task graph, and delegates to five **Specialised Subagents**. Each subagent owns a distinct domain and operates with its own set of Skills loaded at invocation time.

### Agent Hierarchy

```
PRIMARY ORCHESTRATOR AGENT
│  Skills loaded: SKILL-ORCH
│
├── SUBAGENT A: Parser Subagent
│   Skills loaded: SKILL-EDI-CORE, SKILL-EDI-837, SKILL-EDI-835,
│                  SKILL-EDI-834, SKILL-PARSER, SKILL-TESTING
│   Owns: parser/, loop_definitions/
│   Inputs: Raw EDI file content (string)
│   Outputs: ParsedEDI object
│
├── SUBAGENT B: Validation Subagent
│   Skills loaded: SKILL-EDI-CORE, SKILL-EDI-837, SKILL-EDI-835,
│                  SKILL-EDI-834, SKILL-VALIDATOR, SKILL-FASTAPI, SKILL-TESTING
│   Owns: validator/, rules/, routes/, main.py
│   Inputs: ParsedEDI from Subagent A
│   Outputs: ValidationResult object
│
├── SUBAGENT C: Frontend Subagent
│   Skills loaded: SKILL-REACT, SKILL-TESTING
│   Owns: clearclaim-frontend/src/
│   Inputs: TypeScript interfaces from Phase 1
│   Outputs: Running React UI at localhost:5173
│
├── SUBAGENT D: AI and Integration Subagent
│   Skills loaded: SKILL-MARKDOWN-CTX, SKILL-LLM-CHAT, SKILL-EXPORT,
│                  SKILL-DOCKER, SKILL-TESTING
│   Owns: ai/, export/, docker-compose.yml
│   Inputs: ParsedEDI + ValidationResult → Markdown (via SKILL-MARKDOWN-CTX)
│   Outputs: LLM responses, exported files, deployed application
│
└── SUBAGENT E: Testing Subagent
    Skills loaded: SKILL-EDI-CORE, SKILL-TESTING, SKILL-MARKDOWN-CTX
    Owns: tests/, sample_files/, ClearClaim_Unfinished_Work.md
    Inputs: Outputs from all four other subagents
    Outputs: Test results, tracker file, skill updates
```

### Parallelism Rules

Phase 0 (Skills Bootstrapping) and Phase 1 (Scaffolding) are strictly sequential and must complete before anything else. After Phase 1, Subagent A (parser), Subagent C (frontend with mocks), and the first half of Subagent D (context_builder, fix_suggester) can run in parallel. Subagent B cannot start Phase 3 until Phase 2 is complete. Subagent D cannot finish `chat.py` until Phase 3 is complete.

### Orchestrator System Prompt

```
You are the Orchestrator Agent for ClearClaim, a US Healthcare EDI Validator.

SKILLS TO LOAD (read before doing anything else):
1. Read skills/orchestrator.skill.md

Your responsibilities:
1. Read the Task Checklist Master Sheet to identify all unblocked tasks.
2. For each unblocked task, load the relevant subagent definition from this
   document, pass it the task number and the paths of its required Skills,
   and delegate.
3. Monitor Subagent outputs. If tests fail, allow one self-correction retry,
   then escalate to the user with the full error from ClearClaim_Unfinished_Work.md.
4. After each Subagent completes a task, update the Task Checklist in
   ClearClaim_Unfinished_Work.md and check if any new tasks become unblocked.
5. At the end of every session or when context reaches 80% capacity, invoke
   the Unfinished Work Tracker Protocol before stopping.
6. If any subagent reports a missing skill file, halt all work and alert the user.

Project: ClearClaim — US Healthcare X12 EDI Parser and Validator
Working directory: ./clearclaim/
Skills directory: ./clearclaim/skills/
Backend: Python 3.11 + FastAPI
Frontend: React 18 + TypeScript + Vite
LLM: Anthropic claude-sonnet-4-6
Core constraint: ALL parsed EDI data to the LLM must go through
parsed_edi_to_markdown() — never raw JSON. SKILL-MARKDOWN-CTX governs this.
```

---

## Agent Execution Instructions

**Step 1 — Run Phase 0 first, always.** Before any implementation, the Orchestrator runs Phase 0 (Skills Bootstrapping) to create all Skill files. No subagent should ever be invoked without its skill files existing. This is the most important step and must never be skipped even on resumption sessions.

**Step 2 — Read the full document.** The Orchestrator builds a mental dependency graph: Phase 0 → Phase 1 → (Phases 2, 5, 6-partial in parallel) → Phase 3 → Phase 4 → Phase 6-complete → Phases 7-8 → Phase 9 → Phase 10 → Phase 11.

**Step 3 — Create the unfinished work tracker.** At the very start of execution, Subagent E creates `ClearClaim_Unfinished_Work.md` from the template in the Unfinished Work Tracker Protocol section. This includes a `Skills Status` section tracking which skills have been created and which have been updated.

**Step 4 — Each Subagent reads its Skills before writing code.** When the Orchestrator delegates a task, it explicitly lists the skill files to load in the delegation message. The subagent must confirm it has read each skill before writing any code. This is not optional.

**Step 5 — Each Subagent writes its own files.** Subagents receive a scoped task, load their skills, write files, run tests, and report back. They do not ask the Orchestrator to write files.

**Step 6 — On test failure, retry once using the skill's MUST_NOT section.** The first thing a subagent should do on a test failure is re-read the relevant skill's `MUST_NOT` section — the failure is very likely caused by something listed there. If a second attempt still fails, write the error to the Blockers section and escalate.

**Step 7 — Update skills on new discoveries.** When a subagent finishes a task and learned something not in the skills, it appends the finding to the relevant skill file before reporting back to the Orchestrator.

**Step 8 — Final session cleanup.** After all executable tasks complete, the Orchestrator writes a final summary to `ClearClaim_Unfinished_Work.md` including the skill update log showing every skill that was modified and what was added.

---

## Subagent Definitions

Each definition includes the full system prompt AND the explicit list of skills to load. When the Orchestrator delegates a task, it passes the subagent system prompt together with the task number from this document.

### Subagent A — Parser Subagent

```
SUBAGENT A SYSTEM PROMPT:

You are the Parser Subagent for ClearClaim. Your responsibility is
implementing the X12 EDI state machine parser in Python from scratch.

SKILLS TO LOAD (read these files in order BEFORE writing any code):
1. Read skills/edi_core.skill.md      — X12 fundamentals, delimiter bootstrapping
2. Read skills/edi_837.skill.md       — 837P/837I loop grammar and required segments
3. Read skills/edi_835.skill.md       — 835 loop grammar and CLP structure
4. Read skills/edi_834.skill.md       — 834 loop grammar and INS segment rules
5. Read skills/parser.skill.md        — state machine implementation patterns
6. Read skills/testing.skill.md       — pytest patterns and test writing rules
Apply every MUST_NOT rule from each skill throughout your implementation.

Working directory: clearclaim-backend/parser/
Output contract: ParsedEDI objects as defined in parser/models.py
Downstream consumers: Subagent B (Validation) and Subagent D (AI Layer)

Core rules — these are enforced by your loaded skills:
- Never hardcode delimiter characters. SKILL-EDI-CORE explains why and how.
- Never crash on malformed files. SKILL-PARSER has the try/except pattern.
- Never use third-party EDI libraries. SKILL-PARSER explains why.
- Write loop definition YAMLs BEFORE state_machine.py. SKILL-EDI-837/835/834
  contain the loop grammar you need.
- Run tests after each file. SKILL-TESTING has the pytest invocation pattern.

After completing all tasks:
- Update any skills where you discovered a pattern or pitfall not already listed.
- Write a completion summary to your section in ClearClaim_Unfinished_Work.md.
```

### Subagent B — Validation Subagent

```
SUBAGENT B SYSTEM PROMPT:

You are the Validation Subagent for ClearClaim. Your responsibility is the
YAML-driven rule engine, all validation rule YAML files, and FastAPI routes.

SKILLS TO LOAD (read these files in order BEFORE writing any code):
1. Read skills/edi_core.skill.md      — X12 fundamentals and segment structure
2. Read skills/edi_837.skill.md       — 837 CLM rules, service line structure
3. Read skills/edi_835.skill.md       — 835 CAS/CARC code validation rules
4. Read skills/edi_834.skill.md       — 834 INS maintenance codes, duplicate rules
5. Read skills/validator.skill.md     — YAML rule schema, engine patterns
6. Read skills/fastapi.skill.md       — FastAPI route and Pydantic patterns
7. Read skills/testing.skill.md       — pytest patterns for rule engine testing
Apply every MUST_NOT rule from each skill throughout your implementation.

Working directory: clearclaim-backend/validator/ and clearclaim-backend/routes/
Input contract: ParsedEDI objects from Subagent A
Output contract: ValidationResult objects as defined in validator/models.py

Core rules enforced by your loaded skills:
- All validation rules are YAML data objects. SKILL-VALIDATOR has the schema.
- Every rule's plain_english field must be actionable. SKILL-VALIDATOR has examples.
- The malformed_837i.edi has exactly 6 errors — your engine must catch all 6.
  SKILL-EDI-837 lists each error type and which rule catches it.
- Cross-segment rules come last. SKILL-VALIDATOR explains the implementation order.

After completing all tasks, update skills with any new rule patterns discovered.
```

### Subagent C — Frontend Subagent

```
SUBAGENT C SYSTEM PROMPT:

You are the Frontend Subagent for ClearClaim. Your responsibility is
implementing the complete React + TypeScript user interface.

SKILLS TO LOAD (read these files in order BEFORE writing any code):
1. Read skills/react.skill.md         — component patterns, Tailwind, TypeScript
2. Read skills/testing.skill.md       — frontend testing patterns with mock data
Apply every MUST_NOT rule from each skill throughout your implementation.

Working directory: clearclaim-frontend/src/
Input contract: TypeScript interfaces in types/edi.ts
Output: Running React application at http://localhost:5173

Core rules enforced by your loaded skills:
- Use mock data from tests/mocks/ during development. SKILL-REACT has mock patterns.
- SegmentTree must be polished — judges interact with it directly. SKILL-REACT
  has the collapsible tree implementation pattern.
- Colour coding in EnrollmentSummary is defined in SKILL-REACT exactly:
  green = INS03 value "021", red = "024", yellow = "001".
- AIChatPanel loading and error states are defined in SKILL-REACT.
- Build order: FileUpload → MetadataBar → SegmentTree → ErrorDashboard →
  AIChatPanel → RemittanceSummary → EnrollmentSummary → ExportControls → ValidatorPage

After completing all tasks, update SKILL-REACT with any new component patterns.
```

### Subagent D — AI and Integration Subagent

```
SUBAGENT D SYSTEM PROMPT:

You are the AI and Integration Subagent for ClearClaim. Your responsibility is
the LLM integration, Markdown context builder, fix suggester, export system,
and Docker deployment.

SKILLS TO LOAD (read these files in order BEFORE writing any code):
1. Read skills/markdown_context.skill.md  — five-section schema, conversion rules
2. Read skills/llm_chat.skill.md          — Claude API patterns, system prompts
3. Read skills/export.skill.md            — PDF/CSV/EDI export patterns
4. Read skills/docker.skill.md            — Docker Compose, multi-service setup
5. Read skills/testing.skill.md           — pytest patterns for AI layer testing
Apply every MUST_NOT rule from each skill throughout your implementation.

Working directory: clearclaim-backend/ai/ and clearclaim-backend/export/

CRITICAL CONSTRAINT (enforced by SKILL-MARKDOWN-CTX):
ALL parsed EDI data sent to the LLM must be converted via parsed_edi_to_markdown().
Never pass raw JSON, Python dicts, or .json() output directly to the LLM.
The test test_no_raw_json_outside_code_blocks in test_context_builder.py
enforces this automatically — if it fails, re-read SKILL-MARKDOWN-CTX.

The Markdown document schema from SKILL-MARKDOWN-CTX:
  Section 1 — File Metadata (Markdown table)
  Section 2 — Validation Summary (Markdown table)
  Section 3 — Validation Errors (numbered subsections)
  Section 4 — Loop Structure (nested Markdown list)
  Section 5 — Key Segments (fenced code block, 20 segments max)

Fix suggestions in fix_suggester.py are rule-based only — never LLM calls.
SKILL-EXPORT has the deterministic fix patterns for each error type.

After completing all tasks, update all relevant skills with new patterns.
```

### Subagent E — Testing Subagent

```
SUBAGENT E SYSTEM PROMPT:

You are the Testing Subagent for ClearClaim. Your responsibilities are:
creating sample EDI test files, running all unit tests, and maintaining
ClearClaim_Unfinished_Work.md as the live progress tracker.

SKILLS TO LOAD (read these files in order BEFORE starting any work):
1. Read skills/edi_core.skill.md       — X12 structure for building test files
2. Read skills/testing.skill.md        — sample file construction, pytest patterns
3. Read skills/markdown_context.skill.md — for testing context_builder.py output
Apply every MUST_NOT rule from each skill throughout your work.

Working directory: clearclaim-backend/tests/

The four sample EDI files are your most critical output — create them during
Phase 1. SKILL-TESTING has the exact content template for each file type.

malformed_837i.edi must contain exactly these 6 errors (defined in SKILL-TESTING):
  1. Missing NM1 in Loop 2010AA (billing provider name loop)
  2. NPI 1234567890 — fails Luhn checksum
  3. CLM05-1 value "XX" — not a valid CMS facility code
  4. DTP03 as "01152023" — MMDDYYYY instead of CCYYMMDD
  5. CLM02 total mismatched from sum of SV1-02 amounts
  6. Missing CLM09 release of information code

Maintain ClearClaim_Unfinished_Work.md throughout execution. Include a
Skills Status section tracking which skills have been created and updated.
Update the tracker after every task completion, not just at session end.

The demo rehearsal in Phase 10 Task 10.4 is your responsibility.
```

---

## Unfinished Work Tracker Protocol

### When to Invoke

The Orchestrator invokes this at three times: at the natural end of a complete execution run, when context reaches approximately 80% capacity, or when a subagent reports an unresolvable blocker.

### Tracker File Template (`ClearClaim_Unfinished_Work.md`)

Subagent E creates this at the very start of execution. It contains seven sections — the six original ones plus a new Skills Status section.

```markdown
# ClearClaim — Unfinished Work Tracker
## Last Updated: [TIMESTAMP]
## Session Number: [N]

---

## Execution Summary
[Written at end of session — leave blank until then]

---

## Skills Status

### Skills Created (Phase 0)
- [ ] skills/orchestrator.skill.md
- [ ] skills/edi_core.skill.md
- [ ] skills/edi_837.skill.md
- [ ] skills/edi_835.skill.md
- [ ] skills/edi_834.skill.md
- [ ] skills/parser.skill.md
- [ ] skills/validator.skill.md
- [ ] skills/fastapi.skill.md
- [ ] skills/react.skill.md
- [ ] skills/markdown_context.skill.md
- [ ] skills/llm_chat.skill.md
- [ ] skills/export.skill.md
- [ ] skills/testing.skill.md
- [ ] skills/docker.skill.md

### Skills Updated This Session
[Populated as subagents discover and append new patterns]

---

## Completed Tasks This Session
[None yet — populated as tasks complete]

---

## Incomplete Tasks

### Phase 0 — Skills Bootstrapping
- [ ] Task 0.1 — Create skills/ directory and all 14 skill files

### Subagent A — Parser
- [ ] Task 2.1 — ISA Header Reader (parser/edi_reader.py)
- [ ] Task 2.2 — Loop Definition YAMLs (all 4 files)
- [ ] Task 2.3 — State Machine Parser (parser/state_machine.py)
- [ ] Task 2.4 — All 5 parser unit tests pass

### Subagent B — Validation and Backend
- [ ] Task 3.1 — YAML Rule Files (all 5 files)
- [ ] Task 3.2 — Rule Engine (validator/rule_engine.py — all 6 check methods)
- [ ] Task 4.1 — main.py FastAPI entry point
- [ ] Task 4.2 — routes/upload.py
- [ ] Task 4.3 — routes/validate.py
- [ ] Task 4.4 — routes/chat.py
- [ ] Task 4.5 — routes/fix.py and routes/export.py

### Subagent C — Frontend
- [ ] Task 5.1 — api/client.ts
- [ ] Task 5.2 — components/FileUpload.tsx
- [ ] Task 5.3 — components/MetadataBar.tsx
- [ ] Task 5.4 — components/SegmentTree.tsx
- [ ] Task 5.5 — components/ErrorDashboard.tsx
- [ ] Task 5.6 — components/AIChatPanel.tsx
- [ ] Task 5.7 — components/FixSuggestion.tsx
- [ ] Task 5.8 — pages/ValidatorPage.tsx

### Subagent D — AI and Integration
- [ ] Task 6.1 — ai/context_builder.py
- [ ] Task 6.1b — tests/test_context_builder.py (all 4 pass)
- [ ] Task 6.2 — ai/chat.py (Markdown context — never raw JSON)
- [ ] Task 6.3 — ai/fix_suggester.py (rule-based only)
- [ ] Task 8.1 — export/pdf_exporter.py
- [ ] Task 8.2 — export/edi_writer.py (round-trip tested)
- [ ] Task 8.3 — export/csv_exporter.py and json_exporter.py
- [ ] Task 11.1 — docker-compose.yml
- [ ] Task 11.2 — Both Dockerfiles

### Subagent E — Testing
- [ ] Task 1.3 — valid_837p.edi
- [ ] Task 1.3 — malformed_837i.edi (exactly 6 errors)
- [ ] Task 1.3 — sample_835.edi
- [ ] Task 1.3 — sample_834.edi
- [ ] Task 1.4 — tests/mocks/ files
- [ ] Task 10.1 — Parser tests pass (5/5)
- [ ] Task 10.2 — Validator tests pass (6/6 errors caught)
- [ ] Task 10.3 — Markdown context tests pass (4/4)
- [ ] Task 10.4 — Full demo rehearsal documented

### Bonus Features (lowest priority)
- [ ] Real NPI Validation
- [ ] Batch Processing
- [ ] 835-to-837 Reconciliation
- [ ] 834 Delta Report
- [ ] 834 Eligibility Cross-Check

---

## Blockers
None identified.

---

## Resumption Instructions
[Written at end of session — include which skills are confirmed good]

---

## Files Created This Session
[Populated at end of session]
```

---

## Environment Setup

### Prerequisites

```bash
python --version   # must be 3.11+
node --version     # must be 18+
pip install pipenv
# Docker Desktop from https://www.docker.com/products/docker-desktop
```

### Backend Setup

```bash
mkdir clearclaim-backend && cd clearclaim-backend
pipenv --python 3.11
pipenv install fastapi uvicorn pyyaml python-stdnum requests \
               reportlab anthropic python-multipart aiofiles \
               pytest httpx python-jose
pipenv shell
```

### Frontend Setup

```bash
npm create vite@latest clearclaim-frontend -- --template react-ts
cd clearclaim-frontend
npm install axios react-dropzone @uiw/react-json-view \
            recharts tailwindcss postcss autoprefixer @types/node
npx tailwindcss init -p
```

### Environment Variables (`.env` — never commit this)

```env
ANTHROPIC_API_KEY=your_key_here
NPPES_API_BASE=https://npiregistry.cms.hhs.gov/api/
ENVIRONMENT=development
```

---

## Phase 0 — Skills Bootstrapping

**Assigned to:** Orchestrator creates skill files directly
**Time estimate:** 30 minutes
**Must complete before:** Everything else — this is the unconditional first phase

This phase is new relative to a standard implementation plan. The Orchestrator creates the `clearclaim/skills/` directory and writes all 14 skill files before any other work begins. Think of this as writing the instruction manuals before handing tools to a team — the team is dramatically more effective when they have reference material to consult rather than relying on memory alone.

Each skill file follows a consistent structure: a Purpose section (what this skill is for), a Key Knowledge section (the compact domain knowledge the subagent needs), a Patterns section (reusable code or config templates), a MUST_NOT section (the most common mistakes for this domain), and a Discovered During Implementation section (initially empty, populated by subagents as they work).

### Task 0.1 — Create All Skill Files

The Orchestrator creates each file below in order. These are the full contents for each skill.

---

#### `skills/orchestrator.skill.md`

```markdown
# Skill: Orchestrator
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
[Populated by Orchestrator as sessions complete]
```

---

#### `skills/edi_core.skill.md`

```markdown
# Skill: X12 EDI Core
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
[Populated by subagents as they work]
```

---

#### `skills/edi_837.skill.md`

```markdown
# Skill: X12 837 — Medical Claims
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
[Populated by Subagent A and B as they work]
```

---

#### `skills/edi_835.skill.md`

```markdown
# Skill: X12 835 — Remittance Advice
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
[Populated by Subagent A and B as they work]
```

---

#### `skills/edi_834.skill.md`

```markdown
# Skill: X12 834 — Benefit Enrollment
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
[Populated by Subagent A and B as they work]
```

---

#### `skills/parser.skill.md`

```markdown
# Skill: X12 State Machine Parser
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
[Populated by Subagent A as they work]
```

---

#### `skills/validator.skill.md`

```markdown
# Skill: YAML-Driven Validation Engine
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
[Populated by Subagent B as they work]
```

---

#### `skills/fastapi.skill.md`

```markdown
# Skill: FastAPI Backend Patterns
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
[Populated by Subagent B as they work]
```

---

#### `skills/react.skill.md`

```markdown
# Skill: React + TypeScript Frontend Patterns
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
[Populated by Subagent C as they work]
```

---

#### `skills/markdown_context.skill.md`

```markdown
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
[Populated by Subagent D as they work]
```

---

#### `skills/llm_chat.skill.md`

```markdown
# Skill: Claude API Chat Integration
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
        f"Here is the file analysis:\n\n{markdown_context}\n\nMy question: {question}"}]
else:
    messages = history + [{"role": "user", "content": question}]
```

### System Prompt Design
The system prompt must include these three elements:
  1. Role definition ("You are ClearClaim AI, an expert EDI assistant")
  2. Data source constraint ("Only answer using the Markdown document provided")
  3. Citation rule ("Always cite Error N from Section 3 when referencing errors")
Never ask the LLM to recall EDI rules from memory — it must reason from the file.

## MUST_NOT
- MUST_NOT hardcode the API key — always use os.getenv("ANTHROPIC_API_KEY").
- MUST_NOT pass raw JSON as context — always use the Markdown from SKILL-MARKDOWN-CTX.
- MUST_NOT use a different model than claude-sonnet-4-6.
- MUST_NOT call the LLM for fix suggestions — that belongs in fix_suggester.py
  and must be rule-based only (see SKILL-EXPORT).

## Discovered During Implementation
[Populated by Subagent D as they work]
```

---

#### `skills/export.skill.md`

```markdown
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
[Populated by Subagent D as they work]
```

---

#### `skills/testing.skill.md`

```markdown
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
[Populated by Subagent E as they work]
```

---

#### `skills/docker.skill.md`

```markdown
# Skill: Docker Compose Deployment
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
[Populated by Subagent D as they work]
```

---

## Phase 1 — Project Scaffolding

**Assigned to:** Orchestrator coordinates Subagents B, C, and E simultaneously
**Time estimate:** 2 hours
**Precondition:** Phase 0 complete — all 14 skill files must exist before this phase begins

### Task 1.1 — Create Full Folder Structure

Subagent B creates this structure and pushes to GitHub. All other Subagents pull before starting.

```
clearclaim/
├── skills/                            # All 14 skill files (created in Phase 0)
│   ├── orchestrator.skill.md
│   ├── edi_core.skill.md
│   ├── edi_837.skill.md
│   ├── edi_835.skill.md
│   ├── edi_834.skill.md
│   ├── parser.skill.md
│   ├── validator.skill.md
│   ├── fastapi.skill.md
│   ├── react.skill.md
│   ├── markdown_context.skill.md
│   ├── llm_chat.skill.md
│   ├── export.skill.md
│   ├── testing.skill.md
│   └── docker.skill.md
│
├── clearclaim-backend/
│   ├── main.py
│   ├── .env                           # gitignored
│   ├── Pipfile
│   ├── Dockerfile
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── edi_reader.py
│   │   ├── state_machine.py
│   │   ├── loop_definitions/
│   │   │   ├── 837p_loops.yaml
│   │   │   ├── 837i_loops.yaml
│   │   │   ├── 835_loops.yaml
│   │   │   └── 834_loops.yaml
│   │   └── models.py
│   ├── validator/
│   │   ├── __init__.py
│   │   ├── rule_engine.py
│   │   ├── rules/
│   │   │   ├── common.yaml
│   │   │   ├── 837p_rules.yaml
│   │   │   ├── 837i_rules.yaml
│   │   │   ├── 835_rules.yaml
│   │   │   └── 834_rules.yaml
│   │   └── models.py
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── context_builder.py
│   │   ├── chat.py
│   │   └── fix_suggester.py
│   ├── export/
│   │   ├── __init__.py
│   │   ├── pdf_exporter.py
│   │   ├── csv_exporter.py
│   │   ├── json_exporter.py
│   │   └── edi_writer.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── upload.py
│   │   ├── validate.py
│   │   ├── chat.py
│   │   ├── fix.py
│   │   └── export.py
│   ├── tests/
│   │   ├── sample_files/
│   │   │   ├── valid_837p.edi
│   │   │   ├── malformed_837i.edi
│   │   │   ├── sample_835.edi
│   │   │   └── sample_834.edi
│   │   ├── mocks/
│   │   │   ├── mock_parsed_edi.py
│   │   │   └── mock_validation.py
│   │   ├── test_parser.py
│   │   ├── test_validator.py
│   │   ├── test_context_builder.py
│   │   └── test_api.py
│   └── docker-compose.yml
│
└── clearclaim-frontend/
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx
    │   ├── api/
    │   │   └── client.ts
    │   ├── components/
    │   │   ├── FileUpload.tsx
    │   │   ├── SegmentTree.tsx
    │   │   ├── ErrorDashboard.tsx
    │   │   ├── AIChatPanel.tsx
    │   │   ├── FixSuggestion.tsx
    │   │   ├── RemittanceSummary.tsx
    │   │   ├── EnrollmentSummary.tsx
    │   │   ├── ExportControls.tsx
    │   │   └── MetadataBar.tsx
    │   ├── pages/
    │   │   └── ValidatorPage.tsx
    │   ├── types/
    │   │   └── edi.ts
    │   └── styles/
    │       └── index.css
    ├── Dockerfile
    └── vite.config.ts
```

### Task 1.2 — Define Shared Data Models

Subagent B writes Python Pydantic models (`parser/models.py`, `validator/models.py`). Subagent C writes the TypeScript mirrors (`types/edi.ts`). These are the contracts all other Subagents build against — no changes without notifying all other Subagents.

```python
# parser/models.py
from pydantic import BaseModel
from typing import List, Optional

class EDIElement(BaseModel):
    position: int       # 1-indexed position within segment
    label: str          # Human-readable label (used in Markdown context and UI)
    value: str          # Raw string value from file
    raw_key: str        # e.g. "CLM_02" or "CLM_05_01" for subelements

class EDISegment(BaseModel):
    id: str             # Segment identifier e.g. "CLM", "NM1"
    loop_id: str        # Assigned by state machine e.g. "2300"
    elements: List[EDIElement]
    raw_line: str       # Original unparsed line
    line_number: int    # 1-indexed position in file (used in error reporting)

class EDILoop(BaseModel):
    loop_id: str
    loop_name: str      # Human-readable name from loop definition YAML
    segments: List[EDISegment]
    children: List['EDILoop']

class ParsedEDI(BaseModel):
    file_name: str
    transaction_type: str   # "837P", "837I", "835", "834"
    sender_id: str
    receiver_id: str
    interchange_date: str
    transaction_set_count: int
    delimiter_segment: str
    delimiter_element: str
    delimiter_subelement: str
    loops: List[EDILoop]
    raw_segments: List[EDISegment]
```

```python
# validator/models.py
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class ValidationError(BaseModel):
    error_code: str
    severity: Severity
    loop_id: str
    segment_id: str
    element_position: int
    raw_value: Optional[str]
    expected: Optional[str]
    plain_english: str
    line_number: int
    auto_fix_available: bool
    suggested_fix: Optional[str]

class ValidationResult(BaseModel):
    transaction_type: str
    is_valid: bool
    error_count: int
    warning_count: int
    errors: List[ValidationError]
```

```typescript
// types/edi.ts — exact TypeScript mirror of Python models
export interface EDIElement {
  position: number; label: string; value: string; raw_key: string;
}
export interface EDISegment {
  id: string; loop_id: string; elements: EDIElement[];
  raw_line: string; line_number: number;
}
export interface EDILoop {
  loop_id: string; loop_name: string;
  segments: EDISegment[]; children: EDILoop[];
}
export interface ParsedEDI {
  file_name: string; transaction_type: string;
  sender_id: string; receiver_id: string;
  interchange_date: string; transaction_set_count: number;
  loops: EDILoop[]; raw_segments: EDISegment[];
}
export interface ValidationError {
  error_code: string; severity: 'error' | 'warning' | 'info';
  loop_id: string; segment_id: string; element_position: number;
  raw_value?: string; expected?: string; plain_english: string;
  line_number: number; auto_fix_available: boolean; suggested_fix?: string;
}
export interface ValidationResult {
  transaction_type: string; is_valid: boolean;
  error_count: number; warning_count: number;
  errors: ValidationError[];
}
```

### Task 1.3 — Create Sample EDI Test Files

**Assigned to Subagent E.** Subagent E reads `skills/testing.skill.md` and `skills/edi_core.skill.md` first, then constructs all four files per the exact specifications in SKILL-TESTING. The malformed 837I must contain exactly the 6 errors listed in SKILL-EDI-837 — no more, no fewer.

### Task 1.4 — Create Mock Data Files

**Assigned to Subagent E.** Reads `skills/testing.skill.md` and creates `tests/mocks/mock_parsed_edi.py` and `tests/mocks/mock_validation.py` using the mock object pattern from that skill.

---

## Phase 2 — Core Parser Engine

**Assigned to: Subagent A**
**Skills to load:** SKILL-EDI-CORE, SKILL-EDI-837, SKILL-EDI-835, SKILL-EDI-834, SKILL-PARSER, SKILL-TESTING
**Time estimate:** 6-8 hours | **Dependency:** Phase 1 complete

### Task 2.1 — ISA Header Reader (`parser/edi_reader.py`)

Subagent A reads SKILL-EDI-CORE (bootstrapping problem section) and SKILL-PARSER (error resilience pattern) before implementing this file. The bootstrapping logic is explained in detail in those skills and must not be reimplemented from scratch — follow the skill patterns exactly.

```python
# parser/edi_reader.py
# See SKILL-EDI-CORE for the bootstrapping explanation.
# See SKILL-PARSER for the error resilience pattern.

class EDIReader:
    def __init__(self, raw_content: str):
        self.raw_content = raw_content
        self.element_delimiter = None
        self.segment_terminator = None
        self.subelement_delimiter = None

    def bootstrap(self) -> bool:
        if not self.raw_content.startswith("ISA"):
            raise ValueError("File does not begin with ISA — not a valid X12 file")
        # ISA is always 106 chars. Position 3 = element delimiter.
        self.element_delimiter = self.raw_content[3]
        isa_elements = self.raw_content[:106].split(self.element_delimiter)
        self.subelement_delimiter = isa_elements[16][0]
        isa_end = self.raw_content.find(self.element_delimiter + isa_elements[16])
        self.segment_terminator = self.raw_content[
            isa_end + len(self.element_delimiter) + len(isa_elements[16])]
        return True

    def get_segments(self) -> list[str]:
        self.bootstrap()
        return [s.strip() for s in self.raw_content.split(self.segment_terminator) if s.strip()]

    def detect_transaction_type(self, segments: list[str]) -> str:
        # See SKILL-EDI-CORE Transaction Type Detection section
        for seg in segments:
            els = seg.split(self.element_delimiter)
            if els[0] == "GS":
                if els[1] == "HP": return "835"
                if els[1] == "BE": return "834"
            if els[0] == "ST":
                if els[1] in ("837", "835", "834"): return els[1]
        raise ValueError("Cannot detect transaction type")
```

### Task 2.2 — Loop Definition YAMLs

Subagent A reads SKILL-EDI-837, SKILL-EDI-835, and SKILL-EDI-834 to get the complete loop grammar for each transaction type. Each skill's Key Knowledge section contains the critical loop IDs, opening segment IDs, and qualifier values needed to write these files. The YAML schema to follow is defined in SKILL-PARSER.

### Task 2.3 — State Machine Parser (`parser/state_machine.py`)

Subagent A reads SKILL-PARSER (state machine pattern and subelement handling) before implementing. The state machine pattern, transition logic, and error resilience pattern are all in that skill.

### Task 2.4 — Parser Unit Tests

Subagent A reads SKILL-TESTING (pytest invocation and sample file notes) and writes all five tests. Test construction follows the pattern in that skill. All five must pass before Subagent A reports completion.

---

## Phase 3 — Validation Engine

**Assigned to: Subagent B**
**Skills to load:** SKILL-EDI-CORE, SKILL-EDI-837, SKILL-EDI-835, SKILL-EDI-834, SKILL-VALIDATOR, SKILL-FASTAPI, SKILL-TESTING
**Time estimate:** 6-8 hours | **Dependency:** Phase 2 complete

### Task 3.1 — YAML Rule Files

Subagent B reads SKILL-VALIDATOR (rule schema and check type catalogue) and the three transaction-specific EDI skills to understand what each rule must validate. The six errors in malformed_837i.edi are listed in SKILL-EDI-837 with their corresponding rule types — use that list to ensure complete coverage.

Every rule's `plain_english` field must follow the template in SKILL-VALIDATOR: actionable, specific, with `{raw_value}` placeholder. "Invalid value" is not acceptable.

### Task 3.2 — Rule Engine (`validator/rule_engine.py`)

Subagent B follows the implementation order from SKILL-VALIDATOR: `required_segment` → `regex` → `enum` → `luhn` → `cross_segment_sum` → `cross_record_unique`. Do not implement the next type until the previous type's tests pass.

### Tasks 4.1-4.5 — FastAPI Routes

Subagent B reads SKILL-FASTAPI before writing any route files. The app setup pattern, file upload pattern, Pydantic request body pattern, and CORS configuration are all in that skill. The `allow_origins` must include `http://localhost:5173` — this is in the SKILL-FASTAPI MUST_NOT section.

---

## Phase 4 — FastAPI Backend

This phase is owned by Subagent B and completes the route layer after the validation engine is working. See Subagent B system prompt for skill loading instructions. The implementation code is defined in Tasks 4.1-4.5 following the SKILL-FASTAPI patterns.

---

## Phase 5 — React Frontend

**Assigned to: Subagent C**
**Skills to load:** SKILL-REACT, SKILL-TESTING
**Time estimate:** 6-8 hours | **Dependency:** Phase 1 complete (runs in parallel with Phases 2-4)

Subagent C reads both skills before writing any component. SKILL-REACT contains the mock data pattern, collapsible tree pattern, colour coding values (from SKILL-EDI-834 incorporated into SKILL-REACT), loading state pattern, and tab navigation pattern. Every component is built against mock data first — the API is connected only after each component is independently verified.

The component build order from SKILL-REACT must be followed exactly: FileUpload → MetadataBar → SegmentTree → ErrorDashboard → AIChatPanel → RemittanceSummary → EnrollmentSummary → ExportControls → ValidatorPage.

The full component implementations (FileUpload.tsx, ValidatorPage.tsx, and api/client.ts) are the same as in the previous version of this document — refer to them as reference implementations, but adapt according to any updated patterns discovered in the skill files.

---

## Phase 6 — AI Layer and Markdown Context System

**Assigned to: Subagent D**
**Skills to load:** SKILL-MARKDOWN-CTX, SKILL-LLM-CHAT, SKILL-EXPORT, SKILL-DOCKER, SKILL-TESTING
**Time estimate:** 4-5 hours | **Dependency:** Phase 1 complete (context_builder and fix_suggester); Phase 3 complete (chat.py)

The most important principle governing this entire phase is encoded in SKILL-MARKDOWN-CTX: all parsed EDI data passes through `parsed_edi_to_markdown()` before reaching the LLM. The test `test_no_raw_json_outside_code_blocks` in `test_context_builder.py` enforces this mechanically.

### Task 6.1 — Markdown Context Builder (`ai/context_builder.py`)

Subagent D reads SKILL-MARKDOWN-CTX first. That skill defines the exact five-section schema, the Section 3 error subsection format, the Section 5 segment line format, the token budget rules (20 errors max, 20 segments max), and the master conversion function signature. Implement each section builder function following those templates exactly.

After completing context_builder.py, run `pytest tests/test_context_builder.py -v` and confirm all four tests pass before writing chat.py.

### Task 6.2 — AI Chat Assistant (`ai/chat.py`)

Subagent D reads SKILL-LLM-CHAT. That skill has the client initialisation pattern, the first-message vs subsequent-message pattern, and the system prompt design requirements. The markdown_context variable must come from `parsed_edi_to_markdown()` — never from `.json()` or `.dict()`.

### Task 6.3 — Fix Suggester (`ai/fix_suggester.py`)

Subagent D reads SKILL-EXPORT (deterministic fix patterns section). The three fixable error types (`INVALID_DATE_FORMAT`, `INVALID_ZIP`, `CLM_AMOUNT_MISMATCH`) and their fix logic are defined in that skill. No LLM calls are made here.

---

## Phase 7 — Specialized Views

**Assigned to: Subagent C**
**Skills to load:** SKILL-REACT, SKILL-EDI-835 (for RemittanceSummary), SKILL-EDI-834 (for EnrollmentSummary)
**Time estimate:** 3-4 hours | **Dependency:** Phase 5 complete

For RemittanceSummary, Subagent C reads SKILL-EDI-835 to understand CLP loop structure and CAS adjustment codes. For EnrollmentSummary, Subagent C reads SKILL-EDI-834 to confirm INS03 maintenance type codes and the exact colour mapping (defined in that skill's Colour Coding section).

---

## Phase 8 — Export System

**Assigned to: Subagent D**
**Skills to load:** SKILL-EXPORT
**Time estimate:** 3 hours | **Dependency:** Phase 4 complete

Subagent D reads SKILL-EXPORT before starting. That skill has the ReportLab PDF pattern, the EDI writer round-trip pattern, and the CSV export notes. The round-trip test for the EDI writer is mandatory — parse the output file and confirm it matches the original's transaction type and segment count.

---

## Phase 9 — Bonus Features

**Assigned to: Subagent D with Subagent B support**
**Skills to load:** Subagent D loads SKILL-EDI-835, SKILL-EDI-834. Subagent B loads SKILL-VALIDATOR.
**Time estimate:** 4-6 hours | **Dependency:** Phases 1-8 complete

Implement in priority order. Stop when time runs out and log remaining features in `ClearClaim_Unfinished_Work.md`. Each feature is independent.

**Priority 1 — Real NPI Validation.** After Luhn passes, GET `https://npiregistry.cms.hhs.gov/api/?number={npi}&version=2.1`. No result = `NPI_NOT_FOUND` error. Name mismatch between API response and NM1_03 = `NPI_NAME_MISMATCH` warning.

**Priority 2 — Batch Processing.** `/api/batch-upload` accepts ZIP. Extract with Python `zipfile`, run each file through the single-file pipeline, return consolidated report: total files, files with errors, top 5 error codes across all files.

**Priority 3 — 835-to-837 Reconciliation.** `/api/reconcile` accepts two files. Join CLM01 to CLP01. Return billed vs paid comparison. Subagent D reads SKILL-EDI-835 (835-to-837 reconciliation section) for the join logic.

**Priority 4 — 834 Delta Report.** `/api/delta` accepts two 834 files. Compare member dicts keyed by subscriber ID (REF qualifier "0F"). Categorise as Added, Terminated, Changed, Unchanged.

**Priority 5 — 834 Eligibility Cross-Check.** `/api/eligibility-check` accepts one 834 and one 837. Cross-check claim service dates against member coverage windows from the 834. Flag `INELIGIBLE_SERVICE_DATE` when outside coverage window.

---

## Phase 10 — Testing and QA

**Assigned to: Subagent E**
**Skills to load:** SKILL-TESTING, SKILL-MARKDOWN-CTX, SKILL-EDI-CORE
**Time estimate:** 3-4 hours

### Task 10.1 — Parser Unit Tests

`pytest tests/test_parser.py -v` — all 5 must pass.

### Task 10.2 — Validator Unit Tests

`pytest tests/test_validator.py -v` — all 6 errors in malformed_837i.edi must be caught. Subagent E cross-references SKILL-EDI-837 (The 6 Deliberate Errors section) to verify each error type has a corresponding test assertion.

### Task 10.3 — Markdown Context Builder Tests

`pytest tests/test_context_builder.py -v` — all 4 must pass including `test_no_raw_json_outside_code_blocks`.

### Task 10.4 — End-to-End Demo Rehearsal

Run through the exact judge scenario. Upload valid_837p.edi → zero errors, tree renders. Upload malformed_837i.edi → all 6 errors with plain-English descriptions. Upload sample_835.edi → Remittance Summary shows payment breakdown. Upload sample_834.edi → Enrollment Summary shows colour-coded rows. Then test AI with these three questions on the 837I: "Why was this claim rejected?", "What does CLM_AMOUNT_MISMATCH mean and how do I fix it?", "Which line number has the invalid NPI?". Document every result in `ClearClaim_Unfinished_Work.md`.

---

## Phase 11 — Deployment

**Assigned to: Subagent D**
**Skills to load:** SKILL-DOCKER
**Time estimate:** 2 hours

Subagent D reads SKILL-DOCKER before writing any Docker files. That skill has the complete docker-compose.yml pattern, both Dockerfiles, and the production deployment steps for Vercel and Render. The MUST_NOT section in that skill covers the most common deployment mistakes.

---

## Task Checklist Master Sheet

Subagent E maintains this as the live state in `ClearClaim_Unfinished_Work.md`.

### Phase 0 — Skills Bootstrapping (Orchestrator)
- [ ] Task 0.1 — All 14 skill files created in clearclaim/skills/

### Subagent A — Parser
- [ ] Task 2.1 — parser/edi_reader.py (skills loaded: EDI-CORE, PARSER)
- [ ] Task 2.2 — parser/loop_definitions/*.yaml — all 4 files (skills: EDI-837, EDI-835, EDI-834, PARSER)
- [ ] Task 2.3 — parser/state_machine.py (skills: EDI-CORE, PARSER, TESTING)
- [ ] Task 2.4 — All 5 parser unit tests pass

### Subagent B — Validation and Backend
- [ ] Task 1.1 — Full folder structure created and pushed
- [ ] Task 1.2 — parser/models.py and validator/models.py
- [ ] Task 3.1 — validator/rules/*.yaml all 5 files (skills: VALIDATOR, EDI-837, EDI-835, EDI-834)
- [ ] Task 3.2 — validator/rule_engine.py all 6 check methods (skill: VALIDATOR)
- [ ] Task 4.1 — main.py FastAPI entry point (skill: FASTAPI)
- [ ] Task 4.2 — routes/upload.py (skill: FASTAPI)
- [ ] Task 4.3 — routes/validate.py (skill: FASTAPI)
- [ ] Task 4.4 — routes/chat.py (skill: FASTAPI)
- [ ] Task 4.5 — routes/fix.py and routes/export.py (skill: FASTAPI)
- [ ] All 6 validator unit tests pass (6/6 errors caught)

### Subagent C — Frontend
- [ ] Task 1.2 — types/edi.ts TypeScript interfaces
- [ ] Task 5.1 — api/client.ts (skill: REACT)
- [ ] Task 5.2 — components/FileUpload.tsx (skill: REACT)
- [ ] Task 5.3 — components/MetadataBar.tsx (skill: REACT)
- [ ] Task 5.4 — components/SegmentTree.tsx (skill: REACT)
- [ ] Task 5.5 — components/ErrorDashboard.tsx (skill: REACT)
- [ ] Task 5.6 — components/AIChatPanel.tsx (skill: REACT)
- [ ] Task 5.7 — components/FixSuggestion.tsx (skill: REACT)
- [ ] Task 7.1 — components/RemittanceSummary.tsx (skills: REACT, EDI-835)
- [ ] Task 7.2 — components/EnrollmentSummary.tsx (skills: REACT, EDI-834)
- [ ] Task 5.x — components/ExportControls.tsx (skill: REACT)
- [ ] Task 5.8 — pages/ValidatorPage.tsx (skill: REACT)

### Subagent D — AI and Integration
- [ ] Task 6.1 — ai/context_builder.py (skill: MARKDOWN-CTX)
- [ ] Task 6.1b — tests/test_context_builder.py all 4 pass (skills: MARKDOWN-CTX, TESTING)
- [ ] Task 6.2 — ai/chat.py — Markdown only, never JSON (skills: MARKDOWN-CTX, LLM-CHAT)
- [ ] Task 6.3 — ai/fix_suggester.py — rule-based only (skill: EXPORT)
- [ ] Task 8.1 — export/pdf_exporter.py (skill: EXPORT)
- [ ] Task 8.2 — export/edi_writer.py round-trip tested (skill: EXPORT)
- [ ] Task 8.3 — export/csv_exporter.py and json_exporter.py (skill: EXPORT)
- [ ] Task 11.1 — docker-compose.yml (skill: DOCKER)
- [ ] Task 11.2 — Both Dockerfiles (skill: DOCKER)
- [ ] Task 11.3 — Deployed to Vercel + Render (skill: DOCKER)
- [ ] Bonus: Real NPI Validation
- [ ] Bonus: Batch Processing
- [ ] Bonus: 835-to-837 Reconciliation

### Subagent E — Testing
- [ ] Task 1.3 — valid_837p.edi (skill: TESTING + EDI-CORE)
- [ ] Task 1.3 — malformed_837i.edi — exactly 6 errors (skill: TESTING + EDI-837)
- [ ] Task 1.3 — sample_835.edi (skill: TESTING + EDI-835)
- [ ] Task 1.3 — sample_834.edi (skill: TESTING + EDI-834)
- [ ] Task 1.4 — tests/mocks/*.py (skill: TESTING)
- [ ] Task 10.1 — Parser tests pass 5/5
- [ ] Task 10.2 — Validator tests pass 6/6
- [ ] Task 10.3 — Markdown context tests pass 4/4
- [ ] Task 10.4 — Full demo rehearsal documented
- [ ] ClearClaim_Unfinished_Work.md maintained and current throughout

---

## API Contract Reference

| Method | Endpoint | Request | Response |
|--------|----------|---------|----------|
| POST | /api/upload | multipart/form-data (file) | ParsedEDI |
| POST | /api/validate | ParsedEDI | ValidationResult |
| POST | /api/chat | ChatRequest | {response: string} |
| POST | /api/fix | {error, parsed, fix_value} | Updated ParsedEDI |
| POST | /api/export/json | {parsed, validation} | JSON blob |
| POST | /api/export/pdf | {parsed, validation} | PDF blob |
| POST | /api/export/csv | {parsed} | CSV blob |
| POST | /api/export/edi | {parsed} | EDI text blob |
| POST | /api/batch-upload | ZIP file | ConsolidatedReport |
| POST | /api/reconcile | {file_837, file_835} | ReconciliationReport |
| POST | /api/delta | {file_834_old, file_834_new} | DeltaReport |
| POST | /api/eligibility-check | {file_834, file_837} | EligibilityReport |

---

## Common Pitfalls and How to Avoid Them

Each pitfall below is already encoded in the relevant skill's MUST_NOT section. If a subagent follows the skill loading discipline, these pitfalls should never occur. They are listed here as a final cross-check.

**Pitfall 1 — Hardcoded delimiters.** Covered in SKILL-EDI-CORE MUST_NOT. The Orchestrator verifies by checking edi_reader.py reads delimiters from ISA position 3 before marking Task 2.1 complete.

**Pitfall 2 — Crashing on malformed files.** Covered in SKILL-PARSER MUST_NOT (error resilience pattern). The test `test_malformed_837i_does_not_crash` enforces this.

**Pitfall 3 — Sending raw JSON to the LLM.** Covered in SKILL-MARKDOWN-CTX MUST_NOT and enforced by `test_no_raw_json_outside_code_blocks`. If this test fails, the subagent must re-read SKILL-MARKDOWN-CTX before attempting a fix.

**Pitfall 4 — Missing errors in the malformed 837I.** Covered in SKILL-EDI-837 (The 6 Deliberate Errors section). Subagent E cross-references this list during Task 10.2.

**Pitfall 5 — Using 837P loop grammar for 837I.** Covered in SKILL-EDI-837 MUST_NOT. Two separate loop definition YAML files are required.

**Pitfall 6 — CORS misconfiguration.** Covered in SKILL-FASTAPI MUST_NOT. The `allow_origins` must include `http://localhost:5173`.

**Pitfall 7 — Missing subelement handling.** Covered in SKILL-PARSER (subelement delimiter handling section) and SKILL-EDI-837 MUST_NOT (CLM05 composite element note).

**Pitfall 8 — LLM context overflow.** Covered in SKILL-MARKDOWN-CTX (token budget rules). Both errors and segments are capped at 20, with overflow notes included in the Markdown output.

**Pitfall 9 — Stale tracker file.** Covered in Subagent E system prompt and SKILL-TESTING. The tracker must be updated after every task completion, not just at session end.

**Pitfall 10 — Skipping Phase 0.** If skills don't exist when subagents start, they have no reference material and will produce inconsistent output. The Orchestrator system prompt makes Phase 0 the unconditional first step, and the Orchestrator halts if a subagent reports a missing skill file.

---

*This document is the single source of truth for ClearClaim implementation. The Skills Registry governs which skills each subagent loads. The Task Checklist Master Sheet is mirrored live in `ClearClaim_Unfinished_Work.md`. The API Contract must stay in sync with actual implementation. Skills are updated continuously as subagents discover new patterns and pitfalls.*
