import os
import time
from functools import wraps
from flask import request, current_app
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    current_user
)
from flask_restx import Resource, fields, Namespace
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from extensions import db, jwt
from models import User, Shop, Category, Product, PaymentMethod, Sale, SaleItem
from . import api

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# --- JWT User Lookup Loader ---
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return db.session.get(User, int(identity))


# --- Namespaces ---
ns_auth = api.namespace('auth', description='JWT Authentication operations')
ns_shops = api.namespace('shops', description='Shop Management Operations')
ns_categories = api.namespace('categories', description='Category Management Operations')
ns_products = api.namespace('products', description='Product Management Operations')
ns_payment_methods = api.namespace('payment-methods', description='Payment Method Operations')
ns_sales = api.namespace('sales', description='Sales and Transaction Operations')
ns_legacy = api.namespace('legacy', description='Legacy Operations')


# --- Flask-RESTX Models for Marshaling/Documentation ---
user_model = api.model('User', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of the user'),
    'username': fields.String(required=True, description='The username'),
    'status': fields.String(description='Status (pending, rejected, approve)'),
    'type': fields.String(description='Role (admin, student)'),
    'profile': fields.String(description='Profile picture path')
})

shop_model = api.model('Shop', {
    'name': fields.String(required=True, description='Shop name'),
    'address': fields.String(required=True, description='Shop address'),
    'logo': fields.String(description='Shop logo path/URL'),
    'description': fields.String(description='Shop description')
})

shop_response_model = api.clone('ShopResponse', shop_model, {
    'id': fields.Integer(readOnly=True, description='The shop identifier')
})

shop_id_expect_model = api.model('ShopIdExpect', {
    'shop_id': fields.Integer(required=True, description='Shop ID')
})

shop_update_model = api.clone('ShopUpdate', shop_model, {
    'shop_id': fields.Integer(required=True, description='Shop ID')
})

category_model = api.model('Category', {
    'name': fields.String(required=True, description='Category name'),
    'remark': fields.String(description='Category description/remark')
})

category_response_model = api.clone('CategoryResponse', category_model, {
    'id': fields.Integer(readOnly=True, description='Category ID')
})

category_id_expect_model = api.model('CategoryIdExpect', {
    'category_id': fields.Integer(required=True, description='Category ID')
})

category_update_model = api.clone('CategoryUpdate', category_model, {
    'category_id': fields.Integer(required=True, description='Category ID')
})

product_model = api.model('Product', {
    'name': fields.String(required=True, description='Product name'),
    'category_id': fields.Integer(required=True, description='Category ID'),
    'cost': fields.Float(description='Product cost price'),
    'price': fields.Float(required=True, description='Product retail price'),
    'stock': fields.Float(description='Current inventory stock'),
    'image': fields.String(description='Product image path/URL'),
    'remark': fields.String(description='Product remark')
})

product_response_model = api.clone('ProductResponse', product_model, {
    'id': fields.Integer(readOnly=True, description='Product ID')
})

product_id_expect_model = api.model('ProductIdExpect', {
    'product_id': fields.Integer(required=True, description='Product ID')
})

product_update_model = api.clone('ProductUpdate', product_model, {
    'product_id': fields.Integer(required=True, description='Product ID')
})

product_parser = ns_products.parser()
product_parser.add_argument('name', type=str, location='form', required=True, help='Product name')
product_parser.add_argument('category_id', type=int, location='form', required=True, help='Category ID')
product_parser.add_argument('cost', type=float, location='form', help='Product cost price')
product_parser.add_argument('price', type=float, location='form', required=True, help='Product retail price')
product_parser.add_argument('stock', type=float, location='form', help='Current inventory stock')
product_parser.add_argument('image', type=FileStorage, location='files', help='Product image file')
product_parser.add_argument('remark', type=str, location='form', help='Product remark')

product_update_parser = ns_products.parser()
product_update_parser.add_argument('product_id', type=int, location='form', required=True, help='Product ID')
product_update_parser.add_argument('name', type=str, location='form', help='Product name')
product_update_parser.add_argument('category_id', type=int, location='form', help='Category ID')
product_update_parser.add_argument('cost', type=float, location='form', help='Product cost price')
product_update_parser.add_argument('price', type=float, location='form', help='Product retail price')
product_update_parser.add_argument('stock', type=float, location='form', help='Current inventory stock')
product_update_parser.add_argument('image', type=FileStorage, location='files', help='Product image file')
product_update_parser.add_argument('remark', type=str, location='form', help='Product remark')

payment_method_model = api.model('PaymentMethod', {
    'name': fields.String(required=True, description='Payment Method name'),
    'remark': fields.String(description='Payment Method remark')
})

