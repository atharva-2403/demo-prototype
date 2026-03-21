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
