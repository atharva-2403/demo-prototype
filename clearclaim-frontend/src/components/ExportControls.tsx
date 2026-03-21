import type { ParsedEDI, ValidationResult } from '../types/edi';
import axios from 'axios';

export default function ExportControls({ parsed, validation }: { parsed: ParsedEDI, validation: ValidationResult }) {
  const handleExportPDF = async () => {
    try {
      const res = await axios.post('http://localhost:8000/api/export/pdf', { parsed, validation }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${parsed.file_name}_report.pdf`);
      document.body.appendChild(link);
      link.click();
    } catch(e) {
      alert("Failed to export PDF");
    }
  };

  return (
    <div className="flex gap-4">
      <button onClick={handleExportPDF} className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 font-bold text-sm shadow">
        Export PDF Report
      </button>
    </div>
  );
}