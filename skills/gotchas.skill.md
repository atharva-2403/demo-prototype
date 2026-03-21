# Skill: Gotchas and Learning Ledger
## Purpose
This file tracks testing failures, their root causes, and the correct implementation patterns discovered during active development. It acts as the agent's memory to avoid repeating mistakes.

## Rules
- Every time `pytest` fails, an entry MUST be added here BEFORE modifying the code to fix it.
- Each entry must include the Error, Root Cause, and Pattern.

## Ledger

**Error:** `test_delta_scenarios[old_data1-new_data1-1-0-0]` failed because `len(data["changes"]) == 1` instead of `0`.
**Root Cause:** The `extract_members` function in `routes/delta.py` extracts `raw_data` for comparison. However, the first loop 2000 in a file with multiple members might have a slightly different internal state or segment line number metadata, or the `create_834` test helper doesn't add `~` correctly, or maybe something else makes the strings mismatch. Let's look closer: `raw_data` strings are being concatenated from `s.raw_line`. In `old_edi`, M1 is the only member. In `new_edi`, M1 is followed by M2. Their `raw_data` should be identical for M1 unless line numbers or something else causes `s.raw_line` to differ? Wait, `s.raw_line` is just the string from `raw_segments`. It shouldn't differ... wait, maybe `parse_edi` includes the line number in the string? No, `s.raw_line` is the original string.
Wait, `raw_line` in the parser might include the trailing whitespace or delimiter? No, `get_segments` strips them.
Wait, is `raw_data` actually different? Let me debug.
**Pattern:** Always normalize or compare structured data rather than raw text, or ensure exact raw line text equivalence. I will investigate the exact mismatch.

*(New entries will be appended here during execution)*