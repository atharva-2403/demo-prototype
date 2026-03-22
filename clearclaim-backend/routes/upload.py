from fastapi import APIRouter, UploadFile, File, HTTPException
from parser.state_machine import parse_edi
from parser.models import ParsedEDI

router = APIRouter()

@router.post("/preflight")
async def preflight_check(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = content.decode("utf-8", errors="replace")
        segments = [s.strip() for s in text.replace('\n', '').replace('\r', '').split('~') if s.strip()]
        
        edi_type = "Unknown"
        for seg in segments:
            parts = seg.split('*')
            if parts[0] == 'ST' and len(parts) > 1:
                edi_type = parts[1]
                break
                
        return {
            "file_name": file.filename,
            "segment_count": len(segments),
            "edi_type": edi_type
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error in preflight check: {str(e)}")

@router.post("/upload", response_model=ParsedEDI)
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = content.decode("utf-8", errors="replace")
        parsed = parse_edi(text)
        parsed.file_name = file.filename
        return parsed
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing EDI file: {str(e)}")