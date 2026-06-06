import os
import sys
import random
from datetime import datetime, timedelta
from app import app
from extensions import db
import models

def seed_data():
    print("Wiping existing database tables...")
    try:
        # Delete dependent tables first due to foreign keys
        db.session.query(models.SaleItem).delete()
        db.session.query(models.Sale).delete()
        db.session.query(models.Product).delete()
        db.session.query(models.Category).delete()
        db.session.query(models.Shop).delete()
        db.session.query(models.PaymentMethod).delete()
        db.session.query(models.User).delete()
        db.session.commit()
        print("SUCCESS: Existing database wiped clean.")
    except Exception as e:
        db.session.rollback()
        print(f"Error wiping database: {e}")
        sys.exit(1)

    print("Seeding database...")
    
    # 1. Seed Users
    admin_user = models.User(username='admin', status='approve', type='admin')
    admin_user.set_password('admin')
    db.session.add(admin_user)
    print("Created user: admin")
        
    student_user = models.User(username='student', status='approve', type='student')
    student_user.set_password('student')
    db.session.add(student_user)
    print("Created user: student")
    db.session.commit()

    # 2. Seed Shops
    admin_shops_data = [
        {"name": "Main Branch", "address": "123 Norodom Blvd, Phnom Penh", "logo": "https://placehold.co/100x100?text=Main+Branch", "description": "Our flagship store"},
        {"name": "Downtown Shop", "address": "456 Monivong Blvd, Phnom Penh", "logo": "https://placehold.co/100x100?text=Downtown+Shop", "description": "Quick service shop"},
        {"name": "Campus Cafe", "address": "RUPP Campus, Phnom Penh", "logo": "https://placehold.co/100x100?text=Campus+Cafe", "description": "Serving student needs"}
    ]
    admin_shops = []
    for s in admin_shops_data:
        shop = models.Shop(
            name=s["name"], address=s["address"], logo=s["logo"],
            description=s["description"], user_id=admin_user.id
        )
        db.session.add(shop)
        admin_shops.append(shop)
        print(f"Created admin shop: {s['name']}")

    student_shops_data = [
        {"name": "Student Shop", "address": "RUPP Bldg A, Phnom Penh", "logo": "https://placehold.co/100x100?text=Student+Shop", "description": "Student shop"}
    ]
    student_shops = []
    for s in student_shops_data:
        shop = models.Shop(
            name=s["name"], address=s["address"], logo=s["logo"],
            description=s["description"], user_id=student_user.id
        )
        db.session.add(shop)
        student_shops.append(shop)
        print(f"Created student shop: {s['name']}")
    db.session.commit()

    # 3. Seed Categories
    admin_categories_data = ["Beverages", "Snacks", "Electronics", "Stationery"]
    admin_categories = {}
    for c_name in admin_categories_data:
        cat = models.Category(name=c_name, remark=f"{c_name} category description", user_id=admin_user.id)
        db.session.add(cat)
        admin_categories[c_name] = cat
        print(f"Created admin category: {c_name}")

    student_categories_data = ["Beverages", "Books"]
    student_categories = {}
    for c_name in student_categories_data:
        cat = models.Category(name=c_name, remark=f"Student {c_name} category", user_id=student_user.id)
        db.session.add(cat)
        student_categories[c_name] = cat
        print(f"Created student category: {c_name}")
    db.session.commit()

    # 4. Seed Products
    admin_products_data = [
        {"name": "Cappuccino", "cat_name": "Beverages", "cost": 2.50, "price": 4.50, "stock": 150.0},
        {"name": "Iced Latte", "cat_name": "Beverages", "cost": 2.00, "price": 3.75, "stock": 200.0},
        {"name": "Green Tea Latte", "cat_name": "Beverages", "cost": 2.20, "price": 4.00, "stock": 100.0},
        {"name": "Chocolate Cookie", "cat_name": "Snacks", "cost": 1.20, "price": 2.50, "stock": 80.0},
        {"name": "Cheese Sandwich", "cat_name": "Snacks", "cost": 1.80, "price": 3.50, "stock": 50.0},
        {"name": "USB C Cable", "cat_name": "Electronics", "cost": 3.00, "price": 8.99, "stock": 120.0},
        {"name": "Notebook A5", "cat_name": "Stationery", "cost": 0.50, "price": 1.50, "stock": 300.0},
        {"name": "Gel Pen Blue", "cat_name": "Stationery", "cost": 0.20, "price": 0.80, "stock": 500.0}
    ]
    admin_products = []
    for p in admin_products_data:
        cat = admin_categories[p["cat_name"]]
        clean_name = p["name"].lower().replace(" ", "_")
        prod = models.Product(
            name=p["name"], category_id=cat.id, cost=p["cost"], price=p["price"],
            stock=p["stock"], image=f"/static/uploads/{clean_name}.png",
            remark="Best seller", user_id=admin_user.id
        )
        db.session.add(prod)
        admin_products.append(prod)
        print(f"Created admin product: {p['name']}")

    student_products_data = [
        {"name": "Text Book", "cat_name": "Books", "cost": 5.00, "price": 10.00, "stock": 50.0},
        {"name": "Lemon Tea", "cat_name": "Beverages", "cost": 1.00, "price": 2.00, "stock": 100.0}
    ]
    student_products = []
    for p in student_products_data:
        cat = student_categories[p["cat_name"]]
        clean_name = p["name"].lower().replace(" ", "_")
        prod = models.Product(
            name=p["name"], category_id=cat.id, cost=p["cost"], price=p["price"],
            stock=p["stock"], image=f"/static/uploads/{clean_name}.png",
            remark="Student essentials", user_id=student_user.id
        )
        db.session.add(prod)
        student_products.append(prod)
        print(f"Created student product: {p['name']}")
    db.session.commit()

    # 5. Seed Payment Methods
    admin_pm_names = ["Cash", "ABA Pay", "Credit Card", "Wing"]
    admin_pms = []
    for pm_name in admin_pm_names:
        pm = models.PaymentMethod(name=pm_name, remark=f"Pay with {pm_name}", user_id=admin_user.id)
        db.session.add(pm)
        admin_pms.append(pm)
        print(f"Created admin payment method: {pm_name}")

    student_pm_names = ["Cash", "ABA Pay"]
    student_pms = []
    for pm_name in student_pm_names:
        pm = models.PaymentMethod(name=pm_name, remark=f"Pay with {pm_name}", user_id=student_user.id)
        db.session.add(pm)
        student_pms.append(pm)
        print(f"Created student payment method: {pm_name}")
    db.session.commit()

    # 6. Seed Sales and Transactions (spread over the last 15 days)
    print("Seeding sales transactions for users...")
    
    # Seeding for Admin
    # Create 18 sales distributed across last 15 days
    for i in range(18):
        days_ago = random.randint(0, 14)
        sale_date = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
        shop = random.choice(admin_shops)
        pm = random.choice(admin_pms)
        
        # Pick 1 to 3 items
        items_count = random.randint(1, 3)
        selected_prods = random.sample(admin_products, items_count)
        
        discount_pct = random.choice([0, 0, 0, 5, 10]) # 0% common, sometimes 5% or 10%
        
        sale = models.Sale(
            shop_id=shop.id,
            user_id=admin_user.id,
            payment_method_id=pm.id,
            sale_date=sale_date,
            discount_pct=discount_pct,
            total=0.0,
            discount_amount=0.0,
            paid_amount=0.0
        )
        db.session.add(sale)
        db.session.flush() # Get sale.id
        
        subtotal = 0.0
        for prod in selected_prods:
            qty = random.randint(1, 4)
            item = models.SaleItem(
                user_id=admin_user.id,
                sale_id=sale.id,
                product_id=prod.id,
                qty=qty,
                price=prod.price
            )
            db.session.add(item)
            subtotal += float(prod.price) * qty
            
        discount_amt = subtotal * (discount_pct / 100.0)
        net_total = subtotal - discount_amt
        
        sale.total = net_total
        sale.discount_amount = discount_amt
        sale.paid_amount = net_total
        
    # Seeding for Student
    # Create 6 sales distributed across last 15 days
    for i in range(6):
        days_ago = random.randint(0, 14)
        sale_date = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
        shop = random.choice(student_shops)
        pm = random.choice(student_pms)
        
        # Pick 1 to 2 items
        items_count = random.randint(1, 2)
        selected_prods = random.sample(student_products, items_count)
        
        discount_pct = random.choice([0, 0, 5])
        
        sale = models.Sale(
            shop_id=shop.id,
            user_id=student_user.id,
            payment_method_id=pm.id,
            sale_date=sale_date,
            discount_pct=discount_pct,
            total=0.0,
            discount_amount=0.0,
            paid_amount=0.0
        )
        db.session.add(sale)
        db.session.flush()
        
        subtotal = 0.0
        for prod in selected_prods:
            qty = random.randint(1, 2)
            item = models.SaleItem(
                user_id=student_user.id,
                sale_id=sale.id,
                product_id=prod.id,
                qty=qty,
                price=prod.price
            )
            db.session.add(item)
            subtotal += float(prod.price) * qty
            
        discount_amt = subtotal * (discount_pct / 100.0)
        net_total = subtotal - discount_amt
        
        sale.total = net_total
        sale.discount_amount = discount_amt
        sale.paid_amount = net_total

    db.session.commit()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    with app.app_context():
        seed_data()
