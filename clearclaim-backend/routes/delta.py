import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
from parser.state_machine import parse_edi

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

router = APIRouter()

class DeltaReport(BaseModel):
    additions: List[Dict[str, Any]]
    terminations: List[Dict[str, Any]]
    changes: List[Dict[str, Any]]

def extract_members(loops):
    members = {}
    for loop in loops:
        if loop.loop_id == "2000":
            ref_seg = next((s for s in loop.segments if s.id == "REF" and any(e.position == 1 and e.value == "0F" for e in s.elements)), None)
            if ref_seg:
                member_id = next((e.value for e in ref_seg.elements if e.position == 2), None)
                if member_id:
                    # Collect all segments as a comparable string
                    nm1_seg = next((s for s in loop.children[0].segments if s.id == "NM1" and any(e.position == 1 and e.value == "IL" for e in s.elements)), None) if loop.children else None
                    name = ""
                    if nm1_seg:
                        last = next((e.value for e in nm1_seg.elements if e.position == 3), "")
                        first = next((e.value for e in nm1_seg.elements if e.position == 4), "")
                        name = f"{first} {last}".strip()
                        
                    raw_data = "".join(s.raw_line for s in loop.segments if s.id not in ["SE", "GE", "IEA"])
                    for child in loop.children:
                        raw_data += "".join(s.raw_line for s in child.segments if s.id not in ["SE", "GE", "IEA"])
                        for subchild in child.children:
                            raw_data += "".join(s.raw_line for s in subchild.segments if s.id not in ["SE", "GE", "IEA"])
                            
                    members[member_id] = {
                        "id": member_id,
                        "name": name,
                        "raw_data": raw_data
                    }
        else:
            members.update(extract_members(loop.children))
    return members

@router.post("/delta", response_model=DeltaReport)
async def generate_delta(old_file: UploadFile = File(...), new_file: UploadFile = File(...)):
    try:
        content_old = await old_file.read()
        content_new = await new_file.read()
        
        if len(content_old) > MAX_FILE_SIZE or len(content_new) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 5MB.")

        old_text = content_old.decode("utf-8", errors="replace")
        new_text = content_new.decode("utf-8", errors="replace")
        
        old_parsed = parse_edi(old_text)
        new_parsed = parse_edi(new_text)
        
        if old_parsed.transaction_type != "834" or new_parsed.transaction_type != "834":
            raise HTTPException(status_code=400, detail="Both files must be 834 transactions")
            
        old_members = extract_members(old_parsed.loops)
        new_members = extract_members(new_parsed.loops)
        
        additions = []
        terminations = []
        changes = []
        
        for mid, data in new_members.items():
            if mid not in old_members:
                additions.append(data)
            elif old_members[mid]["raw_data"] != data["raw_data"]:
                changes.append(data)
                
        for mid, data in old_members.items():
            if mid not in new_members:
                terminations.append(data)
                
        return DeltaReport(
            additions=additions,
            terminations=terminations,
            changes=changes
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delta error: {str(e)}")