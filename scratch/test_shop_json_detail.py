import sys
from app import app
from extensions import db
from models import Shop, User

def test_shop_json_detail():
    print("Starting Shop JSON Detail validation...")
    client = app.test_client()

    # 1. Login to get token
    resp_login = client.post('/api/auth/login', json={
        'username': 'admin',
        'password': 'admin'
    })
    
    assert resp_login.status_code == 200, "Login failed"
    token = resp_login.json.get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    print("SUCCESS: Login completed. Token obtained.")

    # 2. Find a shop owned by admin
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        shop = Shop.query.filter_by(user_id=admin.id).first()
        if not shop:
            print("FAIL: No shops found for admin.")
            sys.exit(1)
        shop_id = shop.id
        print(f"Using Shop ID: {shop_id}")

    # 3. Retrieve shop details via JSON body
    print("\nRetrieving shop detail via JSON...")
    resp_get = client.post('/api/shops/detail', json={'shop_id': shop_id}, headers=headers)
    print(f"Status Code: {resp_get.status_code}")
    print(f"Body: {resp_get.json}")
    assert resp_get.status_code == 200, "Failed to retrieve shop details"
    assert resp_get.json.get('id') == shop_id, "Shop ID mismatch"
    print("SUCCESS: Shop details retrieved via JSON payload.")

    # 4. Update shop details via JSON body
    print("\nUpdating shop details via JSON...")
    resp_put = client.put('/api/shops/detail', json={
        'shop_id': shop_id,
        'name': 'Updated Shop Name via JSON',
        'address': 'Updated Address'
    }, headers=headers)
    print(f"Status Code: {resp_put.status_code}")
    print(f"Body: {resp_put.json}")
    assert resp_put.status_code == 200, "Failed to update shop details"
    assert resp_put.json.get('name') == 'Updated Shop Name via JSON', "Name not updated"
    print("SUCCESS: Shop updated via JSON payload.")

    # Revert update
    with app.app_context():
        s = Shop.query.get(shop_id)
        s.name = 'Main Branch'
        s.address = '123 Norodom Blvd, Phnom Penh'
        db.session.commit()
        print("Reverted shop details in DB.")

    # 5. Test deletion with dummy shop creation first
    print("\nCreating a temporary shop to test deletion...")
    resp_create = client.post('/api/shops/', json={
        'name': 'Temp Shop to Delete',
        'address': 'Temp Address'
    }, headers=headers)
    assert resp_create.status_code == 201
    temp_shop_id = resp_create.json.get('id')
    print(f"Temporary Shop Created with ID: {temp_shop_id}")

    print("Deleting temporary shop via JSON payload...")
    resp_del = client.delete('/api/shops/detail', json={'shop_id': temp_shop_id}, headers=headers)
    print(f"Status Code: {resp_del.status_code}")
    print(f"Body: {resp_del.json}")
    assert resp_del.status_code == 200, "Failed to delete shop via JSON payload"
    
    # Confirm deletion
    with app.app_context():
        assert Shop.query.get(temp_shop_id) is None, "Shop was not deleted from DB"
    print("SUCCESS: Shop deleted via JSON payload.")

    print("\nALL SHOP JSON DETAIL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_shop_json_detail()
