import pytest
from fastapi.testclient import TestClient
from main import app
import os

client = TestClient(app)

def create_837(dos, mid):
    # Minimal 837P wrapper
    lines = [
        "ISA*00*          *00*          *ZZ*SENDER       *ZZ*RECEIVER   *230115*1200*^*00501*000000001*0*P*:",
        "GS*HC*SENDER*RECEIVER*20230115*1200*1*X*005010X222A1",
        "ST*837*0001",
        "BHT*0019*00*BATCH001*20230115*1200*CH",
        "HL*1**20*1",
        "HL*2*1*22*0",
        f"NM1*IL*1*LAST*FIRST****MI*{mid}",
        "CLM*CLAIM1*100***11:B:1*Y*A*Y*I",
        f"DTP*472*D8*{dos}",
        "SE*10*0001",
        "GE*1*1",
        "IEA*1*000000001"
    ]
    return "~".join(lines) + "~"

def create_834_el(mid, start_date, end_date=None, status="021"):
    lines = [
        "ISA*00*          *00*          *ZZ*SENDER       *ZZ*RECEIVER   *230115*1200*^*00501*000000001*0*P*:",
        "GS*BE*SENDER*RECEIVER*20230115*1200*1*X*005010X220A1",
        "ST*834*0001",
        "BGN*00*1*20230115*1200****RX",
        f"INS*Y*18*{status}*XN*A",
        f"REF*0F*{mid}",
        "HD*021**HE",
        f"DTP*348*D8*{start_date}"
    ]
    if end_date:
        lines.append(f"DTP*349*D8*{end_date}")
        
    lines.extend([
        "SE*10*0001",
        "GE*1*1",
        "IEA*1*000000001"
    ])
    return "~".join(lines) + "~"

@pytest.mark.parametrize("dos, enr_start, enr_end, enr_status, expected_eligible", [
    ("20230601", "20230101", None, "021", True),         # Perfect match (active)
    ("20221231", "20230101", None, "021", False),        # Claim before coverage
    ("20230601", "20230101", "20230531", "024", False),  # Claim 1 day after termination
    ("20230531", "20230101", "20230531", "024", True),   # Claim on last day of coverage
    ("INVALID", "20230101", None, "021", False),         # Malformed date format
])
def test_eligibility_scenarios(dos, enr_start, enr_end, enr_status, expected_eligible):
    claim_edi = create_837(dos, "MEMBER1")
    enr_edi = create_834_el("MEMBER1", enr_start, enr_end, enr_status)
    
    res = client.post("/api/eligibility", files={
        "claim_file": ("claim.edi", claim_edi, "text/plain"),
        "enrollment_file": ("enroll.edi", enr_edi, "text/plain")
    })
    
    assert res.status_code == 200
    data = res.json()
    if expected_eligible:
        assert data["eligible_claims"] == 1
        assert data["ineligible_claims"] == 0
    else:
        assert data["eligible_claims"] == 0
        assert data["ineligible_claims"] == 1

def test_missing_member():
    claim_edi = create_837("20230601", "MISSING_MEM")
    enr_edi = create_834_el("MEMBER1", "20230101")
    
    res = client.post("/api/eligibility", files={
        "claim_file": ("claim.edi", claim_edi, "text/plain"),
        "enrollment_file": ("enroll.edi", enr_edi, "text/plain")
    })
    data = res.json()
    assert data["ineligible_claims"] == 1
    assert data["mismatches"][0]["reason"] == "Member not found in enrollment file"

def test_missing_loops():
    claim_edi = "ISA*00*          *00*          *ZZ*SENDER       *ZZ*RECEIVER   *230115*1200*^*00501*000000001*0*P*:~GS*HC*SENDER*RECEIVER*20230115*1200*1*X*005010X222A1~ST*837*0001~SE*1*0001~GE*1*1~IEA*1*0~"
    enr_edi = create_834_el("MEMBER1", "20230101")
    
    res = client.post("/api/eligibility", files={
        "claim_file": ("claim.edi", claim_edi, "text/plain"),
        "enrollment_file": ("enroll.edi", enr_edi, "text/plain")
    })
    data = res.json()
    assert data["total_claims_checked"] == 0

def test_zero_members():
    claim_edi = create_837("20230601", "MEMBER1")
    enr_edi = "ISA*00*          *00*          *ZZ*SENDER       *ZZ*RECEIVER   *230115*1200*^*00501*000000001*0*P*:~GS*BE*SENDER*RECEIVER*20230115*1200*1*X*005010X220A1~ST*834*0001~SE*1*0001~GE*1*1~IEA*1*0~"
    
    res = client.post("/api/eligibility", files={
        "claim_file": ("claim.edi", claim_edi, "text/plain"),
        "enrollment_file": ("enroll.edi", enr_edi, "text/plain")
    })
    data = res.json()
    assert data["ineligible_claims"] == 1