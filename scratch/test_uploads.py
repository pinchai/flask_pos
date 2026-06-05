import os
import io
import sys
from app import app
from extensions import db
import models

def run_tests():
    print("Starting programmatic file upload verification tests...")
    
    # Use Flask's test client
    client = app.test_client()
    
    # 1. Log in
    print("Logging in as admin/admin...")
    response = client.post('/login', data={
        'username': 'admin',
        'password': 'admin'
    }, follow_redirects=True)
    
    if b"Logged in successfully" not in response.data and b"AdminLTE" not in response.data:
        print("Login failed! Response data:")
        print(response.data[:500])
        sys.exit(1)
    print("Login successful.")

    # Get an existing user ID for shop/product owners
    with app.app_context():
        admin = models.User.query.filter_by(username='admin').first()
        admin_id = admin.id
        
        category = models.Category.query.first()
        if not category:
            # Seed a category if none exists
            category = models.Category(name="Test Category", user_id=admin_id)
            db.session.add(category)
            db.session.commit()
        category_id = category.id

    # 2. Test user creation with profile upload
    print("\nTesting user creation with profile upload...")
    profile_data = (io.BytesIO(b"dummy user profile image data"), "test_profile.png")
    response = client.post('/admin/users/create', data={
        'username': 'test_user_upload',
        'password': 'password123',
        'status': 'approve',
        'type': 'student',
        'profile': profile_data
    }, content_type='multipart/form-data', follow_redirects=True)
    
    # Verify in database
    with app.app_context():
        user = models.User.query.filter_by(username='test_user_upload').first()
        if not user:
            print("FAIL: User was not created in database.")
            sys.exit(1)
        print(f"SUCCESS: User created in database with ID {user.id}.")
        print(f"Stored profile path: {user.profile}")
        if not user.profile or not user.profile.startswith('/static/uploads/'):
            print("FAIL: Profile path is invalid or empty.")
            sys.exit(1)
            
        # Verify file exists on disk
        local_path = os.path.join(app.static_folder, user.profile.lstrip('/static/'))
        if not os.path.exists(local_path):
            print(f"FAIL: Uploaded file not found on disk at {local_path}.")
            sys.exit(1)
        print(f"SUCCESS: File verified on disk at {local_path}.")

    # 3. Test shop creation with logo upload
    print("\nTesting shop creation with logo upload...")
    logo_data = (io.BytesIO(b"dummy shop logo image data"), "test_logo.png")
    response = client.post('/admin/shops/create', data={
        'name': 'Test Upload Shop',
        'address': '123 Test St',
        'description': 'A shop tested via programmatic uploads',
        'user_id': admin_id,
        'logo': logo_data
    }, content_type='multipart/form-data', follow_redirects=True)
    
    # Verify in database
    with app.app_context():
        shop = models.Shop.query.filter_by(name='Test Upload Shop').first()
        if not shop:
            print("FAIL: Shop was not created in database.")
            sys.exit(1)
        print(f"SUCCESS: Shop created in database with ID {shop.id}.")
        print(f"Stored logo path: {shop.logo}")
        if not shop.logo or not shop.logo.startswith('/static/uploads/'):
            print("FAIL: Logo path is invalid or empty.")
            sys.exit(1)
            
        # Verify file exists on disk
        local_path = os.path.join(app.static_folder, shop.logo.lstrip('/static/'))
        if not os.path.exists(local_path):
            print(f"FAIL: Uploaded logo file not found on disk at {local_path}.")
            sys.exit(1)
        print(f"SUCCESS: Logo file verified on disk at {local_path}.")

    # 4. Test product creation with image upload
    print("\nTesting product creation with image upload...")
    image_data = (io.BytesIO(b"dummy product image data"), "test_product.png")
    response = client.post('/admin/products/create', data={
        'name': 'Test Upload Product',
        'category_id': category_id,
        'cost': '1.50',
        'price': '3.00',
        'stock': '50',
        'remark': 'Uploaded via test client',
        'user_id': admin_id,
        'image': image_data
    }, content_type='multipart/form-data', follow_redirects=True)
    
    # Verify in database
    with app.app_context():
        product = models.Product.query.filter_by(name='Test Upload Product').first()
        if not product:
            print("FAIL: Product was not created in database.")
            sys.exit(1)
        print(f"SUCCESS: Product created in database with ID {product.id}.")
        print(f"Stored image path: {product.image}")
        if not product.image or not product.image.startswith('/static/uploads/'):
            print("FAIL: Image path is invalid or empty.")
            sys.exit(1)
            
        # Verify file exists on disk
        local_path = os.path.join(app.static_folder, product.image.lstrip('/static/'))
        if not os.path.exists(local_path):
            print(f"FAIL: Uploaded image file not found on disk at {local_path}.")
            sys.exit(1)
        print(f"SUCCESS: Image file verified on disk at {local_path}.")

    print("\nAll programmatic file upload verification tests PASSED successfully!")

if __name__ == "__main__":
    run_tests()
