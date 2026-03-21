import type { ParsedEDI, ValidationResult } from '../types/edi';

export default function MetadataBar({ parsed, validation }: { parsed: ParsedEDI, validation: ValidationResult }) {
  return (
    <div className="bg-white p-4 rounded shadow flex justify-between items-center border border-slate-200">
      <div>
        <h2 className="font-bold text-slate-800">{parsed.file_name}</h2>
        <p className="text-sm text-slate-500">Type: {parsed.transaction_type} | Sender: {parsed.sender_id} | Receiver: {parsed.receiver_id}</p>
      </div>
      <div className={`px-4 py-2 rounded font-bold text-white ${validation.is_valid ? 'bg-green-500' : 'bg-red-500'}`}>
        {validation.is_valid ? 'VALID' : `${validation.error_count} ERRORS`}
      </div>
    </div>
  );
}