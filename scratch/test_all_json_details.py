import sys
from app import app
from extensions import db
from models import Category, Product, PaymentMethod, Sale, User

def test_all_json_details():
    print("Starting Comprehensive JSON Details validation...")
    client = app.test_client()

    # 1. Login to get token
    resp_login = client.post('/api/auth/login', json={
        'username': 'admin',
        'password': 'admin'
    })
    assert resp_login.status_code == 200, "Login failed"
    token = resp_login.json.get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    print("SUCCESS: Logged in. Token obtained.")

    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        
        # Categories Setup
        cat = Category.query.filter_by(user_id=admin.id).first()
        cat_id = cat.id if cat else None
        
        # Products Setup
        prod = Product.query.filter_by(user_id=admin.id).first()
        prod_id = prod.id if prod else None
        
        # Payment Methods Setup
        pm = PaymentMethod.query.filter_by(user_id=admin.id).first()
        pm_id = pm.id if pm else None
        
        # Sales Setup
        sale = Sale.query.filter_by(user_id=admin.id).first()
        sale_id = sale.id if sale else None

    # 2. Test Category JSON Detail
    if cat_id:
        print(f"\nRetrieving Category ID {cat_id} details...")
        resp = client.post('/api/categories/detail', json={'category_id': cat_id}, headers=headers)
        assert resp.status_code == 200, "Category details retrieval failed"
        assert resp.json.get('id') == cat_id
        print("SUCCESS: Category details retrieved.")

        print("Updating Category via JSON...")
        resp = client.put('/api/categories/detail', json={'category_id': cat_id, 'name': 'Updated Category JSON'}, headers=headers)
        assert resp.status_code == 200, "Category update failed"
        assert resp.json.get('name') == 'Updated Category JSON'
        print("SUCCESS: Category updated.")

    # 3. Test Product JSON Detail
    if prod_id:
        print(f"\nRetrieving Product ID {prod_id} details...")
        resp = client.post('/api/products/detail', json={'product_id': prod_id}, headers=headers)
        assert resp.status_code == 200, "Product details retrieval failed"
        assert resp.json.get('id') == prod_id
        print("SUCCESS: Product details retrieved.")

        print("Updating Product via JSON...")
        resp = client.put('/api/products/detail', json={'product_id': prod_id, 'name': 'Updated Prod JSON', 'category_id': cat_id, 'price': 9.99}, headers=headers)
        assert resp.status_code == 200, "Product update failed"
        assert resp.json.get('name') == 'Updated Prod JSON'
        print("SUCCESS: Product updated.")

    # 4. Test Payment Method JSON Detail
    if pm_id:
        print(f"\nRetrieving Payment Method ID {pm_id} details...")
        resp = client.post('/api/payment-methods/detail', json={'pm_id': pm_id}, headers=headers)
        assert resp.status_code == 200, "PM details retrieval failed"
        assert resp.json.get('id') == pm_id
        print("SUCCESS: PM details retrieved.")

        print("Updating Payment Method via JSON...")
        resp = client.put('/api/payment-methods/detail', json={'pm_id': pm_id, 'name': 'Updated PM JSON'}, headers=headers)
        assert resp.status_code == 200, "PM update failed"
        assert resp.json.get('name') == 'Updated PM JSON'
        print("SUCCESS: PM updated.")

    # 5. Test Sale JSON Detail
    if sale_id:
        print(f"\nRetrieving Sale ID {sale_id} details...")
        resp = client.post('/api/sales/detail', json={'sale_id': sale_id}, headers=headers)
        assert resp.status_code == 200, "Sale details retrieval failed"
        assert resp.json.get('id') == sale_id
        print("SUCCESS: Sale details retrieved.")

    # 6. Test Legacy User JSON Detail
    print("\nRetrieving Legacy User detail via JSON payload...")
    resp = client.post('/api/legacy/legacy-users/detail', json={'user_id': 99, 'name': 'Legacy Guest'})
    assert resp.status_code == 200, "Legacy user endpoint failed"
    assert resp.json == [{"id": 99, "name": "Legacy Guest"}]
    print("SUCCESS: Legacy user details retrieved.")

    # Revert database changes
    with app.app_context():
        if cat_id:
            c = Category.query.get(cat_id)
            c.name = 'Beverages'
            db.session.commit()
        if prod_id:
            p = Product.query.get(prod_id)
            p.name = 'Cappuccino'
            db.session.commit()
        if pm_id:
            m = PaymentMethod.query.get(pm_id)
            m.name = 'Cash'
            db.session.commit()
        print("\nSUCCESS: All dummy database entities successfully reverted.")

    print("\nALL COMPREHENSIVE JSON DETAILS VALIDATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_all_json_details()
