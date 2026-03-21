import axios from 'axios';
import type { ParsedEDI, ValidationResult } from '../types/edi';

const API_BASE = 'http://localhost:8000/api';

export const uploadFile = async (file: File): Promise<ParsedEDI> => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await axios.post(`${API_BASE}/upload`, formData);
  return res.data;
};

export const validateEDI = async (parsed: ParsedEDI): Promise<ValidationResult> => {
  const res = await axios.post(`${API_BASE}/validate`, parsed);
  return res.data;
};

export const askChat = async (question: string, parsed: ParsedEDI, validation: ValidationResult, history: any[] = [], llm_provider?: string) => {
  const res = await axios.post(`${API_BASE}/chat`, {
    question,
    parsed_edi: parsed,
    validation,
    conversation_history: history,
    llm_provider
  });
  return res.data.response;
};

export const applyFix = async (error: any, parsed: ParsedEDI, fix_value?: string) => {
  const res = await axios.post(`${API_BASE}/fix`, {
    error,
    parsed,
    fix_value
  });
  return res.data;
};