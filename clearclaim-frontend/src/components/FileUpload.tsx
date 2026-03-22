import { useState, useEffect } from 'react';
import { uploadFile, uploadDelta, uploadReconcile, uploadEligibility, preflightCheck, validateEDI } from '../api/client';

type Mode = 'standard' | 'delta' | 'reconcile' | 'eligibility';

interface FileData {
  file: File;
  preflight?: {
    file_name: string;
    segment_count: number;
    edi_type: string;
  };
}

export default function FileUpload({ onUploadSuccess }: any) {
  const [mode, setMode] = useState<Mode>('standard');
  const [file1, setFile1] = useState<FileData | null>(null);
  const [file2, setFile2] = useState<FileData | null>(null);
  
  const [loading, setLoading] = useState(false);
  const [statusText, setStatusText] = useState('');
  
  const [isDragActive1, setIsDragActive1] = useState(false);
  const [isDragActive2, setIsDragActive2] = useState(false);

  const handlePreflight = async (file: File) => {
    try {
      return await preflightCheck(file);
    } catch (e) {
      console.error("Preflight failed", e);
      return undefined;
    }
  };

  const processFileSelection = async (fileList: FileList, isZone2: boolean = false) => {
    const file = fileList[0];
    if (!file) return;
    const preflight = await handlePreflight(file);
    if (isZone2) {
      setFile2({ file, preflight });
    } else {
      setFile1({ file, preflight });
    }
  };

  // Drag-and-Drop Handlers for Zone 1
  const handleDragOver1 = (e: React.DragEvent) => { e.preventDefault(); setIsDragActive1(true); };
  const handleDragLeave1 = (e: React.DragEvent) => { e.preventDefault(); setIsDragActive1(false); };
  const handleDrop1 = async (e: React.DragEvent) => {
    e.preventDefault(); 
    setIsDragActive1(false);
    if (e.dataTransfer.files?.length) await processFileSelection(e.dataTransfer.files, false);
  };

  // Drag-and-Drop Handlers for Zone 2
  const handleDragOver2 = (e: React.DragEvent) => { e.preventDefault(); setIsDragActive2(true); };
  const handleDragLeave2 = (e: React.DragEvent) => { e.preventDefault(); setIsDragActive2(false); };
  const handleDrop2 = async (e: React.DragEvent) => {
    e.preventDefault(); 
    setIsDragActive2(false);
    if (e.dataTransfer.files?.length) await processFileSelection(e.dataTransfer.files, true);
  };

  // HTML Input Linkage
  const handleChange1 = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) await processFileSelection(e.target.files, false);
    e.target.value = '';
  };

  const handleChange2 = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) await processFileSelection(e.target.files, true);
    e.target.value = '';
  };

  const simulateProgress = (messages: string[], onComplete: () => void) => {
    let i = 0;
    setStatusText(messages[0]);
    const interval = setInterval(() => {
      i++;
      if (i < messages.length) {
        setStatusText(messages[i]);
      } else {
        clearInterval(interval);
        onComplete();
      }
    }, 800);
  };

  const processFiles = async () => {
    setLoading(true);
    try {
      if (mode === 'standard' && file1) {
        simulateProgress(
          ['Reading ISA Headers...', 'Parsing Segments...', 'Verifying NPI Checksums...', 'Running Rules Engine...'],
          async () => {
            const parsed = await uploadFile(file1.file);
            const validation = await validateEDI(parsed);
            onUploadSuccess(parsed, validation);
            setLoading(false);
          }
        );
      } else if (mode === 'delta' && file1 && file2) {
        simulateProgress(
          ['Reading 834 Files...', 'Aligning Member Loops...', 'Comparing Enrollment Deltas...', 'Generating Report...'],
          async () => {
            const result = await uploadDelta(file1.file, file2.file);
            onUploadSuccess(result, null, 'delta');
            setLoading(false);
          }
        );
      } else if (mode === 'reconcile' && file1 && file2) {
        simulateProgress(
          ['Reading 837 & 835 Files...', 'Matching Claims to Payments...', 'Identifying Denials...', 'Reconciling Balances...'],
          async () => {
            const result = await uploadReconcile(file1.file, file2.file);
            onUploadSuccess(result, null, 'reconcile');
            setLoading(false);
          }
        );
      } else if (mode === 'eligibility' && file1 && file2) {
        simulateProgress(
          ['Reading 837 Claim...', 'Reading 834 Enrollment...', 'Cross-referencing Member IDs...', 'Checking Active Coverage...'],
          async () => {
            const result = await uploadEligibility(file1.file, file2.file);
            onUploadSuccess(result, null, 'eligibility');
            setLoading(false);
          }
        );
      }
    } catch (e) {
      alert("Error processing files. Please ensure the backend is running.");
      setLoading(false);
    }
  };

  useEffect(() => {
    setFile1(null);
    setFile2(null);
  }, [mode]);

  const canProcess = (mode === 'standard' && file1) || (mode !== 'standard' && file1 && file2);

  const getZone1Labels = () => {
    if (mode === 'delta') return { title: 'Upload Current 834', color: 'blue' };
    if (mode === 'reconcile') return { title: 'Upload 837 Claim', color: 'blue' };
    if (mode === 'eligibility') return { title: 'Upload 837 Claim', color: 'blue' };
    return { title: 'Upload EDI File', color: 'blue' };
  };

  const getZone2Labels = () => {
    if (mode === 'delta') return { title: 'Upload Previous 834', color: 'green' };
    if (mode === 'eligibility') return { title: 'Upload 834 Enrollment', color: 'green' };
    return { title: 'Upload 835 Remittance', color: 'green' };
  };

  const z1 = getZone1Labels();
  const z2 = getZone2Labels();

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] py-4 bg-slate-50 relative">
      {loading && (
        <div className="absolute inset-0 bg-white/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center rounded-xl">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-4"></div>
          <p className="text-2xl text-slate-800 font-semibold tracking-wide animate-pulse">{statusText}</p>
        </div>
      )}

      <div className="max-w-5xl w-full bg-white rounded-2xl shadow-xl overflow-hidden border border-slate-200 relative z-10">
        
        <div className="bg-slate-900 px-6 py-4 text-white text-center">
          <h2 className="text-2xl font-extrabold tracking-tight">Mission Control</h2>
          <p className="text-slate-400 text-sm mt-1 font-medium">Select your operation mode and upload X12 EDI files</p>
        </div>

        <div className="p-4 bg-slate-100 border-b border-slate-200 flex flex-wrap justify-center gap-4">
          {(['standard', 'delta', 'reconcile', 'eligibility'] as Mode[]).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-5 py-2 rounded-lg font-semibold transition-all duration-200 shadow-sm text-sm ${
                mode === m 
                  ? 'bg-blue-600 text-white shadow-blue-500/30 scale-105' 
                  : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200 hover:border-slate-300'
              }`}
            >
              {m === 'standard' && 'Standard Parse'}
              {m === 'delta' && '834 Delta Report'}
              {m === 'reconcile' && 'Reconciliation'}
              {m === 'eligibility' && 'Eligibility Check'}
            </button>
          ))}
        </div>

        <div className="p-6 flex flex-col gap-6">
          <div className={`flex flex-col md:flex-row items-center justify-center gap-4 ${mode === 'standard' ? 'max-w-2xl mx-auto w-full' : 'w-full'}`}>
            
            {/* Target Zone 1 */}
            <label 
              htmlFor="edi-upload-1"
              onDragOver={handleDragOver1}
              onDragLeave={handleDragLeave1}
              onDrop={handleDrop1}
              className={`flex-1 w-full min-h-[200px] border-4 border-dashed rounded-xl p-6 flex flex-col items-center justify-center transition-all duration-300 cursor-pointer relative overflow-hidden group
                ${isDragActive1 ? `border-${z1.color}-500 bg-${z1.color}-50` : `border-slate-300 bg-slate-50 hover:border-${z1.color}-400 hover:bg-slate-100`}
                ${file1 ? `border-solid border-${z1.color}-500 bg-${z1.color}-50/50` : ''}
              `}
            >
              <input id="edi-upload-1" type="file" onChange={handleChange1} className="hidden" accept=".edi,.txt" />
              
              {file1 ? (
                <div className="text-center z-10 w-full" onClick={(e) => e.stopPropagation()}>
                  <button onClick={(e) => { e.preventDefault(); setFile1(null); }} className="absolute top-3 right-3 text-slate-400 hover:text-red-500 p-1">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                  </button>
                  <div className={`w-12 h-12 bg-${z1.color}-100 text-${z1.color}-600 rounded-full flex items-center justify-center mx-auto mb-3 shadow-sm`}>
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                  </div>
                  <p className="font-bold text-slate-700 text-base truncate px-4" title={file1.file.name}>{file1.file.name}</p>
                  {file1.preflight && (
                    <div className="mt-3 flex flex-wrap gap-2 justify-center">
                      <span className={`px-2 py-1 bg-${z1.color}-600 text-white text-xs font-bold rounded shadow-sm`}>Type: {file1.preflight.edi_type}</span>
                      <span className="px-2 py-1 bg-slate-700 text-white text-xs font-bold rounded shadow-sm">{file1.preflight.segment_count} Segments</span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center z-10 group-hover:scale-105 transition-transform">
                  <div className={`w-12 h-12 bg-white border border-slate-200 text-slate-400 rounded-full flex items-center justify-center mx-auto mb-3 shadow-sm group-hover:text-${z1.color}-500`}>
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
                  </div>
                  <p className="text-lg font-bold text-slate-600">{z1.title}</p>
                  <p className="text-slate-400 text-sm mt-1">Drag & Drop or Click</p>
                </div>
              )}
            </label>

            {/* Comparison Cues and Zone 2 */}
            {mode !== 'standard' && (
              <>
                <div className="flex-shrink-0 z-20 -mx-4 bg-white rounded-full p-2 shadow-sm border border-slate-200">
                  <div className="w-8 h-8 bg-slate-100 text-slate-500 rounded-full flex items-center justify-center">
                    {(mode === 'reconcile' || mode === 'eligibility') ? (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"></path></svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"></path></svg>
                    )}
                  </div>
                </div>

                <label 
                  htmlFor="edi-upload-2"
                  onDragOver={handleDragOver2}
                  onDragLeave={handleDragLeave2}
                  onDrop={handleDrop2}
                  className={`flex-1 w-full min-h-[200px] border-4 border-dashed rounded-xl p-6 flex flex-col items-center justify-center transition-all duration-300 cursor-pointer relative overflow-hidden group
                    ${isDragActive2 ? `border-${z2.color}-500 bg-${z2.color}-50` : `border-slate-300 bg-slate-50 hover:border-${z2.color}-400 hover:bg-slate-100`}
                    ${file2 ? `border-solid border-${z2.color}-500 bg-${z2.color}-50/50` : ''}
                  `}
                >
                  <input id="edi-upload-2" type="file" onChange={handleChange2} className="hidden" accept=".edi,.txt" />
                  
                  {file2 ? (
                    <div className="text-center z-10 w-full" onClick={(e) => e.stopPropagation()}>
                      <button onClick={(e) => { e.preventDefault(); setFile2(null); }} className="absolute top-3 right-3 text-slate-400 hover:text-red-500 p-1">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                      </button>
                      <div className={`w-12 h-12 bg-${z2.color}-100 text-${z2.color}-600 rounded-full flex items-center justify-center mx-auto mb-3 shadow-sm`}>
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                      </div>
                      <p className="font-bold text-slate-700 text-base truncate px-4" title={file2.file.name}>{file2.file.name}</p>
                      {file2.preflight && (
                        <div className="mt-3 flex flex-wrap gap-2 justify-center">
                          <span className={`px-2 py-1 bg-${z2.color}-600 text-white text-xs font-bold rounded shadow-sm`}>Type: {file2.preflight.edi_type}</span>
                          <span className="px-2 py-1 bg-slate-700 text-white text-xs font-bold rounded shadow-sm">{file2.preflight.segment_count} Segments</span>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center z-10 group-hover:scale-105 transition-transform">
                      <div className={`w-12 h-12 bg-white border border-slate-200 text-slate-400 rounded-full flex items-center justify-center mx-auto mb-3 shadow-sm group-hover:text-${z2.color}-500`}>
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
                      </div>
                      <p className="text-lg font-bold text-slate-600">{z2.title}</p>
                      <p className="text-slate-400 text-sm mt-1">Drag & Drop or Click</p>
                    </div>
                  )}
                </label>
              </>
            )}
          </div>

          <div className="flex justify-center mt-2 h-14">
            {canProcess && (
              <button
                onClick={processFiles}
                className="bg-slate-900 hover:bg-slate-800 text-white px-10 rounded-xl font-bold text-lg shadow-lg hover:shadow-xl transition-all hover:-translate-y-1 w-full max-w-sm flex items-center justify-center gap-3 h-full"
              >
                <span>{mode === 'standard' ? 'Parse EDI File' : 'Start Analysis'}</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}