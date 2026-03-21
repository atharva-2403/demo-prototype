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
