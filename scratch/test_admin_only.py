import sys
from app import app
from extensions import db
import models

def test_admin_only_access():
    print("Starting programmatic admin-only access tests...")
    client = app.test_client()

    # 1. Login as student
    print("Logging in as student/student...")
    client.post('/login', data={'username': 'student', 'password': 'student'}, follow_redirects=True)

    # 2. Try to access /admin/users (should get redirected and have flash message)
    print("Attempting to access /admin/users as student...")
    response = client.get('/admin/users', follow_redirects=True)
    if b"Access denied. Admin role required." not in response.data:
        print("FAIL: Student was not blocked from accessing User list page.")
        sys.exit(1)
    print("SUCCESS: Student blocked from listing users.")

    # Try to access create_user as student
    response = client.get('/admin/users/create', follow_redirects=True)
    if b"Access denied. Admin role required." not in response.data:
        print("FAIL: Student was not blocked from accessing User creation form.")
        sys.exit(1)
    print("SUCCESS: Student blocked from creating users.")

    # 3. Logout and login as admin
    print("Logging out and logging in as admin/admin...")
    client.get('/logout')
    client.post('/login', data={'username': 'admin', 'password': 'admin'}, follow_redirects=True)

    # 4. Access /admin/users (should work)
    print("Accessing /admin/users as admin...")
    response = client.get('/admin/users', follow_redirects=True)
    if b"Access denied. Admin role required." in response.data or response.status_code != 200:
        print("FAIL: Admin was blocked from listing users.")
        sys.exit(1)
    print("SUCCESS: Admin listed users successfully.")

    print("\nALL ADMIN-ONLY ACCESS VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_admin_only_access()
