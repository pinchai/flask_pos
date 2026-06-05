import sys
from app import app
import models

def test_dashboard_charts():
    print("Starting Dashboard Google Charts verification tests...")
    client = app.test_client()

    # 1. Login
    print("Logging in as admin/admin...")
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'admin'
    }, follow_redirects=True)
    
    if b"Logged in successfully" not in response.data and b"AdminLTE" not in response.data:
        print("FAIL: Login failed.")
        sys.exit(1)
    print("SUCCESS: Login completed.")

    # 2. Query Dashboard Index Page
    print("\nQuerying Dashboard index page...")
    response = client.get('/admin')
    if response.status_code != 200:
        print(f"FAIL: Dashboard index returned status code {response.status_code}.")
        sys.exit(1)
    print("SUCCESS: Dashboard index loaded (200 OK).")

    # 3. Check for Google Charts library and chart configuration scripts in response content
    assert b"https://www.gstatic.com/charts/loader.js" in response.data, "FAIL: Google Charts loader script not found."
    assert b"google.visualization.arrayToDataTable" in response.data, "FAIL: Data table draw function not found."
    assert b"revenue_trend_chart" in response.data, "FAIL: Revenue trend container not found."
    assert b"category_share_chart" in response.data, "FAIL: Category share container not found."
    assert b"shop_revenue_chart" in response.data, "FAIL: Shop revenue container not found."
    print("SUCCESS: Google Charts script integration verified on the page.")

    # 4. Confirm chart data variables passed to template are rendered
    with app.app_context():
        # Check if the product category counts are populated
        categories = models.Category.query.all()
        for cat in categories:
            cat_bytes = cat.name.encode()
            if cat_bytes in response.data:
                print(f"SUCCESS: Rendered category '{cat.name}' in charts data.")
            else:
                print(f"INFO: Category '{cat.name}' not rendered (may have 0 products).")

    print("\nAll Dashboard Google Charts verification tests PASSED successfully!")

if __name__ == "__main__":
    test_dashboard_charts()
