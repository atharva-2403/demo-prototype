from fastapi.testclient import TestClient
from main import app
import os

client = TestClient(app)

def get_sample_path(filename):
    return os.path.join(os.path.dirname(__file__), "sample_files", filename)

def test_reconcile_837_835():
    with open(get_sample_path("valid_837p.edi"), "rb") as f837, \
         open(get_sample_path("sample_835.edi"), "rb") as f835:
        
        response = client.post("/api/reconcile", files={
            "file_837": ("valid_837p.edi", f837, "text/plain"),
            "file_835": ("sample_835.edi", f835, "text/plain")
        })
        
    assert response.status_code == 200
    data = response.json()
    assert data["total_claims"] == 1
    assert data["matched_claims"] == 1
    # Check discrepancy calculation
    details = data["details"][0]
    assert details["claim_id"] == "PAT001"
    assert details["billed_amount"] == 350.0
    assert details["paid_amount"] == 100.0
    
    # Adjustments sum to 250 in the sample 835 file (250 PR + 100 PR + 150 PR = 500, wait, let's verify math)
    # Actually, in our dummy 835: 
    # CLP is: CLP*PAT001*1*350*100*250
    # CAS*PR*1*250
    # CAS*PR*1*100
    # CAS*PR*1*150
    # Total CAS amount = 500.
    # Billed 350 - Paid 100 - Adj 500 = 350 - 600 = -250.
    # We should detect a discrepancy because it's not balanced.
    
    assert details["reconciliation_difference"] == 250.0
    assert not details["is_balanced"]
    assert len(data["discrepancies"]) == 1