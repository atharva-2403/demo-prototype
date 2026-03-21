import pytest
from fastapi.testclient import TestClient
from main import app
import os

client = TestClient(app)

def create_834(members_data):
    # minimal 834 wrapper
    lines = [
        "ISA*00*          *00*          *ZZ*SENDERID       *ZZ*RECEIVERID     *230115*1200*^*00501*000000001*0*P*:",
        "GS*BE*SENDERID*RECEIVERID*20230115*1200*1*X*005010X220A1",
        "ST*834*0001",
        "BGN*00*1*20230115*1200****RX"
    ]
    for mid, name, ins03 in members_data:
        lines.append(f"INS*Y*18*{ins03}*XN*A")
        lines.append(f"REF*0F*{mid}")
        lines.append(f"NM1*IL*1*{name}*FIRSTNAME****34*123456789")
        lines.append(f"HD*{ins03}**HE")
        lines.append("DTP*348*D8*20230101")
    
    lines.extend([
        "SE*11*0001",
        "GE*1*1",
        "IEA*1*000000001"
    ])
    return "~".join(lines) + "~"

@pytest.mark.parametrize("old_data, new_data, expected_add, expected_term, expected_change", [
    # Perfect match
    ([("M1", "SMITH", "021")], [("M1", "SMITH", "021")], 0, 0, 0),
    # Addition
    ([("M1", "SMITH", "021")], [("M1", "SMITH", "021"), ("M2", "DOE", "021")], 1, 0, 0),
    # Termination (missing in new)
    ([("M1", "SMITH", "021")], [], 0, 1, 0),
    # Change (data modified)
    ([("M1", "SMITH", "021")], [("M1", "SMITH-JONES", "001")], 0, 0, 1),
    # Zero members
    ([], [], 0, 0, 0),
])
def test_delta_scenarios(old_data, new_data, expected_add, expected_term, expected_change):
    old_edi = create_834(old_data)
    new_edi = create_834(new_data)
    
    res = client.post("/api/delta", files={
        "old_file": ("old.edi", old_edi, "text/plain"),
        "new_file": ("new.edi", new_edi, "text/plain")
    })
    
    assert res.status_code == 200
    data = res.json()
    assert len(data["additions"]) == expected_add
    assert len(data["terminations"]) == expected_term
    assert len(data["changes"]) == expected_change