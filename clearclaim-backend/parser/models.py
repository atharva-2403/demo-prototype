from pydantic import BaseModel
from typing import List, Optional

class EDIElement(BaseModel):
    position: int
    label: str
    value: str
    raw_key: str

class EDISegment(BaseModel):
    id: str
    loop_id: str
    elements: List[EDIElement]
    raw_line: str
    line_number: int

class EDILoop(BaseModel):
    loop_id: str
    loop_name: str
    segments: List[EDISegment]
    children: List['EDILoop']

class ParsedEDI(BaseModel):
    file_name: str
    transaction_type: str
    sender_id: str
    receiver_id: str
    interchange_date: str
    transaction_set_count: int
    delimiter_segment: str
    delimiter_element: str
    delimiter_subelement: str
    loops: List[EDILoop]
    raw_segments: List[EDISegment]