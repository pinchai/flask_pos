import os
from app import app
from extensions import db
import models

def seed_data():
    print("Seeding database...")
    
    # 1. Seed Users
    admin_user = models.User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = models.User(username='admin', status='approve', type='admin')
        admin_user.set_password('admin')
        db.session.add(admin_user)
        print("Created user: admin")
    else:
        print("User 'admin' already exists")
        
    student_user = models.User.query.filter_by(username='student').first()
    if not student_user:
        student_user = models.User(username='student', status='approve', type='student')
        student_user.set_password('student')
        db.session.add(student_user)
        print("Created user: student")
    else:
        print("User 'student' already exists")

    db.session.commit()

    # 2. Seed Shops
    shops_data = [
        {"name": "Main Branch", "address": "123 Norodom Blvd, Phnom Penh", "logo": "https://placehold.co/100x100?text=Main+Branch", "description": "Our flagship store"},
        {"name": "Downtown Shop", "address": "456 Monivong Blvd, Phnom Penh", "logo": "https://placehold.co/100x100?text=Downtown+Shop", "description": "Quick service shop"},
        {"name": "Campus Cafe", "address": "RUPP Campus, Phnom Penh", "logo": "https://placehold.co/100x100?text=Campus+Cafe", "description": "Serving student needs"}
    ]
    
    shops = []
    for s in shops_data:
        shop = models.Shop.query.filter_by(name=s["name"]).first()
        if not shop:
            shop = models.Shop(
                name=s["name"], address=s["address"], logo=s["logo"],
                description=s["description"], user_id=admin_user.id
            )
            db.session.add(shop)
            print(f"Created shop: {s['name']}")
        else:
            print(f"Shop '{s['name']}' already exists")
        shops.append(shop)
    db.session.commit()

    # 3. Seed Categories
    categories_data = ["Beverages", "Snacks", "Electronics", "Stationery"]
    categories = []
    for c_name in categories_data:
        cat = models.Category.query.filter_by(name=c_name).first()
        if not cat:
            cat = models.Category(name=c_name, remark=f"{c_name} category description", user_id=admin_user.id)
            db.session.add(cat)
            print(f"Created category: {c_name}")
        else:
            print(f"Category '{c_name}' already exists")
        categories.append(cat)
    db.session.commit()

    # 4. Seed Products
    products_data = [
        {"name": "Cappuccino", "cat_name": "Beverages", "cost": 2.50, "price": 4.50, "stock": 150.0},
        {"name": "Iced Latte", "cat_name": "Beverages", "cost": 2.00, "price": 3.75, "stock": 200.0},
        {"name": "Green Tea Latte", "cat_name": "Beverages", "cost": 2.20, "price": 4.00, "stock": 100.0},
        {"name": "Chocolate Cookie", "cat_name": "Snacks", "cost": 1.20, "price": 2.50, "stock": 80.0},
        {"name": "Cheese Sandwich", "cat_name": "Snacks", "cost": 1.80, "price": 3.50, "stock": 50.0},
        {"name": "USB C Cable", "cat_name": "Electronics", "cost": 3.00, "price": 8.99, "stock": 120.0},
        {"name": "Notebook A5", "cat_name": "Stationery", "cost": 0.50, "price": 1.50, "stock": 300.0},
        {"name": "Gel Pen Blue", "cat_name": "Stationery", "cost": 0.20, "price": 0.80, "stock": 500.0}
    ]
    for p in products_data:
        prod = models.Product.query.filter_by(name=p["name"]).first()
        if not prod:
            cat = models.Category.query.filter_by(name=p["cat_name"]).first()
            prod = models.Product(
                name=p["name"], category_id=cat.id, cost=p["cost"], price=p["price"],
                stock=p["stock"], image=f"https://placehold.co/170x170?text={p['name']}",
                remark="Best seller", user_id=admin_user.id
            )
            db.session.add(prod)
            print(f"Created product: {p['name']}")
        else:
            print(f"Product '{p['name']}' already exists")
    db.session.commit()

    # 5. Seed Payment Methods
    pm_data = ["Cash", "ABA Pay", "Credit Card", "Wing"]
    for pm_name in pm_data:
        pm = models.PaymentMethod.query.filter_by(name=pm_name).first()
        if not pm:
            pm = models.PaymentMethod(name=pm_name, remark=f"Pay with {pm_name}", user_id=admin_user.id)
            db.session.add(pm)
            print(f"Created payment method: {pm_name}")
        else:
            print(f"Payment method '{pm_name}' already exists")
    db.session.commit()

    print("Database seeding completed successfully!")

if __name__ == "__main__":
    with app.app_context():
        seed_data()
