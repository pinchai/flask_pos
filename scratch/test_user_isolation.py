import sys
from app import app
from extensions import db
import models

def test_user_isolation():
    print("Starting programmatic user isolation validation...")
    client = app.test_client()

    with app.app_context():
        admin_user = models.User.query.filter_by(username='admin').first()
        student_user = models.User.query.filter_by(username='student').first()
        
        if not admin_user or not student_user:
            print("FAIL: Please run seeder first to create admin and student users.")
            sys.exit(1)

        # Count total products, shops, categories, and payment methods owned by admin
        admin_products = models.Product.query.filter_by(user_id=admin_user.id).count()
        admin_shops = models.Shop.query.filter_by(user_id=admin_user.id).count()
        
        print(f"Admin owns {admin_products} products and {admin_shops} shops in DB.")
        
        # Verify student initially has 0 products and shops in DB
        student_products = models.Product.query.filter_by(user_id=student_user.id).count()
        student_shops = models.Shop.query.filter_by(user_id=student_user.id).count()
        print(f"Student owns {student_products} products and {student_shops} shops in DB.")
        
    # 1. Login as student
    print("\nLogging in as student/student...")
    client.post('/login', data={'username': 'student', 'password': 'student'}, follow_redirects=True)
    
    # 2. Check student's product list via products API
    print("Checking student's products list...")
    response = client.get('/admin/api/products')
    assert response.status_code == 200, "Failed to load student products API"
    data = response.json
    products_count = len(data.get('products', []))
    print(f"Student products count from API: {products_count}")
    if products_count != student_products:
        print(f"FAIL: Student saw {products_count} products instead of {student_products}.")
        sys.exit(1)
    print("SUCCESS: Student product list is isolated.")

    # 3. Check student's shops list
    print("Checking student's shops list page...")
    response = client.get('/admin/shops')
    assert response.status_code == 200, "Failed to load student shops page"
    # The count in student's shops page should display "No matching records found" or equivalent since it's empty
    if b"Downtown" in response.data or b"Main Branch" in response.data:
        print("FAIL: Student saw admin's shops on the list page.")
        sys.exit(1)
    print("SUCCESS: Student shops list page is isolated.")

    # 4. Create a shop under student session
    print("\nCreating a new shop under student session...")
    response = client.post('/admin/shops/create', data={
        'name': 'Student Bookstore',
        'address': 'RUPP Bldg A',
        'description': 'Student-owned bookstore'
    }, follow_redirects=True)
    
    with app.app_context():
        new_shop = models.Shop.query.filter_by(name='Student Bookstore').first()
        if not new_shop:
            print("FAIL: Student Bookstore was not created.")
            sys.exit(1)
        if new_shop.user_id != student_user.id:
            print(f"FAIL: Shop user_id was {new_shop.user_id} instead of student ID {student_user.id}.")
            sys.exit(1)
        print("SUCCESS: Shop created under student user ID correctly.")

    # 5. Check if shop is listed in student list
    response = client.get('/admin/shops')
    if b"Student Bookstore" not in response.data:
        print("FAIL: Student Bookstore not visible in student shops list.")
        sys.exit(1)
    print("SUCCESS: Student Bookstore visible in student shops list.")

    # 6. Logout and login as admin
    print("\nLogging out student and logging in as admin...")
    client.get('/logout')
    client.post('/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)

    # Check if student's shop is visible to admin
    response = client.get('/admin/shops')
    if b"Student Bookstore" in response.data:
        print("FAIL: Student's shop is visible to admin.")
        sys.exit(1)
    print("SUCCESS: Student's shop is NOT visible in admin shops list.")

    # Try to access student's shop details directly as admin (should return 404)
    response = client.post(f'/admin/shops/delete/{new_shop.id}', follow_redirects=True)
    if response.status_code != 404:
        print(f"FAIL: Admin was able to access/delete student's shop (Status: {response.status_code}).")
        sys.exit(1)
    print("SUCCESS: Admin got 404 trying to delete student's shop.")

    # Tidy up created bookstore shop
    with app.app_context():
        db.session.delete(models.Shop.query.get(new_shop.id))
        db.session.commit()

    print("\nALL USER ISOLATION VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_user_isolation()
