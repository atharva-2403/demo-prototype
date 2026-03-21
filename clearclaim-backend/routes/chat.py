from fastapi import APIRouter
from pydantic import BaseModel
from parser.models import ParsedEDI
from validator.models import ValidationResult
from typing import List, Optional
from ai.chat import get_chat_response

class ChatRequest(BaseModel):
    question: str
    parsed_edi: ParsedEDI
    validation: ValidationResult
    conversation_history: List[dict] = []
    llm_provider: Optional[str] = None

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    response_text = await get_chat_response(
        req.question,
        req.parsed_edi,
        req.validation,
        req.conversation_history,
        req.llm_provider
    )
    return {"response": response_text}