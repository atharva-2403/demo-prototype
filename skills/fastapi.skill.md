# Skill: FastAPI Backend Patterns
## Purpose
Standard patterns for FastAPI routes, Pydantic models, and CORS setup.

## Key Knowledge

### App Setup Pattern
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ClearClaim API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev port — CRITICAL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### File Upload Pattern
```python
from fastapi import UploadFile, File
@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8", errors="replace")
    # ...process text...
    return result
```

### Pydantic Request Body Pattern
```python
from pydantic import BaseModel
class ChatRequest(BaseModel):
    question: str
    parsed_edi: ParsedEDI       # Pydantic model used directly as request body
    conversation_history: list
```

### Binary Response for Exports
```python
from fastapi.responses import Response
@router.post("/export/pdf")
async def export_pdf(req: ExportRequest):
    pdf_bytes = generate_pdf(req.parsed, req.validation)
    return Response(content=pdf_bytes, media_type="application/pdf")
```

## MUST_NOT
- MUST_NOT forget allow_origins includes http://localhost:5173 — missing this
  causes CORS errors that look like backend failures.
- MUST_NOT use synchronous file I/O in async routes — use aiofiles or run in executor.
- MUST_NOT return raw dicts — always return Pydantic models for type safety.

## Discovered During Implementation
