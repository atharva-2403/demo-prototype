from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from parser.models import ParsedEDI
from validator.models import ValidationError
from ai.fix_suggester import suggest_fix

class FixRequest(BaseModel):
    error: ValidationError
    parsed: ParsedEDI
    fix_value: str = None

router = APIRouter()

@router.post("/fix", response_model=ParsedEDI)
async def fix_endpoint(req: FixRequest):
    if not req.fix_value:
        suggested = suggest_fix(req.error, req.parsed)
        if not suggested:
            raise HTTPException(status_code=400, detail="Cannot auto-fix this error")
        req.fix_value = suggested
        
    for seg in req.parsed.raw_segments:
        if seg.id == req.error.segment_id and seg.line_number == req.error.line_number:
            for el in seg.elements:
                if el.position == req.error.element_position:
                    el.value = req.fix_value
                    
                    # Also update raw string line roughly
                    parts = seg.raw_line.split(req.parsed.delimiter_element)
                    if len(parts) > el.position:
                        parts[el.position] = req.fix_value
                        seg.raw_line = req.parsed.delimiter_element.join(parts)
                    break
    return req.parsed