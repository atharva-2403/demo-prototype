# Skill: Claude API Chat Integration
## Purpose
Patterns for calling the Anthropic Claude API, structuring system prompts,
and managing conversation history for the ClearClaim AI assistant.

## Key Knowledge

### Client Initialisation
```python
import anthropic, os
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```
Never hardcode the API key. Always read from environment variable.

### API Call Pattern
```python
response = client.messages.create(
    model="claude-sonnet-4-6",    # Always use this model
    max_tokens=1000,              # Sufficient for explanation responses
    system=system_prompt,         # Role + constraints
    messages=messages             # Conversation history list
)
return response.content[0].text
```

### First Message vs Subsequent Messages
First message (history is empty): prepend the full Markdown context document.
Subsequent messages: the context is already in history, just append the question.
```python
if not history:
    messages = [{"role": "user", "content":
        f"Here is the file analysis:\n\n{markdown_context}\n\nMy question: {question}"}]
else:
    messages = history + [{"role": "user", "content": question}]
```

### System Prompt Design
The system prompt must include these three elements:
  1. Role definition ("You are ClearClaim AI, an expert EDI assistant")
  2. Data source constraint ("Only answer using the Markdown document provided")
  3. Citation rule ("Always cite Error N from Section 3 when referencing errors")
Never ask the LLM to recall EDI rules from memory — it must reason from the file.

## MUST_NOT
- MUST_NOT hardcode the API key — always use os.getenv("ANTHROPIC_API_KEY").
- MUST_NOT pass raw JSON as context — always use the Markdown from SKILL-MARKDOWN-CTX.
- MUST_NOT use a different model than claude-sonnet-4-6.
- MUST_NOT call the LLM for fix suggestions — that belongs in fix_suggester.py
  and must be rule-based only (see SKILL-EXPORT).

## Discovered During Implementation
