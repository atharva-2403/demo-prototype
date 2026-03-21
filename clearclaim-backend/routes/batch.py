from fastapi import APIRouter, UploadFile, File, HTTPException
import zipfile
import io
from pydantic import BaseModel
from typing import List, Dict, Any
from parser.state_machine import parse_edi
from validator.rule_engine import RuleEngine

class BatchReport(BaseModel):
    total_files: int
    files_with_errors: int
    top_errors: List[Dict[str, Any]]
    details: List[Dict[str, Any]]

router = APIRouter()

@router.post("/batch-upload", response_model=BatchReport)
async def batch_upload(file: UploadFile = File(...)):
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported for batch processing")
        
    try:
        content = await file.read()
        zip_file = zipfile.ZipFile(io.BytesIO(content))
        
        total_files = 0
        files_with_errors = 0
        error_counts = {}
        details = []
        
        for file_info in zip_file.infolist():
            if file_info.filename.endswith('.edi') and not file_info.filename.startswith('__MACOSX'):
                total_files += 1
                with zip_file.open(file_info) as f:
                    edi_text = f.read().decode('utf-8', errors='replace')
                    
                try:
                    parsed = parse_edi(edi_text)
                    parsed.file_name = file_info.filename
                    engine = RuleEngine(parsed.transaction_type)
                    validation = engine.validate(parsed)
                    
                    if not validation.is_valid:
                        files_with_errors += 1
                        for err in validation.errors:
                            error_counts[err.error_code] = error_counts.get(err.error_code, 0) + 1
                            
                    details.append({
                        "file_name": parsed.file_name,
                        "transaction_type": parsed.transaction_type,
                        "is_valid": validation.is_valid,
                        "error_count": validation.error_count
                    })
                except Exception as e:
                    details.append({
                        "file_name": file_info.filename,
                        "error": str(e)
                    })
                    files_with_errors += 1
                    
        # Sort errors by frequency
        top_errors = [{"code": k, "count": v} for k, v in sorted(error_counts.items(), key=lambda item: item[1], reverse=True)[:5]]
        
        return BatchReport(
            total_files=total_files,
            files_with_errors=files_with_errors,
            top_errors=top_errors,
            details=details
        )
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid ZIP file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing error: {str(e)}")