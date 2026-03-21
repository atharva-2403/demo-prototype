import os
os.environ["TESTING"] = "1"
from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

def get_sample_path(filename):
    return os.path.join(os.path.dirname(__file__), "sample_files", filename)

def test_upload_and_validate_full_pipeline():
    with open(get_sample_path("valid_837p.edi"), "rb") as f:
        response = client.post("/api/upload", files={"file": ("valid_837p.edi", f, "text/plain")})
        
    assert response.status_code == 200
    parsed_edi = response.json()
    assert parsed_edi["transaction_type"] == "837P"
    
    # Validation step
    val_res = client.post("/api/validate", json=parsed_edi)
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["is_valid"] is True
    assert val_data["error_count"] == 0

def test_upload_malformed_837i():
    with open(get_sample_path("malformed_837i.edi"), "rb") as f:
        response = client.post("/api/upload", files={"file": ("malformed_837i.edi", f, "text/plain")})
        
    assert response.status_code == 200
    parsed_edi = response.json()
    assert parsed_edi["transaction_type"] == "837I"
    
    # Validation step
    val_res = client.post("/api/validate", json=parsed_edi)
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["is_valid"] is False
    assert val_data["error_count"] == 6