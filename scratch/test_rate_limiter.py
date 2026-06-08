import sys
from app import app

def test_rate_limiter():
    print("Starting Rate Limiter validation...")
    client = app.test_client()

    # Make request to /api/auth/login
    print("Making request to /api/auth/login to check rate limit headers...")
    response = client.post('/api/auth/login', json={
        'username': 'admin',
        'password': 'admin'
    })
    
    print(f"Status Code: {response.status_code}")
    print("Response Headers:")
    for header, value in response.headers.items():
        if 'ratelimit' in header.lower():
            print(f"  {header}: {value}")
            
    # Check if rate limit headers exist
    limit_header = response.headers.get('X-RateLimit-Limit')
    remaining_header = response.headers.get('X-RateLimit-Remaining')
    
    assert limit_header is not None, "X-RateLimit-Limit header not found"
    assert remaining_header is not None, "X-RateLimit-Remaining header not found"
    assert "200" in limit_header, f"Expected limit of 200/hour, got {limit_header}"
    
    print(f"SUCCESS: Rate limit headers validated successfully. Limit: {limit_header}, Remaining: {remaining_header}")
    
    # Check that a non-API route (like /login) also has rate limits applied globally
    print("\nChecking non-API route to ensure rate limits are applied globally...")
    dashboard_resp = client.get('/login')
    print(f"Status Code: {dashboard_resp.status_code}")
    assert 'X-RateLimit-Limit' in dashboard_resp.headers, "Dashboard route should also have rate limits globally"
    print("SUCCESS: Non-API dashboard route is rate limited globally.")
    
    print("\nALL RATE LIMITER TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_rate_limiter()
