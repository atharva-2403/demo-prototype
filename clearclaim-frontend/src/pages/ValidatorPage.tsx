import { useState } from 'react';
import FileUpload from '../components/FileUpload';
import MetadataBar from '../components/MetadataBar';
import SegmentTree from '../components/SegmentTree';
import ErrorDashboard from '../components/ErrorDashboard';
import AIChatPanel from '../components/AIChatPanel';
import ExportControls from '../components/ExportControls';
import RemittanceSummary from '../components/RemittanceSummary';
import EnrollmentSummary from '../components/EnrollmentSummary';
import DeltaReport from '../components/DeltaReport';
import EligibilityCheck from '../components/EligibilityCheck';
import type { ParsedEDI, ValidationResult } from '../types/edi';

export default function ValidatorPage() {
  const [parsed, setParsed] = useState<ParsedEDI | null>(null);
  const [validation, setValidation] = useState<ValidationResult | null>(null);

  if (!parsed || !validation) {
    return (
      <div className="max-w-6xl mx-auto p-4 flex flex-col gap-6 pb-20">
        <FileUpload onUploadSuccess={(p: ParsedEDI, v: ValidationResult) => { setParsed(p); setValidation(v); }} />
        <DeltaReport />
        <EligibilityCheck />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-4 flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-slate-800">ClearClaim EDI Validator</h1>
        <button onClick={() => {setParsed(null); setValidation(null);}} className="text-sm text-blue-500 hover:underline">Upload Another File</button>
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