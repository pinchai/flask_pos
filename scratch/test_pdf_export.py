import sys
from app import app
from models import Sale

def test_pdf_export():
    print("Starting PDF Export verification test...")
    client = app.test_client()

    # 1. Login
    print("Logging in as admin/admin...")
    client.post('/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)

    # 2. Get first sale ID from DB
    with app.app_context():
        sale = Sale.query.first()
        sale_id = sale.id if sale else None

    if not sale_id:
        print("FAIL: No sales found in the database. Cannot run PDF export test.")
        sys.exit(1)

    print(f"Testing PDF export for Sale ID: {sale_id}...")
    
    # 3. Request PDF route
    response = client.get(f'/admin/sales/view/{sale_id}/pdf')
    
    if response.status_code != 200:
        print(f"FAIL: PDF export failed with status code {response.status_code}.")
        sys.exit(1)
        
    print("SUCCESS: PDF route responded with HTTP 200.")
    
    # Verify content type
    content_type = response.headers.get('Content-Type', '')
    print(f"Content-Type: '{content_type}'")
    assert "application/pdf" in content_type, f"Invalid Content-Type: {content_type}"
    
    # Verify PDF file signature (%PDF-)
    data = response.data
    signature = data[:5]
    print(f"PDF header bytes: {signature}")
    assert signature == b'%PDF-', "File is not a valid PDF document (missing %PDF- header)"
    
    print("\nPDF INVOICE GENERATION TEST PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_pdf_export()
