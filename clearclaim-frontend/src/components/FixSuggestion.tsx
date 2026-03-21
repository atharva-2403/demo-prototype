import type { ParsedEDI, ValidationResult } from '../types/edi';
import { applyFix, validateEDI } from '../api/client';
import { useState } from 'react';

export default function FixSuggestion({ err, parsed, onFix }: { err: any, parsed: ParsedEDI, onFix: any }) {
  const [fixing, setFixing] = useState(false);

  const handleAutoFix = async () => {
    setFixing(true);
    try {
      const newParsed = await applyFix(err, parsed);
      const newValidation = await validateEDI(newParsed);
      onFix(newParsed, newValidation);
    } catch (e) {
      alert("Auto-fix failed");
    } finally {
      setFixing(false);
    }
  };

  if (!err.auto_fix_available) return null;

  return (
    <button 
      onClick={handleAutoFix} 
      disabled={fixing}
      className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600 disabled:bg-blue-300 ml-4"
    >
      {fixing ? 'Fixing...' : 'Auto-Fix'}
    </button>
  );
}