payment_method_response_model = api.clone('PaymentMethodResponse', payment_method_model, {
    'id': fields.Integer(readOnly=True, description='Payment Method ID')
})

pm_id_expect_model = api.model('PaymentMethodIdExpect', {
    'pm_id': fields.Integer(required=True, description='Payment Method ID')
})

pm_update_model = api.clone('PaymentMethodUpdate', payment_method_model, {
    'pm_id': fields.Integer(required=True, description='Payment Method ID')
})

sale_item_model = api.model('SaleItem', {
    'product_id': fields.Integer(required=True, description='Product ID'),
    'qty': fields.Integer(required=True, description='Quantity purchased'),
    'price': fields.Float(description='Price per unit (if blank, uses Product.price)')
})

sale_item_response_model = api.model('SaleItemResponse', {
    'id': fields.Integer(readOnly=True),
    'product_id': fields.Integer(),
    'product_name': fields.String(attribute=lambda x: x.product.name if x.product else 'Unknown'),
    'qty': fields.Integer(),
    'price': fields.Float()
})

sale_model = api.model('Sale', {
    'shop_id': fields.Integer(required=True, description='Shop ID'),
    'payment_method_id': fields.Integer(required=True, description='Payment Method ID'),
    'discount_pct': fields.Integer(description='Discount percentage', default=0),
    'discount_amount': fields.Float(description='Computed discount amount', default=0.0),
    'total': fields.Float(description='Computed total amount', default=0.0),
    'paid_amount': fields.Float(required=True, description='Amount paid by customer'),
    'items': fields.List(fields.Nested(sale_item_model), required=True, description='List of sale items')
})

sale_response_model = api.model('SaleResponse', {
    'id': fields.Integer(readOnly=True),
    'shop_id': fields.Integer(),
    'shop_name': fields.String(attribute=lambda x: x.shop.name if x.shop else 'Unknown'),
    'payment_method_id': fields.Integer(),
    'payment_method_name': fields.String(attribute=lambda x: x.payment_method.name if x.payment_method else 'Unknown'),
    'sale_date': fields.String(attribute=lambda x: x.sale_date.isoformat()),
    'total': fields.Float(),
    'discount_pct': fields.Integer(),
    'discount_amount': fields.Float(),
    'paid_amount': fields.Float(),
    'items': fields.List(fields.Nested(sale_item_response_model))
})

login_input_model = api.model('LoginInput', {
    'username': fields.String(required=True, description='The username'),
    'password': fields.String(required=True, description='The password')
})

login_response_model = api.model('LoginResponse', {
    'access_token': fields.String(description='The JWT access token'),
    'user': fields.Nested(user_model, description='Authenticated user details')
})

register_input_model = api.model('RegisterInput', {
    'username': fields.String(required=True, description='The username'),
    'password': fields.String(required=True, description='The password')
})

student_input_model = api.model('StudentInput', {
    'name': fields.String(required=True, description='Student name'),
    'email': fields.String(required=True, description='Student email'),
    'photo': fields.String(required=True, description='Student photo (Base64 data or filename)')
})

sale_id_expect_model = api.model('SaleIdExpect', {
    'sale_id': fields.Integer(required=True, description='Sale ID')
})

legacy_user_expect_model = api.model('LegacyUserExpect', {
    'user_id': fields.Integer(required=True, description='User ID'),
    'name': fields.String(required=True, description='Name')
})


# --- AUTHENTICATION OPERATIONS ---
@ns_auth.route('/login')
class AuthLogin(Resource):
    @ns_auth.expect(login_input_model)
    @ns_auth.marshal_with(login_response_model)
    def post(self):
        """Exchange username/password for a JWT access token"""
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            ns_auth.abort(401, "Invalid username or password")
            
        if user.status != 'approve':
            ns_auth.abort(403, "User account is not approved yet")
            
        access_token = create_access_token(identity=str(user.id))
        return {
            'access_token': access_token,
            'user': user
        }


