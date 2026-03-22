import { useState } from 'react';
import FileUpload from '../components/FileUpload';
import MetadataBar from '../components/MetadataBar';
import SegmentTree from '../components/SegmentTree';
import ErrorDashboard from '../components/ErrorDashboard';
import AIChatPanel from '../components/AIChatPanel';
import ExportControls from '../components/ExportControls';
import RemittanceSummary from '../components/RemittanceSummary';
import EnrollmentSummary from '../components/EnrollmentSummary';
import EligibilityCheck from '../components/EligibilityCheck';
import type { ParsedEDI, ValidationResult } from '../types/edi';

export default function ValidatorPage() {
  const [parsed, setParsed] = useState<ParsedEDI | null>(null);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [activeMode, setActiveMode] = useState<string | null>(null);
  const [modeData, setModeData] = useState<any>(null);

  const handleUploadSuccess = (data: any, v: ValidationResult | null = null, mode: string = 'standard') => {
    setActiveMode(mode);
    if (mode === 'standard') {
      setParsed(data);
      setValidation(v);
    } else {
      setModeData(data);
    }
  };

  if (!activeMode) {
    return (
      <div className="max-w-6xl mx-auto p-4 flex flex-col gap-6 pb-20">
        <FileUpload onUploadSuccess={handleUploadSuccess} />
        <EligibilityCheck />
      </div>
    );
  }

  if (activeMode === 'delta') {
    return (
      <div className="max-w-6xl mx-auto p-4 flex flex-col gap-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-slate-800">834 Delta Report</h1>
          <button onClick={() => setActiveMode(null)} className="text-sm text-blue-500 hover:underline">Upload Another File</button>
        </div>
        <div className="bg-white p-6 rounded shadow border border-slate-200">
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-green-50 p-4 rounded border border-green-200">
              <h4 className="font-bold text-green-800">Additions</h4>
              <p className="text-2xl">{modeData.additions.length}</p>
            </div>
            <div className="bg-red-50 p-4 rounded border border-red-200">
              <h4 className="font-bold text-red-800">Terminations</h4>
              <p className="text-2xl">{modeData.terminations.length}</p>
            </div>
            <div className="bg-yellow-50 p-4 rounded border border-yellow-200">
              <h4 className="font-bold text-yellow-800">Changes</h4>
              <p className="text-2xl">{modeData.changes.length}</p>
            </div>
          </div>
          
          {modeData.additions.length > 0 && (
            <div className="mb-4">
              <h4 className="font-bold text-slate-700 mb-2">Additions</h4>
              <ul className="text-sm space-y-1">
                {modeData.additions.map((m: any, i: number) => (
                  <li key={i} className="flex justify-between border-b py-1">
                    <span>{m.name || "Unknown"}</span>
                    <span className="text-slate-500 font-mono">{m.id}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {modeData.terminations.length > 0 && (
            <div className="mb-4">
              <h4 className="font-bold text-slate-700 mb-2">Terminations</h4>
              <ul className="text-sm space-y-1">
                {modeData.terminations.map((m: any, i: number) => (
                  <li key={i} className="flex justify-between border-b py-1">
                    <span>{m.name || "Unknown"}</span>
                    <span className="text-slate-500 font-mono">{m.id}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {modeData.changes.length > 0 && (
            <div>
              <h4 className="font-bold text-slate-700 mb-2">Changes</h4>
              <ul className="text-sm space-y-1">
                {modeData.changes.map((m: any, i: number) => (
                  <li key={i} className="flex justify-between border-b py-1">
                    <span>{m.name || "Unknown"}</span>
                    <span className="text-slate-500 font-mono">{m.id}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    );
  }

  if (activeMode === 'reconcile') {
    return (
      <div className="max-w-6xl mx-auto p-4 flex flex-col gap-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-slate-800">Reconciliation Report</h1>
          <button onClick={() => setActiveMode(null)} className="text-sm text-blue-500 hover:underline">Upload Another File</button>
        </div>
        <div className="bg-white p-6 rounded shadow border border-slate-200">
           <pre className="text-sm bg-slate-50 p-4 rounded">{JSON.stringify(modeData, null, 2)}</pre>
        </div>
      </div>
    );
  }

  if (activeMode === 'standard' && parsed && validation) {
    return (
      <div className="max-w-6xl mx-auto p-4 flex flex-col gap-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-slate-800">ClearClaim EDI Validator</h1>
          <button onClick={() => setActiveMode(null)} className="text-sm text-blue-500 hover:underline">Upload Another File</button>
        </div>
        <MetadataBar parsed={parsed} validation={validation} />
        <ExportControls parsed={parsed} validation={validation} />
        
        {validation.error_count > 0 && 
          <ErrorDashboard 
            parsed={parsed} 
            validation={validation} 
            onFix={(newP: ParsedEDI, newV: ValidationResult) => { setParsed(newP); setValidation(newV); }} 
          />
        }
        
        {parsed.transaction_type === '835' && <RemittanceSummary parsed={parsed} />}
        {parsed.transaction_type === '834' && <EnrollmentSummary parsed={parsed} />}
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <SegmentTree parsed={parsed} />
          <AIChatPanel parsed={parsed} validation={validation} />
        </div>
      </div>
    );
  }

  return null;
}