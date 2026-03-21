from fastapi.testclient import TestClient
import os
import sys

# Add parent dir to path so we can import main
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app

client = TestClient(app)

def get_sample_path(filename):
    return os.path.join(os.path.dirname(__file__), "sample_files", filename)

def run_demo():
    print("--- TASK 10.4 DEMO REHEARSAL ---")
    
    # 1. Upload valid_837p.edi
    with open(get_sample_path("valid_837p.edi"), "rb") as f:
        res1 = client.post("/api/upload", files={"file": ("valid_837p.edi", f, "text/plain")})
    parsed1 = res1.json()
    val_res1 = client.post("/api/validate", json=parsed1).json()
    print(f"valid_837p.edi: is_valid={val_res1['is_valid']}, errors={val_res1['error_count']}")

    # 2. Upload malformed_837i.edi
    with open(get_sample_path("malformed_837i.edi"), "rb") as f:
        res2 = client.post("/api/upload", files={"file": ("malformed_837i.edi", f, "text/plain")})
    parsed2 = res2.json()
    val_res2 = client.post("/api/validate", json=parsed2).json()
    print(f"malformed_837i.edi: is_valid={val_res2['is_valid']}, errors={val_res2['error_count']}")
    print("Errors:")
    for e in val_res2['errors']:
        print(f"  - {e['error_code']}: {e['plain_english']}")

    # 3. Upload sample_835.edi
    with open(get_sample_path("sample_835.edi"), "rb") as f:
        res3 = client.post("/api/upload", files={"file": ("sample_835.edi", f, "text/plain")})
    parsed3 = res3.json()
    val_res3 = client.post("/api/validate", json=parsed3).json()
    print(f"sample_835.edi: transaction_type={parsed3['transaction_type']}")

    # 4. Upload sample_834.edi
    with open(get_sample_path("sample_834.edi"), "rb") as f:
        res4 = client.post("/api/upload", files={"file": ("sample_834.edi", f, "text/plain")})
    parsed4 = res4.json()
    val_res4 = client.post("/api/validate", json=parsed4).json()
    print(f"sample_834.edi: transaction_type={parsed4['transaction_type']}")

    # 5. AI Chat Questions on malformed_837i.edi
    # Since ANTHROPIC_API_KEY might not be set or we might want to avoid actual API calls in the demo rehearsal script if not explicitly provided,
    # we will just execute the function and catch the 'Error: ANTHROPIC_API_KEY not configured' if so.
    # We will pass dummy context to trigger it.
    
    questions = [
        "Why was this claim rejected?",
        "What does CLM_AMOUNT_MISMATCH mean and how do I fix it?",
        "Which line number has the invalid NPI?"
    ]
    for q in questions:
        print(f"\nQ: {q}")
        chat_req = {
            "question": q,
            "parsed_edi": parsed2,
            "validation": val_res2,
            "conversation_history": []
        }
        chat_res = client.post("/api/chat", json=chat_req).json()
        print(f"A: {chat_res['response'][:100]}...")

if __name__ == "__main__":
    run_demo()
