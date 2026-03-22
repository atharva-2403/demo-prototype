import { useState } from 'react';
import FileUpload from '../components/FileUpload';
import MetadataBar from '../components/MetadataBar';
import SegmentTree from '../components/SegmentTree';
import ErrorDashboard from '../components/ErrorDashboard';
import AIChatPanel from '../components/AIChatPanel';
import ExportControls from '../components/ExportControls';
import RemittanceSummary from '../components/RemittanceSummary';
import EnrollmentSummary from '../components/EnrollmentSummary';
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

  if (activeMode === 'eligibility') {
    return (
      <div className="max-w-6xl mx-auto p-4 flex flex-col gap-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-slate-800">Eligibility Cross-Check Report</h1>
          <button onClick={() => setActiveMode(null)} className="text-sm text-blue-500 hover:underline">Upload Another File</button>
        </div>
        
        <div className="bg-white p-6 rounded-xl shadow border border-slate-200">
          <div className="grid grid-cols-3 gap-4 mb-8">
            <div className="bg-slate-50 p-6 rounded-lg border border-slate-200 text-center">
              <h4 className="font-bold text-slate-600 uppercase tracking-wide text-sm">Total Claims</h4>
              <p className="text-4xl font-extrabold text-slate-800 mt-2">{modeData.total_claims_checked}</p>
            </div>
            <div className="bg-green-50 p-6 rounded-lg border border-green-200 text-center">
              <h4 className="font-bold text-green-700 uppercase tracking-wide text-sm">Eligible</h4>
              <p className="text-4xl font-extrabold text-green-600 mt-2">{modeData.eligible_claims}</p>
            </div>
            <div className="bg-red-50 p-6 rounded-lg border border-red-200 text-center">
              <h4 className="font-bold text-red-700 uppercase tracking-wide text-sm">Ineligible</h4>
              <p className="text-4xl font-extrabold text-red-600 mt-2">{modeData.ineligible_claims}</p>
            </div>
          </div>

          {modeData.mismatches && modeData.mismatches.length > 0 ? (
            <div>
              <h3 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                Coverage Mismatches Detected
              </h3>
              <div className="overflow-x-auto rounded-lg border border-slate-200">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-sm font-semibold text-slate-600">
                      <th className="p-3">Claim ID</th>
                      <th className="p-3">Member ID</th>
                      <th className="p-3">Date of Service</th>
                      <th className="p-3">Rejection Reason</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-sm">
                    {modeData.mismatches.map((m: any, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="p-3 font-mono text-slate-700">{m.claim_id}</td>
                        <td className="p-3 font-mono text-slate-700">{m.member_id}</td>
                        <td className="p-3 text-slate-600">{m.date_of_service}</td>
                        <td className="p-3 text-red-600 font-medium">{m.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="bg-green-50 text-green-700 p-4 rounded-lg flex items-center justify-center gap-2 border border-green-200">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
              <span className="font-bold">All claims have verified active coverage!</span>
            </div>
          )}
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