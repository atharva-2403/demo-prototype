from fastapi import APIRouter, HTTPException
from parser.models import ParsedEDI
from validator.models import ValidationResult
from validator.rule_engine import RuleEngine

router = APIRouter()

@router.post("/validate", response_model=ValidationResult)
async def validate_edi(parsed: ParsedEDI):
    try:
        engine = RuleEngine(parsed.transaction_type)
        return engine.validate(parsed)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error validating EDI file: {str(e)}")