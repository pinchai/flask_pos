import sys
from app import app

def test_jwt_authentication():
    print("Starting JWT Authentication flow validation...")
    client = app.test_client()

    # 1. Access protected route without token (should fail)
    print("Accessing protected route /api/shops/ without token...")
    resp_unauth = client.get('/api/shops/')
    print(f"Status Code: {resp_unauth.status_code}")
    print(f"Body: {resp_unauth.data}")
    assert resp_unauth.status_code == 401, "Should block unauthorized requests"
    print("SUCCESS: Unauthorized access blocked successfully.")

    # 2. Login to get token
    print("\nAttempting login via /api/auth/login...")
    resp_login = client.post('/api/auth/login', json={
        'username': 'admin',
        'password': 'admin'
    })
    
    assert resp_login.status_code == 200, "Login failed"
    data = resp_login.json
    access_token = data.get('access_token')
    assert access_token, "No access token returned"
    print("SUCCESS: Login completed. Token received.")

    # 3. Access protected route with Bearer token (should pass)
    print("\nAccessing protected route /api/shops/ with Bearer token...")
    resp_auth = client.get('/api/shops/', headers={
        'Authorization': f'Bearer {access_token}'
    })
    
    assert resp_auth.status_code == 200, f"Authorized access failed with status {resp_auth.status_code}"
    shops_data = resp_auth.json
    print(f"Discovered Shops: {shops_data}")
    assert isinstance(shops_data, list), "Should return a list of shops"
    print("SUCCESS: Authorized access retrieved correct scoped data.")

    print("\nALL JWT AUTHENTICATION VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_jwt_authentication()
