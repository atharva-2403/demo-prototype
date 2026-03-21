import type { ParsedEDI, ValidationResult } from '../../types/edi';

export const mockParsedEDI: ParsedEDI = {
  file_name: "test.edi",
  transaction_type: "837P",
  sender_id: "SENDER",
  receiver_id: "RECEIVER",
  interchange_date: "230115",
  transaction_set_count: 1,
  delimiter_segment: "~",
  delimiter_element: "*",
  delimiter_subelement: ":",
  loops: [],
  raw_segments: []
};

export const mockValidationResult: ValidationResult = {
  transaction_type: "837P",
  is_valid: false,
  error_count: 1,
  warning_count: 0,
  errors: [
    {
      error_code: "INVALID_NPI",
      severity: "error",
      loop_id: "2010AA",
      segment_id: "NM1",
      element_position: 9,
      raw_value: "1234567890",
      expected: "10-digit Luhn NPI",
      plain_english: "The NPI is invalid.",
      line_number: 8,
      auto_fix_available: false
    }
  ]
};