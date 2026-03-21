import sys
import os
sys.path.insert(0, os.path.abspath('clearclaim-backend'))
from parser.edi_reader import EDIReader

with open("clearclaim-backend/tests/sample_files/malformed_837i.edi") as f:
    content = f.read()

reader = EDIReader(content)
segs = reader.get_segments()
print("SEGS BHT:")
for seg in segs:
    if "BHT" in seg:
        els = [e.strip() for e in seg.split(reader.element_delimiter)]
        print(els)
print("Detected:", reader.detect_transaction_type(segs))
