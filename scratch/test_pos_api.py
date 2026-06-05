import sys
from app import app
from extensions import db
import models

def test_pos_transaction():
    print("Starting POS Transaction API verification tests...")
    client = app.test_client()

    # 1. Login
    print("Logging in as admin...")
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'admin'
    }, follow_redirects=True)
    
    if b"Logged in successfully" not in response.data and b"AdminLTE" not in response.data:
        print("FAIL: Login failed.")
        sys.exit(1)
    print("SUCCESS: Login completed.")

    # 2. Get initial stock of a product
    with app.app_context():
        product = models.Product.query.first()
        if not product:
            print("FAIL: No products in database. Please run seeder first.")
            sys.exit(1)
        product_id = product.id
        initial_stock = float(product.stock)
        price = float(product.price)
        print(f"Product '{product.name}' (ID: {product_id}) - Price: ${price:.2f}, Initial Stock: {initial_stock}")
        
        shop = models.Shop.query.first()
        shop_id = shop.id
        
        pm = models.PaymentMethod.query.first()
        pm_id = pm.id

    # 3. Submit POS Transaction
    print("\nSubmitting sale transaction to POS API...")
    payload = {
        'shop_id': shop_id,
        'payment_method_id': pm_id,
        'discount_pct': 10,
        'discount_amount': round((price * 2) * 0.10, 2),
        'total': round((price * 2) * 0.90, 2),
        'paid_amount': round((price * 2), 2),
        'items': [
            {
                'product_id': product_id,
                'qty': 2
            }
        ]
    }
    
    response = client.post('/admin/api/sales/create', json=payload)
    if response.status_code != 200:
        print(f"FAIL: POS transaction failed with status {response.status_code}.")
        print(response.data)
        sys.exit(1)
    print("SUCCESS: POS transaction submitted successfully (200 OK).")
    print("Response payload:", response.json)

    # 4. Verify stock levels and transaction logs in SQLite
    with app.app_context():
        updated_product = models.Product.query.get(product_id)
        new_stock = float(updated_product.stock)
        print(f"Product '{updated_product.name}' - New Stock: {new_stock}")
        
        if new_stock != initial_stock - 2:
            print(f"FAIL: Stock level not updated correctly. Expected: {initial_stock - 2}, Got: {new_stock}")
            sys.exit(1)
        print("SUCCESS: Product stock level correctly decremented by 2.")

        # Check latest sale log
        latest_sale = models.Sale.query.order_by(models.Sale.id.desc()).first()
        print(f"Latest Sale ID: {latest_sale.id}, Total: ${latest_sale.total:.2f}, Discount: ${latest_sale.discount_amount:.2f}")
        
        if abs(float(latest_sale.total) - payload['total']) > 0.01:
            print(f"FAIL: Recorded sale total mismatch. Expected: {payload['total']}, Got: {latest_sale.total}")
            sys.exit(1)
        print("SUCCESS: Sale record details match the POS payload exactly.")

    print("\nAll POS API transaction verification tests PASSED successfully!")

if __name__ == "__main__":
    test_pos_transaction()
