import os
import time
from flask import render_template, redirect, url_for, request, flash, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models import User, Shop, Category, Product, PaymentMethod, Sale, SaleItem
from . import dashboard_bp

@dashboard_bp.route('/')
def hello_world():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.admin_index'))
    return redirect(url_for('dashboard.login'))

@dashboard_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.admin_index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('dashboard.login'))

        if user.status != 'approve':
            flash('Your account is not approved yet.', 'warning')
            return redirect(url_for('dashboard.login'))

        login_user(user, remember=remember)
        return redirect(url_for('dashboard.admin_index'))

    return render_template('admin/login.html')

@dashboard_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have logged out.', 'success')
    return redirect(url_for('dashboard.login'))

@dashboard_bp.route('/admin')
@login_required
def admin_index():
    from datetime import datetime, timedelta
    from sqlalchemy import func

    user_count = User.query.count()
    shop_count = Shop.query.count()
    product_count = Product.query.count()
    sale_count = Sale.query.count()

    # 1. 15-day revenue trend query
    fifteen_days_ago = datetime.utcnow() - timedelta(days=15)
    daily_sales = db.session.query(
        func.date(Sale.sale_date).label('day'),
        func.sum(Sale.total).label('revenue')
    ).filter(Sale.sale_date >= fifteen_days_ago)\
     .group_by(func.date(Sale.sale_date))\
     .order_by('day').all()

    # Create mapping of day string -> revenue float
    sales_map = {str(day): float(revenue) for day, revenue in daily_sales}
    revenue_chart_data = []
    for i in range(14, -1, -1):
        day_dt = datetime.now() - timedelta(days=i)
        day_str = day_dt.strftime('%Y-%m-%d')
        revenue_chart_data.append({
            'date': day_dt.strftime('%b %d'),
            'revenue': sales_map.get(day_str, 0.0)
        })

    # 2. Product distribution by Category query
    category_share = db.session.query(
        Category.name,
        func.count(Product.id)
    ).outerjoin(Product, Product.category_id == Category.id)\
     .group_by(Category.id).all()

    category_chart_data = [
        {'category': name, 'count': count}
        for name, count in category_share
    ]

    # 3. Revenue by Shop Location query
    shop_sales_data = db.session.query(
        Shop.name,
        func.sum(Sale.total)
    ).join(Sale, Sale.shop_id == Shop.id)\
     .group_by(Shop.id).all()

    shop_chart_data = [
        {'shop': name, 'total': float(total) if total else 0.0}
        for name, total in shop_sales_data
    ]

    return render_template(
        'admin/dashboard.html',
        user_count=user_count,
        shop_count=shop_count,
        product_count=product_count,
        sale_count=sale_count,
        revenue_chart=revenue_chart_data,
        category_chart=category_chart_data,
        shop_chart=shop_chart_data
    )

# --- USER CRUD ---
@dashboard_bp.route('/admin/users')
@login_required
def list_users():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.paginate(page=page, per_page=5, error_out=False)
    return render_template('admin/users/list.html', users=pagination.items, pagination=pagination)

