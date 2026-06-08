import sys
import random
from app import app
from extensions import db
from models import User

def test_register_flow():
    print("Starting User Registration validation...")
    client = app.test_client()
    
    # Generate unique username
    username = f"student_{random.randint(1000, 9999)}"
    password = "password123"

    # 1. Register a new user
    print(f"Registering a new user: {username}...")
    resp_reg = client.post('/api/auth/register', json={
        'username': username,
        'password': password
    })
    
    print(f"Status Code: {resp_reg.status_code}")
    print(f"Body: {resp_reg.json}")
    assert resp_reg.status_code == 201, "Registration failed"
    
    data = resp_reg.json
    assert data.get('username') == username, "Username mismatch"
    assert data.get('status') == 'pending', "Status should default to pending"
    assert data.get('type') == 'student', "Type should default to student"
    print("SUCCESS: User registration completed with correct default values (pending, student).")

    # 2. Register same username again (should fail)
    print("\nAttempting to register the same username again...")
    resp_reg_dup = client.post('/api/auth/register', json={
        'username': username,
        'password': password
    })
    print(f"Status Code: {resp_reg_dup.status_code}")
    assert resp_reg_dup.status_code == 400, "Should block duplicate username registration"
    print("SUCCESS: Duplicate username registration blocked.")

    # 3. Attempt login as pending user (should fail with 403)
    print("\nAttempting login as the newly registered user (status is pending)...")
    resp_login = client.post('/api/auth/login', json={
        'username': username,
        'password': password
    })
    print(f"Status Code: {resp_login.status_code}")
    print(f"Body: {resp_login.data}")
    assert resp_login.status_code == 403, "Pending user should be blocked from logging in"
    assert b"not approved yet" in resp_login.data, "Expected account not approved message"
    print("SUCCESS: Login blocked for pending user.")

    # Cleanup user from DB
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            db.session.delete(user)
            db.session.commit()
            print("\nSUCCESS: Test user cleaned up from database.")

    print("\nALL USER REGISTRATION AND LOGIN BLOCK FLOW VERIFICATION TESTS PASSED!")

if __name__ == "__main__":
    test_register_flow()
