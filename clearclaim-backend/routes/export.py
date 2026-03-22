from fastapi import APIRouter
from pydantic import BaseModel
from parser.models import ParsedEDI
from validator.models import ValidationResult
from fastapi.responses import Response, StreamingResponse
from io import BytesIO
import traceback
import sys

@router.post("/export/pdf")
async def export_pdf(req: ExportRequest):
    try:
        print(f"Generating PDF for {req.parsed.file_name}...", file=sys.stderr)
        pdf_bytes = generate_pdf(req.parsed, req.validation)
        filename = f"{req.parsed.file_name}_report.pdf"
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Suggested-Filename": filename,
                "Access-Control-Expose-Headers": "Content-Disposition, X-Suggested-Filename"
            }
        )
    except Exception as e:
        print("PDF GENERATION FAILURE:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return Response(
            content=f"Error generating PDF: {str(e)}",
            status_code=500,
            media_type="text/plain"
        )

@router.post("/export/json")
async def export_json(req: ExportRequest):
    return req.parsed.model_dump()