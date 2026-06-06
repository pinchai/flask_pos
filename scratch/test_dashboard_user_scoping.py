import sys
from app import app
from models import User, Shop, Product, Sale

def test_dashboard_user_scoping():
    print("Starting Dashboard User Scoping verification tests...")
    
    # Fetch expected counts from database
    with app.app_context():
        admin_user = User.query.filter_by(username='admin').first()
        student_user = User.query.filter_by(username='student').first()
        
        admin_shops = Shop.query.filter_by(user_id=admin_user.id).count()
        admin_products = Product.query.filter_by(user_id=admin_user.id).count()
        admin_sales = Sale.query.filter_by(user_id=admin_user.id).count()
        
        student_shops = Shop.query.filter_by(user_id=student_user.id).count()
        student_products = Product.query.filter_by(user_id=student_user.id).count()
        student_sales = Sale.query.filter_by(user_id=student_user.id).count()

    print(f"Database Counts - Admin: shops={admin_shops}, products={admin_products}, sales={admin_sales}")
    print(f"Database Counts - Student: shops={student_shops}, products={student_products}, sales={student_sales}")

    # 1. Test Admin Dashboard
    print("\nLogging in as admin/admin...")
    client_admin = app.test_client()
    client_admin.post('/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)
    
    response = client_admin.get('/admin')
    assert response.status_code == 200
    html_admin = response.data.decode('utf-8')
    
    # Admin should see Total Users, Shops, Products, and Sales
    assert "Total Users" in html_admin, "Admin dashboard should show 'Total Users'"
    assert f"<h3>{admin_shops}</h3>" in html_admin, "Admin dashboard shop count does not match database"
    assert f"<h3>{admin_sales}</h3>" in html_admin, "Admin dashboard sales count does not match database"
    
    # 2. Test Student Dashboard (standard salesperson)
    print("\nLogging in as student/student...")
    client_student = app.test_client()
    client_student.post('/login', data={'username': 'student', 'password': 'student'}, follow_redirects=True)
    
    response = client_student.get('/admin')
    assert response.status_code == 200
    html_student = response.data.decode('utf-8')
    
    # Student should NOT see Total Users box
    assert "Total Users" not in html_student, "Student dashboard should NOT show 'Total Users' box"
    
    # Student should see correct scoped counts in HTML
    assert f"<h3>{student_shops}</h3>" in html_student, "Student dashboard shop count does not match database"
    assert f"<h3>{student_sales}</h3>" in html_student, "Student dashboard sales count does not match database"
    
    print("\nSUCCESS: Dashboard user scoping verified successfully.")
    print("ALL DASHBOARD USER SCOPING TESTS PASSED!")

if __name__ == "__main__":
    test_dashboard_user_scoping()
