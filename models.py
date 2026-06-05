from datetime import datetime
from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    profile = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(255), nullable=True)  # pending, rejected, approve
    type = db.Column(db.String(255), nullable=True)  # admin, student

    # Relationships
    shops = db.relationship('Shop', backref='user', lazy=True)
    categories = db.relationship('Category', backref='user', lazy=True)
    products = db.relationship('Product', backref='user', lazy=True)
    payment_methods = db.relationship('PaymentMethod', backref='user', lazy=True)
    sales = db.relationship('Sale', backref='user', lazy=True)
    sale_items = db.relationship('SaleItem', backref='user', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Shop(db.Model):
    __tablename__ = 'shop'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    logo = db.Column(db.String(255), nullable=True)
    description = db.Column(db.String(500), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    sales = db.relationship('Sale', backref='shop', lazy=True)

    def __repr__(self):
        return f"<Shop {self.name}>"


class Category(db.Model):
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    remark = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    products = db.relationship('Product', backref='category', lazy=True)

    def __repr__(self):
        return f"<Category {self.name}>"


class Product(db.Model):
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    cost = db.Column(db.Numeric(10, 2), nullable=True, default=0.0)
    price = db.Column(db.Numeric(10, 2), nullable=True, default=0.0)
    stock = db.Column(db.Numeric(10, 2), nullable=True, default=0.0)
    image = db.Column(db.String(255), nullable=True)
    remark = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    sale_items = db.relationship('SaleItem', backref='product', lazy=True)

    def __repr__(self):
        return f"<Product {self.name}>"


class PaymentMethod(db.Model):
    __tablename__ = 'payment_method'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    remark = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    sales = db.relationship('Sale', backref='payment_method', lazy=True)

    def __repr__(self):
        return f"<PaymentMethod {self.name}>"


class Sale(db.Model):
    __tablename__ = 'sale'

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_method.id'), nullable=False)
    sale_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    discount_pct = db.Column(db.Integer, nullable=False, default=0)
    discount_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)
    paid_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0.0)

    # Relationships
    items = db.relationship('SaleItem', backref='sale', lazy=True)

    def __repr__(self):
        return f"<Sale ID: {self.id}, Total: {self.total}>"


class SaleItem(db.Model):
    __tablename__ = 'sale_item'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=True, default=0.0)

    def __repr__(self):
        return f"<SaleItem ID: {self.id}, Qty: {self.qty}>"
