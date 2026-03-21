from tests.test_delta import create_834
from parser.state_machine import parse_edi
from routes.delta import extract_members

old_edi = create_834([("M1", "SMITH", "021")])
new_edi = create_834([("M1", "SMITH", "021"), ("M2", "DOE", "021")])

o = extract_members(parse_edi(old_edi).loops)
n = extract_members(parse_edi(new_edi).loops)
print("OLD M1:", repr(o["M1"]["raw_data"]))
print("NEW M1:", repr(n["M1"]["raw_data"]))
