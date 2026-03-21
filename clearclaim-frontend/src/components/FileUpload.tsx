import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadFile, validateEDI } from '../api/client';

export default function FileUpload({ onUploadSuccess }: any) {
  const [loading, setLoading] = useState(false);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;
    setLoading(true);
    try {
      const parsed = await uploadFile(acceptedFiles[0]);
      const validation = await validateEDI(parsed);
      onUploadSuccess(parsed, validation);
    } catch (e) {
      alert("Error processing file. Please ensure the backend is running.");
    } finally {
      setLoading(false);
    }
  }, [onUploadSuccess]);

  const { getRootProps, getInputProps } = useDropzone({ onDrop });

  return (
    <div className="flex items-center justify-center h-screen">
      <div {...getRootProps()} className="border-4 border-dashed border-slate-300 p-20 bg-white hover:bg-slate-50 cursor-pointer rounded-lg text-center shadow-sm">
        <input {...getInputProps()} />
        {loading ? (
          <p className="text-xl text-slate-600 font-medium">Parsing and Validating EDI...</p>
        ) : (
          <div>
            <p className="text-2xl font-bold text-slate-700 mb-2">ClearClaim AI</p>
            <p className="text-slate-500">Drag and drop an X12 file (837, 835, 834) here, or click to select</p>
          </div>
        )}
      </div>
    </div>
  );
}