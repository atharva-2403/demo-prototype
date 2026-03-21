import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export default function DeltaReport() {
  const [oldFile, setOldFile] = useState<File | null>(null);
  const [newFile, setNewFile] = useState<File | null>(null);
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onDropOld = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) setOldFile(acceptedFiles[0]);
  }, []);

  const onDropNew = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) setNewFile(acceptedFiles[0]);
  }, []);

  const { getRootProps: getOldProps, getInputProps: getOldInput } = useDropzone({ onDrop: onDropOld, maxFiles: 1 });
  const { getRootProps: getNewProps, getInputProps: getNewInput } = useDropzone({ onDrop: onDropNew, maxFiles: 1 });

  const handleCompare = async () => {
    if (!oldFile || !newFile) return;
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('old_file', oldFile);
      formData.append('new_file', newFile);
      const res = await axios.post(`${API_BASE}/delta`, formData);
      setReport(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed to compare files");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-4 rounded shadow border border-slate-200 mt-6">
      <h2 className="font-bold text-slate-800 mb-4 border-b pb-2">834 Delta Report</h2>
      
      {!report ? (
        <div className="flex flex-col gap-4">
          <div className="flex gap-4">
            <div {...getOldProps()} className="flex-1 border-2 border-dashed border-slate-300 p-8 text-center cursor-pointer hover:bg-slate-50">
              <input {...getOldInput()} />
              <p className="text-slate-600 font-medium">1. Drop Old 834 File</p>
              {oldFile && <p className="text-sm text-green-600 mt-2">✓ {oldFile.name}</p>}
            </div>
            
            <div {...getNewProps()} className="flex-1 border-2 border-dashed border-slate-300 p-8 text-center cursor-pointer hover:bg-slate-50">
              <input {...getNewInput()} />
              <p className="text-slate-600 font-medium">2. Drop New 834 File</p>
              {newFile && <p className="text-sm text-green-600 mt-2">✓ {newFile.name}</p>}
            </div>
          </div>
          
          <button 
            onClick={handleCompare} 
            disabled={!oldFile || !newFile || loading}
            className="bg-blue-600 text-white font-bold py-2 px-4 rounded disabled:opacity-50"
          >
            {loading ? "Comparing..." : "Generate Delta Report"}
          </button>
          
          {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
        </div>
      ) : (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-bold">Delta Results</h3>
            <button onClick={() => { setReport(null); setOldFile(null); setNewFile(null); }} className="text-sm text-blue-500 hover:underline">Start Over</button>
          </div>
          
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-green-50 p-4 rounded border border-green-200">
              <h4 className="font-bold text-green-800">Additions</h4>
              <p className="text-2xl">{report.additions.length}</p>
            </div>
            <div className="bg-red-50 p-4 rounded border border-red-200">
              <h4 className="font-bold text-red-800">Terminations</h4>
              <p className="text-2xl">{report.terminations.length}</p>
            </div>
            <div className="bg-yellow-50 p-4 rounded border border-yellow-200">
              <h4 className="font-bold text-yellow-800">Changes</h4>
              <p className="text-2xl">{report.changes.length}</p>
            </div>
          </div>
          
          {report.additions.length > 0 && (
            <div>
              <h4 className="font-bold text-slate-700 mb-2">Additions</h4>
              <ul className="text-sm space-y-1">
                {report.additions.map((m: any, i: number) => (
                  <li key={i} className="flex justify-between border-b py-1">
                    <span>{m.name || "Unknown"}</span>
                    <span className="text-slate-500 font-mono">{m.id}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {report.terminations.length > 0 && (
            <div>
              <h4 className="font-bold text-slate-700 mb-2">Terminations</h4>
              <ul className="text-sm space-y-1">
                {report.terminations.map((m: any, i: number) => (
                  <li key={i} className="flex justify-between border-b py-1">
                    <span>{m.name || "Unknown"}</span>
                    <span className="text-slate-500 font-mono">{m.id}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {report.changes.length > 0 && (
            <div>
              <h4 className="font-bold text-slate-700 mb-2">Changes</h4>
              <ul className="text-sm space-y-1">
                {report.changes.map((m: any, i: number) => (
                  <li key={i} className="flex justify-between border-b py-1">
                    <span>{m.name || "Unknown"}</span>
                    <span className="text-slate-500 font-mono">{m.id}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}