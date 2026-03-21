import yaml
import os
import re
from stdnum import luhn
from parser.models import ParsedEDI
from validator.models import ValidationResult, ValidationError, Severity

class RuleEngine:
    def __init__(self, transaction_type: str):
        self.transaction_type = transaction_type
        self.rules = self._load_rules()

    def _load_rules(self) -> list:
        rules = []
        base_dir = os.path.dirname(__file__)
        common_path = os.path.join(base_dir, "rules", "common.yaml")
        if os.path.exists(common_path):
            with open(common_path) as f:
                rules.extend(yaml.safe_load(f).get("rules", []))
        
        type_map = {
            "837P": "837p_rules.yaml",
            "837I": "837i_rules.yaml",
            "835": "835_rules.yaml",
            "834": "834_rules.yaml"
        }
        spec_path = os.path.join(base_dir, "rules", type_map.get(self.transaction_type, "837p_rules.yaml"))
        if os.path.exists(spec_path):
            with open(spec_path) as f:
                rules.extend(yaml.safe_load(f).get("rules", []))
        return rules

    def validate(self, parsed: ParsedEDI) -> ValidationResult:
        errors = []
        
        for rule in self.rules:
            if self.transaction_type not in rule.get("applies_to_types", []):
                continue
                
            check_type = rule["check_type"]
            if check_type == "required_segment":
                errors.extend(self._check_required_segment(rule, parsed))
            elif check_type == "regex":
                errors.extend(self._check_regex(rule, parsed))
            elif check_type == "enum":
                errors.extend(self._check_enum(rule, parsed))
            elif check_type == "luhn":
                errors.extend(self._check_luhn(rule, parsed))
            elif check_type == "cross_segment_sum":
                errors.extend(self._check_cross_segment_sum(rule, parsed))
            elif check_type == "cross_record_unique":
                errors.extend(self._check_cross_record_unique(rule, parsed))
                
        is_valid = len(errors) == 0
        error_count = sum(1 for e in errors if e.severity == Severity.ERROR)
        warning_count = sum(1 for e in errors if e.severity == Severity.WARNING)
        
        return ValidationResult(
            transaction_type=self.transaction_type,
            is_valid=is_valid,
            error_count=error_count,
            warning_count=warning_count,
            errors=errors
        )

    def _get_element_value(self, segment, position):
        for e in segment.elements:
            if e.position == position:
                return e.value
        return None

    def _check_condition(self, segment, condition):
        if not condition:
            return True
        val = self._get_element_value(segment, condition["when_element"])
        return val == condition["when_value"]

    def _check_required_segment(self, rule, parsed):
        errors = []
        target_loop_id = rule["loop_id"]
        loop_found = False
        
        def traverse(loops):
            nonlocal loop_found
            for loop in loops:
                if loop.loop_id == target_loop_id:
                    loop_found = True
                    if not any(s.id == rule["segment_id"] for s in loop.segments):
                        errors.append(ValidationError(
                            error_code=rule["error_code"],
                            severity=Severity(rule["severity"]),
                            loop_id=loop.loop_id,
                            segment_id=rule["segment_id"],
                            element_position=0,
                            raw_value=None,
                            expected=f"Segment {rule['segment_id']}",
                            plain_english=rule["plain_english"],
                            line_number=0,
                            auto_fix_available=False,
                            suggested_fix=None
                        ))
                traverse(loop.children)
                
        traverse(parsed.loops)
        
        if not loop_found:
            errors.append(ValidationError(
                error_code=rule["error_code"],
                severity=Severity(rule["severity"]),
                loop_id=target_loop_id,
                segment_id=rule["segment_id"],
                element_position=0,
                raw_value=None,
                expected=f"Segment {rule['segment_id']}",
                plain_english=rule["plain_english"],
                line_number=0,
                auto_fix_available=False,
                suggested_fix=None
            ))
            
        return errors

    def _check_regex(self, rule, parsed):
        errors = []
        for seg in parsed.raw_segments:
            if seg.id == rule["segment_id"]:
                if self._check_condition(seg, rule.get("condition")):
                    val = self._get_element_value(seg, rule["element_position"])
                    if val is None or not re.match(rule["pattern"], val):
                        msg = rule["plain_english"].replace("{raw_value}", str(val))
                        errors.append(ValidationError(
                            error_code=rule["error_code"],
                            severity=Severity(rule["severity"]),
                            loop_id=seg.loop_id,
                            segment_id=seg.id,
                            element_position=rule["element_position"],
                            raw_value=val,
                            expected=rule["pattern"],
                            plain_english=msg,
                            line_number=seg.line_number,
                            auto_fix_available=(rule["error_code"] in ("INVALID_DATE_FORMAT", "MISSING_ROI_CODE")),
                            suggested_fix=None
                        ))
        return errors

    def _check_enum(self, rule, parsed):
        errors = []
        for seg in parsed.raw_segments:
            if seg.id == rule["segment_id"]:
                if self._check_condition(seg, rule.get("condition")):
                    val = self._get_element_value(seg, rule["element_position"])
                    if val not in rule["valid_values"]:
                        msg = rule["plain_english"].replace("{raw_value}", str(val))
                        errors.append(ValidationError(
                            error_code=rule["error_code"],
                            severity=Severity(rule["severity"]),
                            loop_id=seg.loop_id,
                            segment_id=seg.id,
                            element_position=rule["element_position"],
                            raw_value=val,
                            expected=f"One of {rule['valid_values']}",
                            plain_english=msg,
                            line_number=seg.line_number,
                            auto_fix_available=False,
                            suggested_fix=None
                        ))
        return errors

    def _check_luhn(self, rule, parsed):
        import requests
        errors = []
        for seg in parsed.raw_segments:
            if seg.id == rule["segment_id"]:
                if self._check_condition(seg, rule.get("condition")):
                    val = self._get_element_value(seg, rule["element_position"])
                    if val and not luhn.is_valid(val):
                        msg = rule["plain_english"].replace("{raw_value}", str(val))
                        errors.append(ValidationError(
                            error_code=rule["error_code"],
                            severity=Severity(rule["severity"]),
                            loop_id=seg.loop_id,
                            segment_id=seg.id,
                            element_position=rule["element_position"],
                            raw_value=val,
                            expected="Valid Luhn NPI",
                            plain_english=msg,
                            line_number=seg.line_number,
                            auto_fix_available=False,
                            suggested_fix=None
                        ))
                    elif val and os.environ.get("TESTING") != "1":
                        # Bonus Feature: Real NPI Validation
                        try:
                            resp = requests.get(f"https://npiregistry.cms.hhs.gov/api/?number={val}&version=2.1", timeout=5)
                            if resp.status_code == 200:
                                data = resp.json()
                                if "Errors" in data or not data.get("results"):
                                    errors.append(ValidationError(
                                        error_code="NPI_NOT_FOUND",
                                        severity=Severity.ERROR,
                                        loop_id=seg.loop_id,
                                        segment_id=seg.id,
                                        element_position=rule["element_position"],
                                        raw_value=val,
                                        expected="Registered NPI",
                                        plain_english=f"The NPI '{val}' passed checksum but is not registered in the NPPES registry.",
                                        line_number=seg.line_number,
                                        auto_fix_available=False,
                                        suggested_fix=None
                                    ))
                                else:
                                    # Check name mismatch
                                    results = data["results"][0]
                                    basic_info = results.get("basic", {})
                                    org_name = basic_info.get("organization_name", "")
                                    first_name = basic_info.get("first_name", "")
                                    last_name = basic_info.get("last_name", "")
                                    
                                    nppes_name_str = f"{org_name} {first_name} {last_name}".lower()
                                    nm1_name = self._get_element_value(seg, 3) or ""
                                    
                                    if nm1_name and nm1_name.lower() not in nppes_name_str and nppes_name_str.strip():
                                        errors.append(ValidationError(
                                            error_code="NPI_NAME_MISMATCH",
                                            severity=Severity.WARNING,
                                            loop_id=seg.loop_id,
                                            segment_id=seg.id,
                                            element_position=3,
                                            raw_value=nm1_name,
                                            expected="Matches NPPES registry",
                                            plain_english=f"The name '{nm1_name}' does not closely match the NPPES registry record for NPI {val}.",
                                            line_number=seg.line_number,
                                            auto_fix_available=False,
                                            suggested_fix=None
                                        ))
                        except Exception:
                            # Ignore API call failures in order not to block validation completely
                            pass

        return errors

    def _check_cross_segment_sum(self, rule, parsed):
        errors = []
        target_loop_id = rule["loop_id"]
        
        def traverse(loops):
            for loop in loops:
                if loop.loop_id == target_loop_id:
                    # Find source segment
                    src_seg = next((s for s in loop.segments if s.id == rule["source_segment"]), None)
                    if src_seg:
                        src_val_str = self._get_element_value(src_seg, rule["source_element"])
                        try:
                            src_val = float(src_val_str)
                        except (ValueError, TypeError):
                            src_val = 0.0
                            
                        # Find child loops and sum
                        total_sum = 0.0
                        for child in loop.children:
                            if child.loop_id == rule["sum_loop"]:
                                sum_seg = next((s for s in child.segments if s.id == rule["sum_segment"]), None)
                                if sum_seg:
                                    s_val_str = self._get_element_value(sum_seg, rule["sum_element"])
                                    try:
                                        total_sum += float(s_val_str)
                                    except (ValueError, TypeError):
                                        pass
                        
                        if abs(src_val - total_sum) > 0.01:
                            msg = rule["plain_english"].replace("{raw_value}", str(src_val_str)).replace("{sum_value}", str(total_sum))
                            errors.append(ValidationError(
                                error_code=rule["error_code"],
                                severity=Severity(rule["severity"]),
                                loop_id=loop.loop_id,
                                segment_id=src_seg.id,
                                element_position=rule["source_element"],
                                raw_value=str(src_val_str),
                                expected=str(total_sum),
                                plain_english=msg,
                                line_number=src_seg.line_number,
                                auto_fix_available=True,
                                suggested_fix=None
                            ))
                traverse(loop.children)
                
        traverse(parsed.loops)
        return errors

    def _check_cross_record_unique(self, rule, parsed):
        errors = []
        seen = set()
        for seg in parsed.raw_segments:
            if seg.id == rule["segment_id"]:
                if self._check_condition(seg, rule.get("condition")):
                    val = self._get_element_value(seg, rule["element_position"])
                    if val in seen:
                        msg = rule["plain_english"].replace("{raw_value}", str(val))
                        errors.append(ValidationError(
                            error_code=rule["error_code"],
                            severity=Severity(rule["severity"]),
                            loop_id=seg.loop_id,
                            segment_id=seg.id,
                            element_position=rule["element_position"],
                            raw_value=val,
                            expected="Unique value",
                            plain_english=msg,
                            line_number=seg.line_number,
                            auto_fix_available=False,
                            suggested_fix=None
                        ))
                    if val:
                        seen.add(val)
        return errors