@dashboard_bp.route('/admin/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        status = request.form.get('status', 'pending')
        utype = request.form.get('type', 'student')

        profile_path = None
        profile_file = request.files.get('profile')
        if profile_file and profile_file.filename != '':
            filename = secure_filename(profile_file.filename)
            filename = f"{int(time.time())}_{filename}"
            upload_dir = os.path.join(current_app.static_folder, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            profile_file.save(os.path.join(upload_dir, filename))
            profile_path = f"/static/uploads/{filename}"

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('dashboard.create_user'))

        new_user = User(username=username, profile=profile_path, status=status, type=utype)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('User created successfully!', 'success')
        return redirect(url_for('dashboard.list_users'))

    return render_template('admin/users/form.html', user=None)

@dashboard_bp.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.username = request.form.get('username')
        user.status = request.form.get('status')
        user.type = request.form.get('type')

        profile_file = request.files.get('profile')
        if profile_file and profile_file.filename != '':
            filename = secure_filename(profile_file.filename)
            filename = f"{int(time.time())}_{filename}"
            upload_dir = os.path.join(current_app.static_folder, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            profile_file.save(os.path.join(upload_dir, filename))
            user.profile = f"/static/uploads/{filename}"

        password = request.form.get('password')
        if password:
            user.set_password(password)

        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('dashboard.list_users'))

    return render_template('admin/users/form.html', user=user)

@dashboard_bp.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('dashboard.list_users'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('dashboard.list_users'))


# --- SHOP CRUD ---
@dashboard_bp.route('/admin/shops')
@login_required
def list_shops():
    page = request.args.get('page', 1, type=int)
    pagination = Shop.query.paginate(page=page, per_page=5, error_out=False)
    return render_template('admin/shops/list.html', shops=pagination.items, pagination=pagination)

@dashboard_bp.route('/admin/shops/create', methods=['GET', 'POST'])
@login_required
def create_shop():
    users = User.query.all()
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        description = request.form.get('description')
        user_id = request.form.get('user_id')

        logo_path = None
        logo_file = request.files.get('logo')
        if logo_file and logo_file.filename != '':
            filename = secure_filename(logo_file.filename)
            filename = f"{int(time.time())}_{filename}"
            upload_dir = os.path.join(current_app.static_folder, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            logo_file.save(os.path.join(upload_dir, filename))
            logo_path = f"/static/uploads/{filename}"

        new_shop = Shop(name=name, address=address, logo=logo_path, description=description, user_id=user_id)
        db.session.add(new_shop)
        db.session.commit()

        flash('Shop created successfully!', 'success')
        return redirect(url_for('dashboard.list_shops'))

    return render_template('admin/shops/form.html', shop=None, users=users)

@dashboard_bp.route('/admin/shops/edit/<int:shop_id>', methods=['GET', 'POST'])
@login_required
def edit_shop(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    users = User.query.all()

    if request.method == 'POST':
        shop.name = request.form.get('name')
        shop.address = request.form.get('address')
        shop.description = request.form.get('description')
        shop.user_id = request.form.get('user_id')

        logo_file = request.files.get('logo')
        if logo_file and logo_file.filename != '':
            filename = secure_filename(logo_file.filename)
            filename = f"{int(time.time())}_{filename}"
            upload_dir = os.path.join(current_app.static_folder, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            logo_file.save(os.path.join(upload_dir, filename))
            shop.logo = f"/static/uploads/{filename}"

        db.session.commit()
        flash('Shop updated successfully!', 'success')
        return redirect(url_for('dashboard.list_shops'))

    return render_template('admin/shops/form.html', shop=shop, users=users)

@dashboard_bp.route('/admin/shops/delete/<int:shop_id>', methods=['POST'])
@login_required
def delete_shop(shop_id):
    shop = Shop.query.get_or_404(shop_id)
    db.session.delete(shop)
    db.session.commit()
    flash('Shop deleted successfully!', 'success')
    return redirect(url_for('dashboard.list_shops'))


# --- CATEGORY CRUD ---
@dashboard_bp.route('/admin/categories')
@login_required
def list_categories():
    page = request.args.get('page', 1, type=int)
    pagination = Category.query.paginate(page=page, per_page=5, error_out=False)
    return render_template('admin/categories/list.html', categories=pagination.items, pagination=pagination)

@dashboard_bp.route('/admin/categories/create', methods=['GET', 'POST'])
@login_required
def create_category():
    users = User.query.all()
    if request.method == 'POST':
        name = request.form.get('name')
        remark = request.form.get('remark')
        user_id = request.form.get('user_id')

        new_cat = Category(name=name, remark=remark, user_id=user_id)
        db.session.add(new_cat)
        db.session.commit()

        flash('Category created successfully!', 'success')
        return redirect(url_for('dashboard.list_categories'))

    return render_template('admin/categories/form.html', category=None, users=users)

@dashboard_bp.route('/admin/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    users = User.query.all()

    if request.method == 'POST':
        category.name = request.form.get('name')
        category.remark = request.form.get('remark')
        category.user_id = request.form.get('user_id')

        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('dashboard.list_categories'))

    return render_template('admin/categories/form.html', category=category, users=users)

@dashboard_bp.route('/admin/categories/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('dashboard.list_categories'))


# --- PRODUCT CRUD ---
@dashboard_bp.route('/admin/products')
@login_required
def list_products():
    page = request.args.get('page', 1, type=int)
    pagination = Product.query.paginate(page=page, per_page=5, error_out=False)
    return render_template('admin/products/list.html', products=pagination.items, pagination=pagination)

@dashboard_bp.route('/admin/products/create', methods=['GET', 'POST'])
@login_required
def create_product():
    categories = Category.query.all()
    users = User.query.all()

    if not categories:
        flash('Please create a category first before adding products.', 'warning')
        return redirect(url_for('dashboard.list_categories'))

    if request.method == 'POST':
        name = request.form.get('name')
        category_id = request.form.get('category_id')
        cost = float(request.form.get('cost') or 0.0)
        price = float(request.form.get('price') or 0.0)
        stock = float(request.form.get('stock') or 0.0)
        remark = request.form.get('remark')
        user_id = request.form.get('user_id')

        image_path = None
        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            filename = f"{int(time.time())}_{filename}"
            upload_dir = os.path.join(current_app.static_folder, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            image_file.save(os.path.join(upload_dir, filename))
            image_path = f"/static/uploads/{filename}"

        new_prod = Product(
            name=name, category_id=category_id, cost=cost, price=price,
            stock=stock, image=image_path, remark=remark, user_id=user_id
        )
        db.session.add(new_prod)
        db.session.commit()

        flash('Product created successfully!', 'success')
        return redirect(url_for('dashboard.list_products'))

    return render_template('admin/products/form.html', product=None, categories=categories, users=users)

@dashboard_bp.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.all()
    users = User.query.all()

    if request.method == 'POST':
        product.name = request.form.get('name')
        product.category_id = request.form.get('category_id')
        product.cost = float(request.form.get('cost') or 0.0)
        product.price = float(request.form.get('price') or 0.0)
        product.stock = float(request.form.get('stock') or 0.0)
        product.remark = request.form.get('remark')
        product.user_id = request.form.get('user_id')

        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            filename = f"{int(time.time())}_{filename}"
            upload_dir = os.path.join(current_app.static_folder, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            image_file.save(os.path.join(upload_dir, filename))
            product.image = f"/static/uploads/{filename}"

        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('dashboard.list_products'))

    return render_template('admin/products/form.html', product=product, categories=categories, users=users)

@dashboard_bp.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('dashboard.list_products'))


# --- PAYMENT METHOD CRUD ---
@dashboard_bp.route('/admin/payment-methods')
@login_required
def list_payment_methods():
    page = request.args.get('page', 1, type=int)
    pagination = PaymentMethod.query.paginate(page=page, per_page=5, error_out=False)
    return render_template('admin/payment_methods/list.html', payment_methods=pagination.items, pagination=pagination)

@dashboard_bp.route('/admin/payment-methods/create', methods=['GET', 'POST'])
@login_required
def create_payment_method():
    users = User.query.all()
    if request.method == 'POST':
        name = request.form.get('name')
        remark = request.form.get('remark')
        user_id = request.form.get('user_id')

        new_pm = PaymentMethod(name=name, remark=remark, user_id=user_id)
        db.session.add(new_pm)
        db.session.commit()

        flash('Payment Method created successfully!', 'success')
        return redirect(url_for('dashboard.list_payment_methods'))

    return render_template('admin/payment_methods/form.html', payment_method=None, users=users)

@dashboard_bp.route('/admin/payment-methods/edit/<int:pm_id>', methods=['GET', 'POST'])
@login_required
def edit_payment_method(pm_id):
    payment_method = PaymentMethod.query.get_or_404(pm_id)
    users = User.query.all()

    if request.method == 'POST':
        payment_method.name = request.form.get('name')
        payment_method.remark = request.form.get('remark')
        payment_method.user_id = request.form.get('user_id')

        db.session.commit()
        flash('Payment Method updated successfully!', 'success')
        return redirect(url_for('dashboard.list_payment_methods'))

    return render_template('admin/payment_methods/form.html', payment_method=payment_method, users=users)

@dashboard_bp.route('/admin/payment-methods/delete/<int:pm_id>', methods=['POST'])
@login_required
def delete_payment_method(pm_id):
    payment_method = PaymentMethod.query.get_or_404(pm_id)
    db.session.delete(payment_method)
    db.session.commit()
    flash('Payment Method deleted successfully!', 'success')
    return redirect(url_for('dashboard.list_payment_methods'))


# --- SALE CRUD ---
@dashboard_bp.route('/admin/sales')
@login_required
def list_sales():
    page = request.args.get('page', 1, type=int)
    pagination = Sale.query.order_by(Sale.sale_date.desc()).paginate(page=page, per_page=5, error_out=False)
    return render_template('admin/sales/list.html', sales=pagination.items, pagination=pagination)

@dashboard_bp.route('/admin/sales/view/<int:sale_id>')
@login_required
def view_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template('admin/sales/view.html', sale=sale)

@dashboard_bp.route('/admin/sales/create', methods=['GET', 'POST'])
@login_required
def create_sale():
    shops = Shop.query.all()
    users = User.query.all()
    products = Product.query.all()
    payment_methods = PaymentMethod.query.all()

    if not shops or not products or not payment_methods:
        flash('Please ensure you have created at least one Shop, Product, and Payment Method before recording a sale.', 'warning')
        return redirect(url_for('dashboard.admin_index'))

    if request.method == 'POST':
        shop_id = request.form.get('shop_id')
        user_id = request.form.get('user_id')
        payment_method_id = request.form.get('payment_method_id')
        discount_pct = int(request.form.get('discount_pct') or 0)
        discount_amount = float(request.form.get('discount_amount') or 0.0)
        total = float(request.form.get('total') or 0.0)
        paid_amount = float(request.form.get('paid_amount') or 0.0)

        # Create Sale object
        new_sale = Sale(
            shop_id=shop_id, user_id=user_id, payment_method_id=payment_method_id,
            discount_pct=discount_pct, discount_amount=discount_amount,
            total=total, paid_amount=paid_amount
        )
        db.session.add(new_sale)
        
        # Read list of products and quantities submitted dynamically
        product_ids = request.form.getlist('product_ids[]')
        qtys = request.form.getlist('qtys[]')

        for prod_id, qty_val in zip(product_ids, qtys):
            qty = int(qty_val)
            product = Product.query.get(prod_id)
            if product:
                # Deduct stock level
                product.stock = float(product.stock) - float(qty)
                
                # Create SaleItem
                item = SaleItem(
                    user_id=user_id,
                    sale=new_sale,
                    product_id=prod_id,
                    qty=qty,
                    price=product.price
                )
                db.session.add(item)

        db.session.commit()
        flash('Sale created successfully!', 'success')
        return redirect(url_for('dashboard.list_sales'))

    return render_template(
        'admin/sales/create.html',
        shops=shops, users=users, products=products, payment_methods=payment_methods
    )

@dashboard_bp.route('/admin/sales/delete/<int:sale_id>', methods=['POST'])
@login_required
def delete_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    
    # Delete sale items first
    for item in sale.items:
        # Revert stock deduction when deleting a sale
        item.product.stock = float(item.product.stock) + float(item.qty)
        db.session.delete(item)
        
    db.session.delete(sale)
    db.session.commit()
    
    flash('Sale and associated items deleted successfully, inventory levels restored.', 'success')
    return redirect(url_for('dashboard.list_sales'))


# --- SALES REPORT ---
@dashboard_bp.route('/admin/reports/sales')
@login_required
def sales_report():
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    from_date_str = request.args.get('from_date', '')
    to_date_str = request.args.get('to_date', '')

    # Default to last 30 days if not specified
    if not from_date_str:
        from_date_dt = datetime.now() - timedelta(days=30)
        from_date_str = from_date_dt.strftime('%Y-%m-%dT%H:%M')
    else:
        try:
            from_date_dt = datetime.fromisoformat(from_date_str)
        except ValueError:
            from_date_dt = datetime.now() - timedelta(days=30)
            from_date_str = from_date_dt.strftime('%Y-%m-%dT%H:%M')

    if not to_date_str:
        to_date_dt = datetime.now()
        to_date_str = to_date_dt.strftime('%Y-%m-%dT%H:%M')
    else:
        try:
            to_date_dt = datetime.fromisoformat(to_date_str)
        except ValueError:
            to_date_dt = datetime.now()
            to_date_str = to_date_dt.strftime('%Y-%m-%dT%H:%M')

    # Query matching sales
    sales_query = Sale.query.filter(Sale.sale_date >= from_date_dt, Sale.sale_date <= to_date_dt)

    # Calculate Aggregates
    sales_subquery = sales_query.with_entities(Sale.id)

    total_sales_val = db.session.query(func.sum(Sale.total)).filter(Sale.id.in_(sales_subquery)).scalar() or 0.0
    total_discount_val = db.session.query(func.sum(Sale.discount_amount)).filter(Sale.id.in_(sales_subquery)).scalar() or 0.0
    total_transactions = sales_query.count()

    # Sales by Shop
    shop_sales = db.session.query(
        Shop.name,
        func.sum(Sale.total).label('shop_total')
    ).join(Sale, Sale.shop_id == Shop.id)\
     .filter(Sale.id.in_(sales_subquery))\
     .group_by(Shop.id).all()

    # Sales by Payment Method
    pm_sales = db.session.query(
        PaymentMethod.name,
        func.sum(Sale.total).label('pm_total')
    ).join(Sale, Sale.payment_method_id == PaymentMethod.id)\
     .filter(Sale.id.in_(sales_subquery))\
     .group_by(PaymentMethod.id).all()

    # Paginated detailed list of sales
    page = request.args.get('page', 1, type=int)
    pagination = sales_query.order_by(Sale.sale_date.desc()).paginate(page=page, per_page=10, error_out=False)

    return render_template(
        'admin/reports/sales.html',
        sales=pagination.items,
        pagination=pagination,
        total_sales=total_sales_val,
        total_discount=total_discount_val,
        total_transactions=total_transactions,
        shop_sales=shop_sales,
        pm_sales=pm_sales,
        from_date=from_date_str,
        to_date=to_date_str
    )


# --- POS ROUTING & API ---
@dashboard_bp.route('/admin/pos')
@login_required
def pos_index():
    shops = Shop.query.all()
    payment_methods = PaymentMethod.query.all()
    return render_template('admin/pos.html', shops=shops, payment_methods=payment_methods)


@dashboard_bp.route('/admin/api/products')
@login_required
def api_list_products():
    products = Product.query.all()
    out = []
    for p in products:
        out.append({
            'id': p.id,
            'title': p.name,
            'price': float(p.price) if p.price else 0.0,
            'category': p.category.name,
            'image': p.image or f"https://placehold.co/170x170?text={p.name}",
            'stock': float(p.stock) if p.stock else 0.0
        })
    return {'products': out}


@dashboard_bp.route('/admin/api/sales/create', methods=['POST'])
@login_required
def api_create_sale():
    data = request.get_json()
    if not data:
        return {'error': 'No data provided'}, 400
    
    shop_id = data.get('shop_id')
    payment_method_id = data.get('payment_method_id')
    discount_pct = int(data.get('discount_pct') or 0)
    discount_amount = float(data.get('discount_amount') or 0.0)
    total = float(data.get('total') or 0.0)
    paid_amount = float(data.get('paid_amount') or 0.0)
    items = data.get('items', [])
    
    if not shop_id or not payment_method_id or not items:
        return {'error': 'Missing required fields or items'}, 400
        
    new_sale = Sale(
        shop_id=shop_id,
        user_id=current_user.id,
        payment_method_id=payment_method_id,
        discount_pct=discount_pct,
        discount_amount=discount_amount,
        total=total,
        paid_amount=paid_amount
    )
    db.session.add(new_sale)
    
    for item_data in items:
        prod_id = item_data.get('product_id')
        qty = int(item_data.get('qty') or 1)
        product = Product.query.get(prod_id)
        if product:
            product.stock = float(product.stock) - float(qty)
            item = SaleItem(
                user_id=current_user.id,
                sale=new_sale,
                product_id=prod_id,
                qty=qty,
                price=product.price
            )
            db.session.add(item)
            
    db.session.commit()
    return {'success': True, 'sale_id': new_sale.id}

