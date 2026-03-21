from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
from parser.state_machine import parse_edi
from datetime import datetime

router = APIRouter()

class EligibilityReport(BaseModel):
    total_claims_checked: int
    eligible_claims: int
    ineligible_claims: int
    mismatches: List[Dict[str, Any]]

def parse_date(date_str):
    if not date_str or len(date_str) != 8:
        return None
    try:
        return datetime.strptime(date_str, "%Y%m%d")
    except ValueError:
        return None

def extract_enrollment(loops):
    members = {}
    for loop in loops:
        if loop.loop_id == "2000":
            ref_seg = next((s for s in loop.segments if s.id == "REF" and any(e.position == 1 and e.value == "0F" for e in s.elements)), None)
            ins_seg = next((s for s in loop.segments if s.id == "INS"), None)
            
            status = "active"
            if ins_seg:
                ins03 = next((e.value for e in ins_seg.elements if e.position == 3), "")
                if ins03 == "024":
                    status = "terminated"
            
            member_id = None
            if ref_seg:
                member_id = next((e.value for e in ref_seg.elements if e.position == 2), None)
            
            start_date, end_date = None, None
            for child in loop.children:
                if child.loop_id == "2300":
                    for seg in child.segments:
                        if seg.id == "DTP":
                            qual = next((e.value for e in seg.elements if e.position == 1), "")
                            date_val = next((e.value for e in seg.elements if e.position == 3), "")
                            if qual == "348":
                                start_date = parse_date(date_val)
                            elif qual == "349":
                                end_date = parse_date(date_val)
            
            if member_id:
                members[member_id] = {
                    "status": status,
                    "start_date": start_date,
                    "end_date": end_date
                }
        else:
            members.update(extract_enrollment(loop.children))
    return members

def extract_claims(loops):
    claims = []
    for loop in loops:
        if loop.loop_id == "2000B":
            nm1_seg = next((s for s in loop.children[0].segments if s.id == "NM1" and any(e.position == 1 and e.value == "IL" for e in s.elements)), None) if loop.children else None
            member_id = None
            if nm1_seg:
                member_id = next((e.value for e in nm1_seg.elements if e.position == 9), None)
            
            for child in loop.children:
                if child.loop_id == "2300":
                    clm_seg = next((s for s in child.segments if s.id == "CLM"), None)
                    dtp_seg = next((s for s in child.segments if s.id == "DTP" and any(e.position == 1 and e.value == "472" for e in s.elements)), None)
                    
                    claim_id = next((e.value for e in clm_seg.elements if e.position == 1), "UNKNOWN") if clm_seg else "UNKNOWN"
                    date_val = next((e.value for e in dtp_seg.elements if e.position == 3), "") if dtp_seg else ""
                    
                    if "-" in date_val:
                        date_val = date_val.split("-")[0]
                        
                    dos = parse_date(date_val)
                    if member_id:
                        claims.append({
                            "claim_id": claim_id,
                            "member_id": member_id,
                            "date_of_service": dos,
                            "raw_date": date_val
                        })
        else:
            claims.extend(extract_claims(loop.children))
    return claims

@router.post("/eligibility", response_model=EligibilityReport)
async def check_eligibility(claim_file: UploadFile = File(...), enrollment_file: UploadFile = File(...)):
    try:
        claim_text = (await claim_file.read()).decode("utf-8", errors="replace")
        enrollment_text = (await enrollment_file.read()).decode("utf-8", errors="replace")
        
        parsed_837 = parse_edi(claim_text)
        parsed_834 = parse_edi(enrollment_text)
        
        if parsed_837.transaction_type not in ["837P", "837I"]:
            raise HTTPException(status_code=400, detail="First file must be 837 claim")
        if parsed_834.transaction_type != "834":
            raise HTTPException(status_code=400, detail="Second file must be 834 enrollment")
            
        enrollments = extract_enrollment(parsed_834.loops)
        claims = extract_claims(parsed_837.loops)
        
        total_claims = len(claims)
        eligible = 0
        ineligible = 0
        mismatches = []
        
        for claim in claims:
            mid = claim["member_id"]
            dos = claim["date_of_service"]
            
            if mid not in enrollments:
                ineligible += 1
                mismatches.append({
                    "claim_id": claim["claim_id"],
                    "member_id": mid,
                    "date_of_service": claim["raw_date"],
                    "reason": "Member not found in enrollment file"
                })
                continue
                
            enr = enrollments[mid]
            is_valid = True
            reason = ""
            
            if dos is None:
                is_valid = False
                reason = "Invalid or missing date of service"
            elif enr["status"] == "terminated" and enr["end_date"] is None:
                is_valid = False
                reason = "Member terminated (no end date specified)"
            else:
                if enr["start_date"] and dos < enr["start_date"]:
                    is_valid = False
                    reason = f"Service date before coverage start ({enr['start_date'].strftime('%Y%m%d')})"
                elif enr["end_date"] and dos > enr["end_date"]:
                    is_valid = False
                    reason = f"Service date after coverage end ({enr['end_date'].strftime('%Y%m%d')})"
                    
            if is_valid:
                eligible += 1
            else:
                ineligible += 1
                mismatches.append({
                    "claim_id": claim["claim_id"],
                    "member_id": mid,
                    "date_of_service": claim["raw_date"],
                    "reason": reason
                })
                
        return EligibilityReport(
            total_claims_checked=total_claims,
            eligible_claims=eligible,
            ineligible_claims=ineligible,
            mismatches=mismatches
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))