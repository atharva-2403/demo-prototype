from fastapi import APIRouter
from pydantic import BaseModel
from parser.models import ParsedEDI
from validator.models import ValidationResult
from fastapi.responses import Response
from export.pdf_exporter import generate_pdf

class ExportRequest(BaseModel):
    parsed: ParsedEDI
    validation: ValidationResult

router = APIRouter()

@router.post("/export/pdf")
async def export_pdf(req: ExportRequest):
    pdf_bytes = generate_pdf(req.parsed, req.validation)
    filename = f"{req.parsed.file_name}_report.pdf"
    return Response(
        content=pdf_bytes, 
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Suggested-Filename": filename
        }
    )

@router.post("/export/json")
async def export_json(req: ExportRequest):
    return req.parsed.model_dump()