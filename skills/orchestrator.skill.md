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
