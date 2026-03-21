import os
import pytest
from parser.state_machine import parse_edi

def read_sample(filename):
    path = os.path.join(os.path.dirname(__file__), "sample_files", filename)
    with open(path, "r") as f:
        return f.read()

def test_parses_valid_837p():
    content = read_sample("valid_837p.edi")
    parsed = parse_edi(content)
    assert parsed.transaction_type == "837P"
    assert parsed.sender_id == "SENDERID"
    clm_segs = [s for s in parsed.raw_segments if s.id == "CLM"]
    assert len(clm_segs) == 1
    assert clm_segs[0].loop_id == "2300"

def test_parses_malformed_837i_without_crashing():
    content = read_sample("malformed_837i.edi")
    parsed = parse_edi(content)
    assert parsed.transaction_type == "837I"
    assert len(parsed.raw_segments) > 0
    clm_segs = [s for s in parsed.raw_segments if s.id == "CLM"]
    assert len(clm_segs) > 0
    assert clm_segs[0].loop_id == "2300"

def test_parses_sample_835():
    content = read_sample("sample_835.edi")
    parsed = parse_edi(content)
    assert parsed.transaction_type == "835"
    clp_segs = [s for s in parsed.raw_segments if s.id == "CLP"]
    assert clp_segs[0].loop_id == "2100"

def test_parses_sample_834():
    content = read_sample("sample_834.edi")
    parsed = parse_edi(content)
    assert parsed.transaction_type == "834"
    ins_segs = [s for s in parsed.raw_segments if s.id == "INS"]
    assert ins_segs[0].loop_id == "2000"

def test_composite_elements_split_correctly():
    content = read_sample("valid_837p.edi")
    parsed = parse_edi(content)
    clm_segs = [s for s in parsed.raw_segments if s.id == "CLM"]
    clm = clm_segs[0]
    subelements = [e for e in clm.elements if e.raw_key.startswith("CLM_05")]
    assert len(subelements) == 3
    assert subelements[0].value == "11"
    assert subelements[1].value == "B"
    assert subelements[2].value == "1"