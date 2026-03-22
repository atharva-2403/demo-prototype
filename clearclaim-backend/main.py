import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import upload, validate, chat, fix, export, batch, reconcile, delta, eligibility

app = FastAPI(title="ClearClaim API", version="1.0.0")

# Get allowed origins from environment, fallback to localhost for dev
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS", 
    "http://localhost:5173,http://localhost:3000,https://demo-prototype-jade.vercel.app"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(validate.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(fix.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(batch.router, prefix="/api")
app.include_router(reconcile.router, prefix="/api")
app.include_router(delta.router, prefix="/api")
app.include_router(eligibility.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to ClearClaim API"}