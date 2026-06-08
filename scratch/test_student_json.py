import sys
import os
from app import app

def test_student_json():
    print("Starting Student JSON Endpoint validation...")
    client = app.test_client()

    # Create dummy base64 photo content
    # "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    dummy_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    payload = {
        "name": "Jane Student",
        "email": "jane@example.com",
        "photo": dummy_base64
    }

    print("Posting student JSON payload...")
    response = client.post('/api/legacy/students', json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Body: {response.json}")
    
    assert response.status_code == 201, "Failed to create student via JSON payload"
    data = response.json
    assert data.get("name") == "Jane Student", "Name mismatch"
    assert data.get("email") == "jane@example.com", "Email mismatch"
    assert data.get("photo").startswith("student_"), "Saved photo filename mismatch"

    # Cleanup the saved file
    saved_filename = data.get("photo")
    saved_path = os.path.join("uploads", saved_filename)
    if os.path.exists(saved_path):
        os.remove(saved_path)
        print("SUCCESS: Decoded base64 file cleaned up from uploads directory.")

    print("\nSTUDENT JSON PAYLOAD VERIFICATION PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_student_json()
