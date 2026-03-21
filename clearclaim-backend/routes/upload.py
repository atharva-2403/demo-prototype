from fastapi import APIRouter, UploadFile, File, HTTPException
from parser.state_machine import parse_edi
from parser.models import ParsedEDI

router = APIRouter()

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