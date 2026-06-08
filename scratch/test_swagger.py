import sys
from app import app

def test_swagger_schema():
    print("Testing Swagger schema compilation...")
    client = app.test_client()
    
    response = client.get('/api/swagger.json')
    if response.status_code != 200:
        print(f"FAIL: /api/swagger.json failed with status code {response.status_code}")
        print(response.data)
        sys.exit(1)
        
    print("SUCCESS: /api/swagger.json returned HTTP 200.")
    data = response.json
    
    # Assert namespaces exist
    paths = data.get('paths', {})
    print(f"Discovered Swagger API Paths: {list(paths.keys())}")
    
    expected_paths = [
        '/shops/',
        '/categories/',
        '/products/',
        '/payment-methods/',
        '/sales/'
    ]
    
    for path in expected_paths:
        assert any(p.startswith(path) for p in paths), f"Namespace path {path} not found in Swagger schema!"
        print(f"SUCCESS: Namespace path {path} verified in Swagger.")

    print("\nALL SWAGGER API SCHEMAS COMPILED AND VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    test_swagger_schema()
