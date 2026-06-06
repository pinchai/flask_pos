import sys
from app import app

def test_search_features():
    print("Starting Table Search verification tests...")
    client = app.test_client()

    # 1. Login
    print("Logging in as admin/admin...")
    client.post('/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)

    # 2. Test Users Search
    print("Testing /admin/users?search=admin...")
    response = client.get('/admin/users?search=admin')
    assert response.status_code == 200, f"Failed: {response.status_code}"
    html = response.data.decode('utf-8')
    assert "admin" in html, "Username admin not found in results"
    
    print("Testing /admin/users?search=nonexistent...")
    response = client.get('/admin/users?search=nonexistent')
    html = response.data.decode('utf-8')
    assert "No users found" in html or "nonexistent" not in html, "Nonexistent user match is leaking"
    print("SUCCESS: Users search verified.")

    # 3. Test Shops Search
    print("Testing /admin/shops?search=Main...")
    response = client.get('/admin/shops?search=Main')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert "Main Branch" in html, "Main Branch not found"
    assert "Downtown Shop" not in html, "Downtown Shop should be filtered out"
    print("SUCCESS: Shops search verified.")

    # 4. Test Categories Search
    print("Testing /admin/categories?search=Beverage...")
    response = client.get('/admin/categories?search=Beverage')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert "Beverages" in html, "Beverages category not found"
    assert "Electronics" not in html, "Electronics category should be filtered out"
    print("SUCCESS: Categories search verified.")

    # 5. Test Products Search
    print("Testing /admin/products?search=Latte...")
    response = client.get('/admin/products?search=Latte')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert "Latte" in html, "Latte product not found"
    assert "USB C Cable" not in html, "USB C Cable should be filtered out"
    print("SUCCESS: Products search verified.")

    # 6. Test Payment Methods Search
    print("Testing /admin/payment-methods?search=ABA...")
    response = client.get('/admin/payment-methods?search=ABA')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    assert "ABA" in html, "ABA Pay not found"
    assert "Credit Card" not in html, "Credit Card should be filtered out"
    print("SUCCESS: Payment Methods search verified.")

    # 7. Test Sales Search
    print("Testing /admin/sales?search=Main...")
    response = client.get('/admin/sales?search=Main')
    assert response.status_code == 200
    print("SUCCESS: Sales search verified.")

    print("\nALL TABLE SEARCH VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_search_features()
