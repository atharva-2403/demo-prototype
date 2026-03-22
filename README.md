# demo-prototype
For Hackathon Inspiron 5.0
NOTE: ONLY THE GEMINI API KEY EXISTS SO PLEASE TEST USING THE GEMINI MODEL ONLY. ALSO ITS FREE TIER SO DONT EXPECT MUCH.






ClearClaim — Enterprise EDI Intelligence Platform
ClearClaim is a "security-first" AI-driven analytics suite designed to deconstruct, validate, and reconcile complex healthcare X12 EDI transactions. Built for the 2026 Hackathon, it bridges the gap between cryptic legacy billing formats and actionable administrative insights using a hybrid state-machine and LLM approach.


Key Features
1. Unified Mission Control Dashboard
Above-the-Fold Design: A consolidated UI that fits entirely within the primary viewport, eliminating scrolling and maximizing judge engagement.

Dynamic Dropzone Geometry: Intelligently reconfigures from a single-file parser to side-by-side relational staging zones based on the selected operation mode.

Native Drag-and-Drop: Utilizes native HTML5 event handlers to prevent browsers from opening sensitive EDI files in new tabs.



2. Relational EDI Engines
834 Enrollment Delta: Automatically identifies member additions, terminations, and attribute changes between two enrollment cycles.

835/837 Payment Reconciliation: Handshakes Professional Claims (837) with Remittance Advice (835) to instantly flag underpayments and denials.

Eligibility Cross-Check: Validates active coverage by matching 837 claim data against 834 enrollment records to prevent eligibility-based rejections.



3. Interpretive AI Consultant
Multi-LLM Orchestration: Dynamically routes processed EDI trees to Gemini 2.5 and Claude 3.5.

Plain-English Explanations: Converts raw segment data into human-readable billing advice and "Next Step" instructions for administrative staff.

Expert Persona: The AI functions as a specialized Medical Billing and EDI Consultant, focusing on business impact rather than repeating technical codes.

Enterprise Security & Compliance
ClearClaim treats simulated Protected Health Information (PHI) with production-level rigor:

HIPAA-Compliant Masking: A regex-based sanitization layer in context_builder.py redacts SSNs and sensitive demographics before data reaches external AI APIs.

Prompt Injection Defense: Implements strict triple-quote delimiters and system prompt boundaries to prevent malicious EDI payloads from hijacking the LLM.

Hardened Infrastructure: Migrated to PyJWT to resolve CVE-2024-33663 and enforced strict CORS whitelisting for the production Vercel domain.

Zero-Trust Network: API access is strictly limited to the production frontend URL via environment variables.



Tech Stack
Frontend: React 18, Tailwind CSS, Vite.


Backend: FastAPI (Python 3.11+), deployed on Render.



AI/ML: Google Gemini (Default), Anthropic Claude, Custom X12 State-Machine Parser.



Deployment: Vercel (Frontend), Render (Backend), GitHub Actions.



Project Structure


├── clearclaim-backend/
│   ├── ai/               # LLM Orchestration & Prompt Engineering
│   ├── parsers/          # Custom X12 State-Machine Logic
│   ├── main.py           # FastAPI Entry & Secure CORS Middleware
│   └── context_builder.py # PHI Masking & Markdown Generation
├── src/                  # React Frontend
│   ├── components/       # Mission Control & Segment Tree UI
│   ├── api/              # Secure Client with Env Injection
│   └── App.tsx           # Global State & Mode Routing
└── Security_Action_Plan.md # Audit findings and implemented patches
