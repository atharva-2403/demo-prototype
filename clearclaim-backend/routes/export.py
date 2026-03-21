from fastapi import APIRouter
from pydantic import BaseModel
from parser.models import ParsedEDI
from validator.models import ValidationResult
from fastapi.responses import Response

class ExportRequest(BaseModel):
    parsed: ParsedEDI
    validation: ValidationResult

router = APIRouter()

@router.post("/export/pdf")
async def export_pdf(req: ExportRequest):
    # To be implemented in Phase 8
    return Response(content=b"PDF bytes", media_type="application/pdf")

@router.post("/export/json")
async def export_json(req: ExportRequest):
    return req.parsed.model_dump()