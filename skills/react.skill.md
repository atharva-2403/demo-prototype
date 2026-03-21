# Skill: React + TypeScript Frontend Patterns
## Purpose
Component patterns, Tailwind usage, and UI patterns for the ClearClaim frontend.

## Key Knowledge

### Mock Data Pattern (for development before backend is ready)
```typescript
// tests/mocks/mock_parsed_edi.ts
export const mockParsedEDI: ParsedEDI = {
  file_name: "test.edi",
  transaction_type: "837P",
  // ... minimal but complete mock matching the interface exactly
};
```
Always develop components against mock data first, then switch to API.

### Collapsible Tree Pattern (SegmentTree)
Use @uiw/react-json-view for the segment tree — it handles recursive
collapsible rendering out of the box. Pass parsed.loops as the data source.
Customise the theme to match Tailwind's slate colour palette.

### Colour Coding Pattern (EnrollmentSummary)
```typescript
const getRowClass = (maintenanceType: string) => {
  if (maintenanceType === "021") return "bg-green-50 border-green-200";
  if (maintenanceType === "024") return "bg-red-50 border-red-200";
  if (maintenanceType === "001") return "bg-yellow-50 border-yellow-200";
  return "bg-gray-50 border-gray-200";
};
```
The INS03 values are from SKILL-EDI-834 — "021"=Addition, "024"=Termination, "001"=Change.

### AI Chat Loading Pattern
```tsx
const [isThinking, setIsThinking] = useState(false);
const handleSend = async () => {
  setIsThinking(true);
  try {
    const response = await sendChatMessage(question, parsed, validation, history);
    // append response
  } catch {
    setError("The AI assistant is temporarily unavailable. Please try again.");
  } finally {
    setIsThinking(false);
  }
};
```

### Tab Navigation Pattern
Use a simple border-bottom approach for tabs — no external library needed.
The three tabs are "tree", "errors", and "summary". Auto-switch to "errors"
when validation.error_count > 0 after file upload.

## MUST_NOT
- MUST_NOT wait for the backend to build components — use mocks from day one.
- MUST_NOT build components in the wrong order — follow the build order in the
  Subagent C system prompt exactly.
- MUST_NOT style colour coding with hardcoded hex values — use Tailwind classes.
- MUST_NOT omit loading state on AIChatPanel — users must see the spinner.

## Discovered During Implementation
