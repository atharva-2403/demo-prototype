import { useState } from 'react';
import { askChat } from '../api/client';
import type { ParsedEDI, ValidationResult } from '../types/edi';

export default function AIChatPanel({ parsed, validation }: { parsed: ParsedEDI, validation: ValidationResult }) {
  const [history, setHistory] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const [provider, setProvider] = useState('gemini');

  const handleSend = async () => {
    if (!input.trim()) return;
    const currentQ = input;
    setInput('');
    setHistory(prev => [...prev, { role: 'user', content: currentQ }]);
    setIsThinking(true);
    try {
      const resp = await askChat(currentQ, parsed, validation, history, provider);
      setHistory(prev => [...prev, { role: 'assistant', content: resp }]);
    } catch (e) {
      setHistory(prev => [...prev, { role: 'assistant', content: "Error communicating with AI assistant." }]);
    } finally {
      setIsThinking(false);
    }
  };

  return (
    <div className="bg-white p-4 rounded shadow border border-slate-200 flex flex-col h-[600px]">
      <div className="flex justify-between items-center mb-4 border-b pb-2">
        <h2 className="font-bold text-slate-800">ClearClaim AI Assistant</h2>
        <select
          value={provider}
          onChange={(e) => setProvider(e.target.value)}
          className="border border-slate-300 rounded p-1 text-sm bg-slate-50 text-slate-700 outline-none"
        >
          <option value="gemini">Gemini 2.5 (Google)</option>
          <option value="anthropic">Claude (Anthropic)</option>
          <option value="openai">GPT-4o (OpenAI)</option>
        </select>
      </div>      <div className="flex-1 overflow-y-auto mb-4 space-y-4 pr-2">
        {history.length === 0 && <p className="text-slate-400 text-sm">Ask me why a claim was rejected, how to fix an error, or to summarize this file.</p>}
        {history.map((msg, i) => (
          <div key={i} className={`p-3 rounded-lg ${msg.role === 'user' ? 'bg-blue-50 ml-8' : 'bg-slate-50 mr-8 border'}`}>
            <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
          </div>
        ))}
        {isThinking && (
          <div className="bg-slate-50 p-3 rounded-lg mr-8 border text-slate-500 text-sm">
            AI is thinking...
          </div>
        )}
      </div>
      <div className="flex gap-2">
        <input 
          type="text" 
          value={input} 
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          className="flex-1 border p-2 rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
          placeholder="Ask a question about this file..."
        />
        <button onClick={handleSend} disabled={isThinking || !input.trim()} className="bg-slate-800 text-white px-4 py-2 rounded hover:bg-slate-700 disabled:opacity-50">
          Send
        </button>
      </div>
    </div>
  );
}