import { useCallback, useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadFile, uploadDelta, uploadReconcile, preflightCheck, validateEDI } from '../api/client';

type Mode = 'standard' | 'delta' | 'reconcile';

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

  const handlePreflight = async (file: File) => {
    try {
      return await preflightCheck(file);
    } catch (e) {
      console.error("Preflight failed", e);
      return undefined;
    }
  };

  const onDrop1 = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    const file = acceptedFiles[0];
    const preflight = await handlePreflight(file);
    setFile1({ file, preflight });
  }, []);

  const onDrop2 = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    const file = acceptedFiles[0];
    const preflight = await handlePreflight(file);
    setFile2({ file, preflight });
  }, []);

  const { getRootProps: getRoot1, getInputProps: getInput1, isDragActive: isDragActive1 } = useDropzone({ onDrop: onDrop1, maxFiles: 1 });
  const { getRootProps: getRoot2, getInputProps: getInput2, isDragActive: isDragActive2 } = useDropzone({ onDrop: onDrop2, maxFiles: 1 });

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
            // Delta results usually handled differently, but we'll pass to onUploadSuccess 
            // Assuming onUploadSuccess can handle delta response
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
      }
    } catch (e) {
      alert("Error processing files. Please ensure the backend is running.");
      setLoading(false);
    }
  };

  const clearFiles = () => {
    setFile1(null);
    setFile2(null);
  };

  useEffect(() => {
    clearFiles();
  }, [mode]);

  const canProcess = (mode === 'standard' && file1) || (mode !== 'standard' && file1 && file2);

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] p-8 bg-slate-50 relative">
      {loading && (
        <div className="absolute inset-0 bg-white/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center rounded-xl">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-4"></div>
          <p className="text-2xl text-slate-800 font-semibold tracking-wide animate-pulse">{statusText}</p>
        </div>
      )}

      <div className="max-w-4xl w-full bg-white rounded-2xl shadow-xl overflow-hidden border border-slate-200">
        
        <div className="bg-slate-900 p-6 text-white text-center">
          <h2 className="text-3xl font-extrabold tracking-tight">Mission Control</h2>
          <p className="text-slate-400 mt-2 font-medium">Select your operation mode and upload X12 EDI files</p>
        </div>

        <div className="p-6 bg-slate-100 border-b border-slate-200 flex justify-center gap-4">
          {(['standard', 'delta', 'reconcile'] as Mode[]).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-6 py-3 rounded-lg font-semibold transition-all duration-200 shadow-sm ${
                mode === m 
                  ? 'bg-blue-600 text-white shadow-blue-500/30 scale-105' 
                  : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200 hover:border-slate-300'
              }`}
            >
              {m === 'standard' && 'Standard Parse'}
              {m === 'delta' && '834 Delta Report'}
              {m === 'reconcile' && 'Reconciliation'}
            </button>
          ))}
        </div>

        <div className="p-8 flex flex-col gap-8">
          <div className="flex gap-6 w-full">
            
            {/* Primary Target Zone */}
            <div 
              {...getRoot1()} 
              className={`flex-1 min-h-[250px] border-4 border-dashed rounded-xl p-8 flex flex-col items-center justify-center transition-all duration-300 cursor-pointer relative overflow-hidden group
                ${isDragActive1 ? 'border-blue-500 bg-blue-50' : 'border-slate-300 bg-slate-50 hover:border-blue-400 hover:bg-slate-100'}
                ${file1 ? 'border-solid border-blue-500 bg-blue-50/50' : ''}
              `}
            >
              <input {...getInput1()} />
              {file1 ? (
                <div className="text-center z-10">
                  <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm">
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinelinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                  </div>
                  <p className="font-bold text-slate-700 text-lg">{file1.file.name}</p>
                  {file1.preflight && (
                    <div className="mt-4 flex flex-wrap gap-2 justify-center">
                      <span className="px-3 py-1 bg-blue-600 text-white text-xs font-bold rounded-full shadow-sm">
                        Type: {file1.preflight.edi_type}
                      </span>
                      <span className="px-3 py-1 bg-slate-700 text-white text-xs font-bold rounded-full shadow-sm">
                        {file1.preflight.segment_count} Segments
                      </span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center z-10 group-hover:scale-105 transition-transform">
                  <div className="w-16 h-16 bg-white border border-slate-200 text-slate-400 rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm group-hover:text-blue-500">
                    <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinelinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
                  </div>
                  <p className="text-xl font-bold text-slate-600">
                    {mode === 'reconcile' ? 'Upload 837 Claim' : mode === 'delta' ? 'Upload Current 834' : 'Upload EDI File'}
                  </p>
                  <p className="text-slate-500 mt-2">Drag & Drop or Click</p>
                </div>
              )}
            </div>

            {/* Secondary Comparison Zone */}
            {mode !== 'standard' && (
              <div 
                {...getRoot2()} 
                className={`flex-1 min-h-[250px] border-4 border-dashed rounded-xl p-8 flex flex-col items-center justify-center transition-all duration-300 cursor-pointer relative overflow-hidden group
                  ${mode === 'reconcile' 
                    ? (isDragActive2 ? 'border-emerald-500 bg-emerald-50' : 'border-slate-300 bg-slate-50 hover:border-emerald-400 hover:bg-slate-100')
                    : (isDragActive2 ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 bg-slate-50 hover:border-indigo-400 hover:bg-slate-100')
                  }
                  ${file2 && mode === 'reconcile' ? 'border-solid border-emerald-500 bg-emerald-50/50' : ''}
                  ${file2 && mode === 'delta' ? 'border-solid border-indigo-500 bg-indigo-50/50' : ''}
                `}
              >
                <input {...getInput2()} />
                {file2 ? (
                  <div className="text-center z-10">
                    <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm
                      ${mode === 'reconcile' ? 'bg-emerald-100 text-emerald-600' : 'bg-indigo-100 text-indigo-600'}`}>
                      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinelinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    </div>
                    <p className="font-bold text-slate-700 text-lg">{file2.file.name}</p>
                    {file2.preflight && (
                      <div className="mt-4 flex flex-wrap gap-2 justify-center">
                        <span className={`px-3 py-1 text-white text-xs font-bold rounded-full shadow-sm
                          ${mode === 'reconcile' ? 'bg-emerald-600' : 'bg-indigo-600'}`}>
                          Type: {file2.preflight.edi_type}
                        </span>
                        <span className="px-3 py-1 bg-slate-700 text-white text-xs font-bold rounded-full shadow-sm">
                          {file2.preflight.segment_count} Segments
                        </span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center z-10 group-hover:scale-105 transition-transform">
                    <div className={`w-16 h-16 bg-white border border-slate-200 rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm
                      ${mode === 'reconcile' ? 'text-slate-400 group-hover:text-emerald-500' : 'text-slate-400 group-hover:text-indigo-500'}
                    `}>
                      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinelinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
                    </div>
                    <p className="text-xl font-bold text-slate-600">
                      {mode === 'reconcile' ? 'Upload 835 Remittance' : 'Upload Previous 834'}
                    </p>
                    <p className="text-slate-500 mt-2">Drag & Drop or Click</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {canProcess && (
            <div className="flex justify-center mt-4">
              <button
                onClick={processFiles}
                className="bg-slate-900 hover:bg-slate-800 text-white px-10 py-4 rounded-xl font-bold text-lg shadow-lg hover:shadow-xl transition-all hover:-translate-y-1 w-full max-w-sm flex items-center justify-center gap-3"
              >
                <span>Process Files</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinelinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}