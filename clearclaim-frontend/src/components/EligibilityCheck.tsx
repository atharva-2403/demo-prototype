import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export default function EligibilityCheck() {
  const [claimFile, setClaimFile] = useState<File | null>(null);
  const [enrFile, setEnrFile] = useState<File | null>(null);
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDropClaim = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) setClaimFile(acceptedFiles[0]);
  }, []);

  const onDropEnr = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) setEnrFile(acceptedFiles[0]);
  }, []);

  const { getRootProps: getClaimProps, getInputProps: getClaimInput } = useDropzone({ onDrop: onDropClaim, maxFiles: 1 });
  const { getRootProps: getEnrProps, getInputProps: getEnrInput } = useDropzone({ onDrop: onDropEnr, maxFiles: 1 });

  const handleCheck = async () => {
    if (!claimFile || !enrFile) return;
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('claim_file', claimFile);
      formData.append('enrollment_file', enrFile);
      const res = await axios.post(`${API_BASE}/eligibility`, formData);
      setReport(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed to check eligibility");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-4 rounded shadow border border-slate-200 mt-6">
      <h2 className="font-bold text-slate-800 mb-4 border-b pb-2">834 Eligibility Cross-Check</h2>
      
      {!report ? (
        <div className="flex flex-col gap-4">
          <div className="flex gap-4">
            <div {...getClaimProps()} className="flex-1 border-2 border-dashed border-slate-300 p-8 text-center cursor-pointer hover:bg-slate-50">
              <input {...getClaimInput()} />
              <p className="text-slate-600 font-medium">1. Drop 837 Claim File</p>
              {claimFile && <p className="text-sm text-green-600 mt-2">✓ {claimFile.name}</p>}
            </div>
            
            <div {...getEnrProps()} className="flex-1 border-2 border-dashed border-slate-300 p-8 text-center cursor-pointer hover:bg-slate-50">
              <input {...getEnrInput()} />
              <p className="text-slate-600 font-medium">2. Drop 834 Enrollment File</p>
              {enrFile && <p className="text-sm text-green-600 mt-2">✓ {enrFile.name}</p>}
            </div>
          </div>
          
          <button 
            onClick={handleCheck} 
            disabled={!claimFile || !enrFile || loading}
            className="bg-indigo-600 text-white font-bold py-2 px-4 rounded disabled:opacity-50 hover:bg-indigo-700"
          >
            {loading ? "Checking..." : "Cross-Check Eligibility"}
          </button>
          
          {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
        </div>
      ) : (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-bold">Eligibility Results</h3>
            <button onClick={() => { setReport(null); setClaimFile(null); setEnrFile(null); }} className="text-sm text-blue-500 hover:underline">Start Over</button>
          </div>
          
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-slate-50 p-4 rounded border border-slate-200 text-center">
              <h4 className="font-bold text-slate-600">Total Checked</h4>
              <p className="text-2xl font-bold text-slate-800">{report.total_claims_checked}</p>
            </div>
            <div className="bg-green-50 p-4 rounded border border-green-200 text-center">
              <h4 className="font-bold text-green-700">Eligible</h4>
              <p className="text-2xl font-bold text-green-800">{report.eligible_claims}</p>
            </div>
            <div className="bg-red-50 p-4 rounded border border-red-200 text-center">
              <h4 className="font-bold text-red-700">Ineligible</h4>
              <p className="text-2xl font-bold text-red-800">{report.ineligible_claims}</p>
            </div>
          </div>
          
          {report.mismatches.length > 0 && (
            <div>
              <h4 className="font-bold text-red-700 mb-2">Mismatches / Ineligible Claims</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b-2 border-slate-200 bg-slate-50">
                      <th className="p-2 text-sm font-semibold text-slate-600">Claim ID</th>
                      <th className="p-2 text-sm font-semibold text-slate-600">Member ID</th>
                      <th className="p-2 text-sm font-semibold text-slate-600">Date of Service</th>
                      <th className="p-2 text-sm font-semibold text-slate-600">Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.mismatches.map((m: any, i: number) => (
                      <tr key={i} className="border-b border-slate-100">
                        <td className="p-2 text-sm font-mono">{m.claim_id}</td>
                        <td className="p-2 text-sm font-mono">{m.member_id}</td>
                        <td className="p-2 text-sm">{m.date_of_service}</td>
                        <td className="p-2 text-sm text-red-600">{m.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}