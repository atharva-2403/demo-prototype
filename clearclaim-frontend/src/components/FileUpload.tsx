import { useState, useEffect } from 'react';
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
  const [files, setFiles] = useState<FileData[]>([]);
  
  const [loading, setLoading] = useState(false);
  const [statusText, setStatusText] = useState('');
  const [isDragActive, setIsDragActive] = useState(false);

  const handlePreflight = async (file: File) => {
    try {
      return await preflightCheck(file);
    } catch (e) {
      console.error("Preflight failed", e);
      return undefined;
    }
  };

  const addFiles = async (fileList: FileList) => {
    const newFiles = Array.from(fileList);
    const processed: FileData[] = [];
    
    for (const file of newFiles) {
      const preflight = await handlePreflight(file);
      processed.push({ file, preflight });
    }

    setFiles(prev => {
      const combined = [...prev, ...processed];
      const maxAllowed = mode === 'standard' ? 1 : 2;
      return combined.slice(0, maxAllowed);
    });
  };

  // Drag-and-Drop Handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault(); // Prevent browser from opening file
    setIsDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault(); // Prevent browser from opening file
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await addFiles(e.dataTransfer.files);
    }
  };

  // HTML Input Linkage
  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      await addFiles(e.target.files);
    }
    // Reset input value so the same file can be selected again if removed
    e.target.value = '';
  };

  const removeFile = (index: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setFiles(prev => prev.filter((_, i) => i !== index));
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
      if (mode === 'standard' && files.length >= 1) {
        simulateProgress(
          ['Reading ISA Headers...', 'Parsing Segments...', 'Verifying NPI Checksums...', 'Running Rules Engine...'],
          async () => {
            const parsed = await uploadFile(files[0].file);
            const validation = await validateEDI(parsed);
            onUploadSuccess(parsed, validation);
            setLoading(false);
          }
        );
      } else if (mode === 'delta' && files.length >= 2) {
        simulateProgress(
          ['Reading 834 Files...', 'Aligning Member Loops...', 'Comparing Enrollment Deltas...', 'Generating Report...'],
          async () => {
            const result = await uploadDelta(files[0].file, files[1].file);
            onUploadSuccess(result, null, 'delta');
            setLoading(false);
          }
        );
      } else if (mode === 'reconcile' && files.length >= 2) {
        simulateProgress(
          ['Reading 837 & 835 Files...', 'Matching Claims to Payments...', 'Identifying Denials...', 'Reconciling Balances...'],
          async () => {
            const result = await uploadReconcile(files[0].file, files[1].file);
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

  useEffect(() => {
    setFiles([]);
  }, [mode]);

  const canProcess = (mode === 'standard' && files.length >= 1) || (mode !== 'standard' && files.length >= 2);

  return (
    <div 
      className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] p-8 bg-slate-50 relative"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {loading && (
        <div className="absolute inset-0 bg-white/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center rounded-xl">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-4"></div>
          <p className="text-2xl text-slate-800 font-semibold tracking-wide animate-pulse">{statusText}</p>
        </div>
      )}

      <div className="max-w-4xl w-full bg-white rounded-2xl shadow-xl overflow-hidden border border-slate-200 relative z-10">
        
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
          
          <label 
            htmlFor="edi-upload"
            className={`w-full min-h-[300px] border-4 border-dashed rounded-xl p-8 flex flex-col items-center justify-center transition-all duration-300 cursor-pointer relative overflow-hidden group
              ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-slate-300 bg-slate-50 hover:border-blue-400 hover:bg-slate-100'}
            `}
          >
            <input 
              id="edi-upload" 
              type="file" 
              onChange={handleChange} 
              multiple={mode !== 'standard'} 
              className="hidden" 
              accept=".edi,.txt"
            />
            
            {files.length === 0 ? (
              <div className="text-center z-10 group-hover:scale-105 transition-transform">
                <div className="w-16 h-16 bg-white border border-slate-200 text-slate-400 rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm group-hover:text-blue-500">
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
                </div>
                <p className="text-xl font-bold text-slate-600">
                  {mode === 'standard' ? 'Upload EDI File' : `Upload ${mode === 'delta' ? '834 files' : '837 & 835 files'}`}
                </p>
                <p className="text-slate-500 mt-2">Drag & Drop or Click here</p>
                {mode !== 'standard' && (
                  <p className="text-sm text-slate-400 mt-1">Requires 2 files</p>
                )}
              </div>
            ) : (
              <div className="w-full flex flex-col gap-4">
                <h3 className="text-lg font-bold text-slate-700 text-center mb-2">Files Selected</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {files.map((fileData, index) => (
                    <div key={index} className="bg-white border border-blue-200 p-4 rounded-xl shadow-sm flex flex-col relative z-20" onClick={(e) => e.stopPropagation()}>
                      <button 
                        onClick={(e) => removeFile(index, e)}
                        className="absolute top-2 right-2 text-slate-400 hover:text-red-500 bg-slate-50 hover:bg-red-50 rounded-full p-1 transition-colors"
                        title="Remove file"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                      </button>
                      
                      <div className="flex items-center gap-3 mb-2 pr-8">
                        <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center shrink-0">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        </div>
                        <p className="font-bold text-slate-700 truncate" title={fileData.file.name}>{fileData.file.name}</p>
                      </div>
                      
                      {fileData.preflight && (
                        <div className="flex flex-wrap gap-2 mt-auto">
                          <span className="px-2 py-1 bg-blue-600 text-white text-xs font-bold rounded shadow-sm">
                            Type: {fileData.preflight.edi_type}
                          </span>
                          <span className="px-2 py-1 bg-slate-700 text-white text-xs font-bold rounded shadow-sm">
                            {fileData.preflight.segment_count} Segments
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                  
                  {mode !== 'standard' && files.length === 1 && (
                    <div className="border-2 border-dashed border-slate-300 rounded-xl flex items-center justify-center p-4 bg-slate-50/50">
                       <p className="text-slate-500 font-medium text-center">Waiting for 2nd file...<br/><span className="text-xs font-normal">Click or drop here</span></p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </label>

          {canProcess && (
            <div className="flex justify-center">
              <button
                onClick={processFiles}
                className="bg-slate-900 hover:bg-slate-800 text-white px-10 py-4 rounded-xl font-bold text-lg shadow-lg hover:shadow-xl transition-all hover:-translate-y-1 w-full max-w-sm flex items-center justify-center gap-3"
              >
                <span>Process Files</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}