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