@ns_auth.route('/register')
class AuthRegister(Resource):
    @ns_auth.expect(register_input_model)
    @ns_auth.marshal_with(user_model, code=201)
    def post(self):
        """Register a new student account (status pending)"""
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            ns_auth.abort(400, "Username and password are required")
            
        if User.query.filter_by(username=username).first():
            ns_auth.abort(400, "Username already exists")
            
        new_user = User(
            username=username,
            status='pending',
            type='student'
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return new_user, 201


# --- LEGACY / CUSTOM ENDPOINTS ---
@ns_legacy.route("/legacy-users/detail")
class LegacyUserList(Resource):
    @ns_legacy.expect(legacy_user_expect_model)
    def post(self):
        data = request.json
        user_id = data.get('user_id')
        name = data.get('name')
        return [{"id": user_id, "name": name}]


@ns_legacy.route("/students")
class StudentList(Resource):
    @api.doc(params={
        "page": {
            "description": "Page number",
            "type": "integer",
            "location": "args",
            "default": 1
        },
        "per_page": {
            "description": "Items per page",
            "type": "integer",
            "location": "args",
            "default": 20
        },
        "keyword": {
            "description": "Search keyword",
            "type": "string",
            "location": "args"
        }
    })
    def get(self):
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        keyword = request.args.get("keyword", "", type=str)

        return {
            "page": page,
            "per_page": per_page,
            "keyword": keyword
        }

    @ns_legacy.expect(student_input_model)
    def post(self):
        data = request.json
        name = data.get("name")
        email = data.get("email")
        photo_data = data.get("photo")

        filename = None

        if photo_data:
            if photo_data.startswith("data:image"):
                import base64
                header, encoded = photo_data.split(",", 1)
                file_ext = header.split(";")[0].split("/")[1]
                filename = f"student_{int(time.time())}.{file_ext}"
                with open(os.path.join(UPLOAD_FOLDER, filename), "wb") as fh:
                    fh.write(base64.b64decode(encoded))
            else:
                filename = photo_data

        return {
            "message": "Student created",
            "name": name,
            "email": email,
            "photo": filename
        }, 201


# --- NEW RESTFUL ENDPOINTS FOR ALL MODULES ---

# 2. Shops Namespace
@ns_shops.route('/')
class ApiShopList(Resource):
    @jwt_required()
    @ns_shops.marshal_list_with(shop_response_model)
    def get(self):
        """List all shops owned by the logged-in user"""
        return Shop.query.filter_by(user_id=current_user.id).all()

    @jwt_required()
    @ns_shops.expect(shop_model)
    @ns_shops.marshal_with(shop_response_model, code=201)
    def post(self):
        """Create a new shop"""
        data = request.json
        new_shop = Shop(
            name=data.get('name'),
            address=data.get('address'),
            logo=data.get('logo'),
            description=data.get('description'),
            user_id=current_user.id
        )
        db.session.add(new_shop)
        db.session.commit()
        return new_shop, 201


@ns_shops.route('/detail')
@ns_shops.response(404, 'Shop not found')
class ApiShopDetail(Resource):
    @jwt_required()
    @ns_shops.expect(shop_id_expect_model)
    @ns_shops.marshal_with(shop_response_model)
    def post(self):
        """Get a shop by ID"""
        data = request.json
        shop_id = data.get('shop_id')
        shop = Shop.query.filter_by(id=shop_id, user_id=current_user.id).first_or_404()
        return shop

    @jwt_required()
    @ns_shops.expect(shop_update_model)
    @ns_shops.marshal_with(shop_response_model)
    def put(self):
        """Update a shop"""
        data = request.json
        shop_id = data.get('shop_id')
        shop = Shop.query.filter_by(id=shop_id, user_id=current_user.id).first_or_404()
        shop.name = data.get('name', shop.name)
        shop.address = data.get('address', shop.address)
        shop.logo = data.get('logo', shop.logo)
        shop.description = data.get('description', shop.description)
        db.session.commit()
        return shop

    @jwt_required()
    @ns_shops.expect(shop_id_expect_model)
    def delete(self):
        """Delete a shop"""
        data = request.json
        shop_id = data.get('shop_id')
        shop = Shop.query.filter_by(id=shop_id, user_id=current_user.id).first_or_404()
        db.session.delete(shop)
        db.session.commit()
        return {'message': 'Shop deleted successfully'}


# 3. Categories Namespace
@ns_categories.route('/')
class ApiCategoryList(Resource):
    @jwt_required()
    @ns_categories.marshal_list_with(category_response_model)
    def get(self):
        """List all categories owned by the logged-in user"""
        return Category.query.filter_by(user_id=current_user.id).all()

    @jwt_required()
    @ns_categories.expect(category_model)
    @ns_categories.marshal_with(category_response_model, code=201)
    def post(self):
        """Create a new category"""
        data = request.json
        new_cat = Category(
            name=data.get('name'),
            remark=data.get('remark'),
            user_id=current_user.id
        )
        db.session.add(new_cat)
        db.session.commit()
        return new_cat, 201


@ns_categories.route('/detail')
@ns_categories.response(404, 'Category not found')
class ApiCategoryDetail(Resource):
    @jwt_required()
    @ns_categories.expect(category_id_expect_model)
    @ns_categories.marshal_with(category_response_model)
    def post(self):
        """Get a category by ID"""
        data = request.json
        category_id = data.get('category_id')
        cat = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
        return cat

    @jwt_required()
    @ns_categories.expect(category_update_model)
    @ns_categories.marshal_with(category_response_model)
    def put(self):
        """Update a category"""
        data = request.json
        category_id = data.get('category_id')
        cat = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
        cat.name = data.get('name', cat.name)
        cat.remark = data.get('remark', cat.remark)
        db.session.commit()
        return cat

    @jwt_required()
    @ns_categories.expect(category_id_expect_model)
    def delete(self):
        """Delete a category"""
        data = request.json
        category_id = data.get('category_id')
        cat = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
        db.session.delete(cat)
        db.session.commit()
        return {'message': 'Category deleted successfully'}


# 4. Products Namespace
@ns_products.route('/')
class ApiProductList(Resource):
    @jwt_required()
    @ns_products.marshal_list_with(product_response_model)
    def get(self):
        """List all products owned by the logged-in user"""
        return Product.query.filter_by(user_id=current_user.id).all()

    @jwt_required()
    @ns_products.expect(product_parser)
    @ns_products.marshal_with(product_response_model, code=201)
    def post(self):
        """Create a new product"""
        args = product_parser.parse_args()
        cat_id = args.get('category_id')
        Category.query.filter_by(id=cat_id, user_id=current_user.id).first_or_404(description="Invalid category ID")
        
        image_file = args.get('image')
        image_path = None
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            filename = f"{int(time.time())}_{filename}"
            upload_dir = os.path.join(current_app.static_folder, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            image_file.save(os.path.join(upload_dir, filename))
            image_path = f"/static/uploads/{filename}"

        new_prod = Product(
            name=args.get('name'),
            category_id=cat_id,
            cost=args.get('cost') or 0.0,
            price=args.get('price') or 0.0,
            stock=args.get('stock') or 0.0,
            image=image_path,
            remark=args.get('remark'),
            user_id=current_user.id
        )
        db.session.add(new_prod)
        db.session.commit()
        return new_prod, 201


@ns_products.route('/detail')
@ns_products.response(404, 'Product not found')
class ApiProductDetail(Resource):
    @jwt_required()
    @ns_products.expect(product_id_expect_model)
    @ns_products.marshal_with(product_response_model)
    def post(self):
        """Get a product by ID"""
        data = request.json
        product_id = data.get('product_id')
        prod = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
        return prod

    @jwt_required()
    @ns_products.expect(product_update_parser)
    @ns_products.marshal_with(product_response_model)
    def put(self):
        """Update a product"""
        args = product_update_parser.parse_args()
        product_id = args.get('product_id')
        prod = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
        
        cat_id = args.get('category_id')
        if cat_id is not None:
            Category.query.filter_by(id=cat_id, user_id=current_user.id).first_or_404(description="Invalid category ID")
            prod.category_id = cat_id
            
        if args.get('name') is not None:
            prod.name = args.get('name')
        if args.get('cost') is not None:
            prod.cost = args.get('cost')
        if args.get('price') is not None:
            prod.price = args.get('price')
        if args.get('stock') is not None:
            prod.stock = args.get('stock')
        if args.get('remark') is not None:
            prod.remark = args.get('remark')
            
        image_file = args.get('image')
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            filename = f"{int(time.time())}_{filename}"
            upload_dir = os.path.join(current_app.static_folder, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            image_file.save(os.path.join(upload_dir, filename))
            prod.image = f"/static/uploads/{filename}"
            
        db.session.commit()
        return prod

    @jwt_required()
    @ns_products.expect(product_id_expect_model)
    def delete(self):
        """Delete a product"""
        data = request.json
        product_id = data.get('product_id')
        prod = Product.query.filter_by(id=product_id, user_id=current_user.id).first_or_404()
        db.session.delete(prod)
        db.session.commit()
        return {'message': 'Product deleted successfully'}


# 5. Payment Methods Namespace
@ns_payment_methods.route('/')
class ApiPaymentMethodList(Resource):
    @jwt_required()
    @ns_payment_methods.marshal_list_with(payment_method_response_model)
    def get(self):
        """List all payment methods owned by the logged-in user"""
        return PaymentMethod.query.filter_by(user_id=current_user.id).all()

    @jwt_required()
    @ns_payment_methods.expect(payment_method_model)
    @ns_payment_methods.marshal_with(payment_method_response_model, code=201)
    def post(self):
        """Create a new payment method"""
        data = request.json
        new_pm = PaymentMethod(
            name=data.get('name'),
            remark=data.get('remark'),
            user_id=current_user.id
        )
        db.session.add(new_pm)
        db.session.commit()
        return new_pm, 201


@ns_payment_methods.route('/detail')
@ns_payment_methods.response(404, 'Payment Method not found')
class ApiPaymentMethodDetail(Resource):
    @jwt_required()
    @ns_payment_methods.expect(pm_id_expect_model)
    @ns_payment_methods.marshal_with(payment_method_response_model)
    def post(self):
        """Get a payment method by ID"""
        data = request.json
        pm_id = data.get('pm_id')
        pm = PaymentMethod.query.filter_by(id=pm_id, user_id=current_user.id).first_or_404()
        return pm

    @jwt_required()
    @ns_payment_methods.expect(pm_update_model)
    @ns_payment_methods.marshal_with(payment_method_response_model)
    def put(self):
        """Update a payment method"""
        data = request.json
        pm_id = data.get('pm_id')
        pm = PaymentMethod.query.filter_by(id=pm_id, user_id=current_user.id).first_or_404()
        pm.name = data.get('name', pm.name)
        pm.remark = data.get('remark', pm.remark)
        db.session.commit()
        return pm

    @jwt_required()
    @ns_payment_methods.expect(pm_id_expect_model)
    def delete(self):
        """Delete a payment method"""
        data = request.json
        pm_id = data.get('pm_id')
        pm = PaymentMethod.query.filter_by(id=pm_id, user_id=current_user.id).first_or_404()
        db.session.delete(pm)
        db.session.commit()
        return {'message': 'Payment Method deleted successfully'}


# 6. Sales Namespace
@ns_sales.route('/')
class ApiSaleList(Resource):
    @jwt_required()
    @ns_sales.marshal_list_with(sale_response_model)
    def get(self):
        """List all sales owned by the logged-in user"""
        return Sale.query.filter_by(user_id=current_user.id).order_by(Sale.sale_date.desc()).all()

    @jwt_required()
    @ns_sales.expect(sale_model)
    @ns_sales.marshal_with(sale_response_model, code=201)
    def post(self):
        """Create a new sale transaction (POS Checkout)"""
        data = request.json
        shop_id = data.get('shop_id')
        payment_method_id = data.get('payment_method_id')
        items = data.get('items', [])
        discount_pct = int(data.get('discount_pct') or 0)
        paid_amount = float(data.get('paid_amount') or 0.0)

        # Enforce validation of referenced models (must be owned by the user)
        Shop.query.filter_by(id=shop_id, user_id=current_user.id).first_or_404(description="Invalid Shop ID")
        PaymentMethod.query.filter_by(id=payment_method_id, user_id=current_user.id).first_or_404(description="Invalid Payment Method ID")

        if not items:
            ns_sales.abort(400, "Missing sale items")

        # Create base sale record
        new_sale = Sale(
            shop_id=shop_id,
            user_id=current_user.id,
            payment_method_id=payment_method_id,
            discount_pct=discount_pct,
            total=0.0,
            discount_amount=0.0,
            paid_amount=paid_amount
        )
        db.session.add(new_sale)
        db.session.flush() # Generate ID

        subtotal = 0.0
        for item_data in items:
            prod_id = item_data.get('product_id')
            qty = int(item_data.get('qty') or 1)
            
            # Retrieve product and check ownership
            product = Product.query.filter_by(id=prod_id, user_id=current_user.id).first()
            if not product:
                db.session.rollback()
                ns_sales.abort(404, f"Product ID {prod_id} not found or unauthorized.")
                
            # Verify and update stock
            product.stock = float(product.stock) - float(qty)
            
            price_used = float(item_data.get('price') or product.price)
            
            sale_item = SaleItem(
                user_id=current_user.id,
                sale_id=new_sale.id,
                product_id=prod_id,
                qty=qty,
                price=price_used
            )
            db.session.add(sale_item)
            subtotal += price_used * qty

        discount_amount = subtotal * (discount_pct / 100.0)
        total = subtotal - discount_amount

        new_sale.total = total
        new_sale.discount_amount = discount_amount
        
        db.session.commit()
        return new_sale, 201


@ns_sales.route('/detail')
@ns_sales.response(404, 'Sale not found')
class ApiSaleDetail(Resource):
    @jwt_required()
    @ns_sales.expect(sale_id_expect_model)
    @ns_sales.marshal_with(sale_response_model)
    def post(self):
        """Get sale invoice details by ID"""
        data = request.json
        sale_id = data.get('sale_id')
        sale = Sale.query.filter_by(id=sale_id, user_id=current_user.id).first_or_404()
        return sale
