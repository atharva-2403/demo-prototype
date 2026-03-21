import type { ParsedEDI, ValidationResult } from '../types/edi';
import { applyFix, validateEDI } from '../api/client';
import { useState } from 'react';

export default function ErrorDashboard({ parsed, validation, onFix }: { parsed: ParsedEDI, validation: ValidationResult, onFix: any }) {
  const [fixing, setFixing] = useState<string | null>(null);

  const handleAutoFix = async (err: any) => {
    setFixing(err.error_code);
    try {
      const newParsed = await applyFix(err, parsed);
      const newValidation = await validateEDI(newParsed);
      onFix(newParsed, newValidation);
    } catch (e) {
      alert("Auto-fix failed");
    } finally {
      setFixing(null);
    }
  };

  return (
    <div className="bg-white p-4 rounded shadow border border-red-200">
      <h2 className="font-bold text-red-600 mb-4 border-b border-red-100 pb-2">Validation Errors</h2>
      <ul className="space-y-4">
        {validation.errors.map((err, i) => (
          <li key={i} className="p-3 bg-red-50 rounded border border-red-100">
            <div className="flex justify-between items-start">
              <div>
                <span className="font-bold text-red-700 block">{err.error_code}</span>
                <span className="text-sm text-red-600">Loop {err.loop_id} | Segment {err.segment_id} | Element {err.element_position}</span>
              </div>
              {err.auto_fix_available && (
                <button 
                  onClick={() => handleAutoFix(err)} 
                  disabled={fixing === err.error_code}
                  className="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600 disabled:bg-blue-300"
                >
                  {fixing === err.error_code ? 'Fixing...' : 'Auto-Fix'}
                </button>
              )}
            </div>
            <p className="mt-2 text-slate-800">{err.plain_english}</p>
            {err.raw_value && <p className="text-xs text-slate-500 mt-1">Found: {err.raw_value} | Expected: {err.expected}</p>}
          </li>
        ))}
      </ul>
    </div>
  );
}