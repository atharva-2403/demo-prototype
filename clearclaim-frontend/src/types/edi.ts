export interface EDIElement {
  position: number; label: string; value: string; raw_key: string;
}
export interface EDISegment {
  id: string; loop_id: string; elements: EDIElement[];
  raw_line: string; line_number: number;
}
export interface EDILoop {
  loop_id: string; loop_name: string;
  segments: EDISegment[]; children: EDILoop[];
}
export interface ParsedEDI {
  file_name: string; transaction_type: string;
  sender_id: string; receiver_id: string;
  interchange_date: string; transaction_set_count: number;
  loops: EDILoop[]; raw_segments: EDISegment[];
}
export interface ValidationError {
  error_code: string; severity: 'error' | 'warning' | 'info';
  loop_id: string; segment_id: string; element_position: number;
  raw_value?: string; expected?: string; plain_english: string;
  line_number: number; auto_fix_available: boolean; suggested_fix?: string;
}
export interface ValidationResult {
  transaction_type: string; is_valid: boolean;
  error_count: number; warning_count: number;
  errors: ValidationError[];
}