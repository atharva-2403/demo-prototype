from pydantic import BaseModel
from typing import List, Optional
from parser.models import ParsedEDI
from validator.models import ValidationResult
from ai.context_builder import parsed_edi_to_markdown
from ai.llm_provider import get_llm_provider

async def get_chat_response(question: str, parsed: ParsedEDI, validation: ValidationResult, history: List[dict] = None, llm_provider: Optional[str] = None) -> str:
    try:
        provider = get_llm_provider(llm_provider)
        
        system_prompt = (
            "You are ClearClaim AI, an expert EDI assistant.\n"
            "Only answer using the Markdown document provided.\n"
            "Always cite Error N from Section 3 when referencing errors."
        )
        
        messages = history or []
        
        if not messages:
            markdown_context = parsed_edi_to_markdown(parsed, validation)
            messages.append({
                "role": "user",
                "content": f"Here is the file analysis:\n\n{markdown_context}\n\nMy question: {question}"
            })
        else:
            messages.append({"role": "user", "content": question})
            
        return await provider.answer(system_prompt, messages)
    except ValueError as ve:
        return f"Configuration Error: {str(ve)}"
    except Exception as e:
        return f"Error communicating with AI: {str(e)}"