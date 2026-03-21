# demo-prototype
For Hackathon Inspiron 5.0






Project: ClearClaim EDI Validation Engine

Architecture and Implementation
ClearClaim is a decoupled web application designed for the high-fidelity parsing and validation of X12 EDI healthcare transaction sets (837, 835, and 834). The system architecture consists of a FastAPI backend and a React 18 frontend, utilizing asynchronous service discovery via build-time environment variables.

Technical Features

State-Machine Parser: A custom-built Python engine that recursively extracts data from nested EDI loops with 100% structural accuracy.

Registry Validation: Real-time NPI verification against the NPPES database and automated ICD-10 formatting enforcement.

AI Analysis: Multi-LLM support (Gemini 2.5 and Claude 3.5) integrated through a specialized Markdown context-builder to eliminate hallucinations and provide intelligent claim rejection insights.

Membership Reporting: An automated 834 Delta Engine identifies additions, terminations, and demographic changes between enrollment cycles.

Production Access

Frontend: Hosted on Netlify.

Backend: Hosted on Render at the /api root endpoint.

Directions for Use
Launch: Access the production URL via the Netlify dashboard.

Upload: Provide a standard .edi transaction file for analysis.

Inspect: Navigate the hierarchical Segment Tree to examine specific transaction data.

Resolve: Consult the Error Dashboard for flagged compliance failures and use the AI panel for detailed resolution steps.
