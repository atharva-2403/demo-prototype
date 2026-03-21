import JsonView from '@uiw/react-json-view';
import type { ParsedEDI } from '../types/edi';

export default function SegmentTree({ parsed }: { parsed: ParsedEDI }) {
  return (
    <div className="bg-white p-4 rounded shadow border border-slate-200 max-h-[600px] overflow-auto">
      <h2 className="font-bold text-slate-800 mb-4 border-b pb-2">Segment Tree</h2>
      <JsonView value={parsed.loops} collapsed={2} />
    </div>
  );
}