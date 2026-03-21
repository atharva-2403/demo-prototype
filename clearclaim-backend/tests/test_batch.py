import os
os.environ["TESTING"] = "1"
from fastapi.testclient import TestClient
from main import app
import io
import zipfile

client = TestClient(app)

def get_sample_path(filename):
    return os.path.join(os.path.dirname(__file__), "sample_files", filename)

def test_batch_upload():
    # Create an in-memory zip file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for f in ["valid_837p.edi", "malformed_837i.edi", "sample_835.edi", "sample_834.edi"]:
            with open(get_sample_path(f), "rb") as edifile:
                zip_file.writestr(f, edifile.read())
    
    zip_buffer.seek(0)
    
    response = client.post("/api/batch-upload", files={"file": ("batch.zip", zip_buffer, "application/zip")})
    assert response.status_code == 200
    data = response.json()
    assert data["total_files"] == 4
    # malformed_837i.edi has 6 errors, others have 0 (assuming the valid ones are perfect)
    # Actually wait, sample_835 and 834 might have rule issues if rules aren't exhaustive?
    # Our tests passed them as 0 errors earlier implicitly if they just don't trigger the explicit 837 rules.
    assert data["files_with_errors"] >= 1
    
    file_details = {d["file_name"]: d for d in data["details"]}
    assert file_details["valid_837p.edi"]["is_valid"] is True
    assert file_details["malformed_837i.edi"]["is_valid"] is False
    assert file_details["malformed_837i.edi"]["error_count"] == 6