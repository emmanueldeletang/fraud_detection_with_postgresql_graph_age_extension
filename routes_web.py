from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from models import db, User, MenuItem, Order, OrderItem, UserLocation
from utils import get_ip_address, get_location_from_ip
from collections import defaultdict
from graph_utils import add_order_to_graph, detect_fraud_patterns
from sqlalchemy.exc import OperationalError, DBAPIError
import time

web_bp = Blueprint('web', __name__)


@web_bp.context_processor
def inject_demo_mode():
    """Inject demo mode status into all templates"""
    return {'demo_mode': current_app.config.get('DEMO_MODE', False)}


def db_retry(max_attempts=3, delay=1):
    """Retry database operations on connection errors"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DBAPIError) as e:
                    if attempt < max_attempts - 1:
                        print(f"Database error, retrying... (attempt {attempt + 1}/{max_attempts})")
                        time.sleep(delay)
                        db.session.rollback()
                        try:
                            db.engine.dispose()
                        except:
                            pass
                    else:
                        raise
        return wrapper
    return decorator


def login_required_web(f):
    """Decorator for web routes that require login"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('web.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required_web(f):
    """Decorator for web routes that require admin"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('web.login'))
        if not session.get('is_admin'):
            flash('Admin access required.', 'danger')
            return redirect(url_for('web.index'))
        return f(*args, **kwargs)
    return decorated_function


@web_bp.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@web_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        city = request.form.get('city')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('web.register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('web.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('web.register'))
        
        user = User(username=username, email=email, city=city)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('web.login'))
    
    return render_template('register.html')


@web_bp.route('/login', methods=['GET', 'POST'])
@db_retry(max_attempts=3, delay=1)
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            user = User.query.filter_by(username=username).first()
        except (OperationalError, DBAPIError) as e:
            flash('Database connection error. Please try again.', 'danger')
            return redirect(url_for('web.login'))
        
        if not user or not user.check_password(password):
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('web.login'))
        
        # Track login location
        ip_address = get_ip_address()
        location_data = get_location_from_ip(ip_address)
        matches_city = location_data['city'].lower() == user.city.lower() if location_data['city'] else None
        
        user_location = UserLocation(
            user_id=user.id,
            ip_address=ip_address,
            city=location_data['city'],
            region=location_data['region'],
            country=location_data['country'],
            latitude=location_data['latitude'],
            longitude=location_data['longitude'],
            matches_user_city=matches_city,
            action='login'
        )
        db.session.add(user_location)
        db.session.commit()
        
        # Set session
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.role == 'admin'
        session['cart'] = []
        
        if matches_city == False:
            flash(f'Welcome {user.username}! Warning: Login detected from {location_data["city"]}, but your registered city is {user.city}.', 'warning')
        else:
            flash(f'Welcome back, {user.username}!', 'success')
        
        return redirect(url_for('web.index'))
    
    return render_template('login.html')


@web_bp.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('web.index'))


@web_bp.route('/menu')
def menu():
    """Display menu"""
    items = MenuItem.query.filter_by(available=True).all()
    
    # Group by category
    menu_by_category = defaultdict(list)
    for item in items:
        menu_by_category[item.category].append(item)
    
    return render_template('menu.html', items=dict(menu_by_category))


@web_bp.route('/cart/add', methods=['POST'])
@login_required_web
def add_to_cart():
    """Add item to cart"""
    item_id = request.form.get('item_id', type=int)
    quantity = request.form.get('quantity', type=int, default=1)
    
    item = MenuItem.query.get(item_id)
    if not item:
        flash('Item not found.', 'danger')
        return redirect(url_for('web.menu'))
    
    cart = session.get('cart', [])
    
    # Check if item already in cart
    found = False
    for cart_item in cart:
        if cart_item['id'] == item_id:
            cart_item['quantity'] += quantity
            found = True
            break
    
    if not found:
        cart.append({
            'id': item.id,
            'name': item.name,
            'price': item.price,
            'quantity': quantity
        })
    
    session['cart'] = cart
    flash(f'{item.name} added to cart!', 'success')
    return redirect(url_for('web.menu'))


@web_bp.route('/cart')
@login_required_web
def cart():
    """View cart"""
    cart_items = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)


@web_bp.route('/cart/remove', methods=['POST'])
@login_required_web
def remove_from_cart():
    """Remove item from cart"""
    item_id = request.form.get('item_id', type=int)
    cart = session.get('cart', [])
    session['cart'] = [item for item in cart if item['id'] != item_id]
    flash('Item removed from cart.', 'info')
    return redirect(url_for('web.cart'))


@web_bp.route('/checkout', methods=['POST'])
@login_required_web
def checkout():
    """Process checkout"""
    cart = session.get('cart', [])
    if not cart:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('web.menu'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    notes = request.form.get('notes', '')
    
    # Track order location
    ip_address = get_ip_address()
    location_data = get_location_from_ip(ip_address)
    matches_city = location_data['city'].lower() == user.city.lower() if location_data['city'] else None
    
    user_location = UserLocation(
        user_id=user.id,
        ip_address=ip_address,
        city=location_data['city'],
        region=location_data['region'],
        country=location_data['country'],
        latitude=location_data['latitude'],
        longitude=location_data['longitude'],
        matches_user_city=matches_city,
        action='order'
    )
    db.session.add(user_location)
    
    # Calculate total
    total_price = sum(item['price'] * item['quantity'] for item in cart)
    
    # Create order
    order = Order(
        user_id=user_id,
        total_price=total_price,
        notes=notes,
        status='pending'
    )
    db.session.add(order)
    db.session.flush()
    
    # Add order items
    for cart_item in cart:
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=cart_item['id'],
            quantity=cart_item['quantity'],
            price_at_order=cart_item['price']
        )
        db.session.add(order_item)
    
    db.session.commit()
    
    # Add order to graph database
    try:
        add_order_to_graph(
            user=user,
            ip_address=ip_address,
            city_detected=location_data['city'],
            order_id=order.id
        )
    except Exception as e:
        print(f"Warning: Could not add order to graph: {e}")
    
    # Clear cart
    session['cart'] = []
    
    if matches_city == False:
        flash(f'Order placed successfully! Warning: Order from {location_data["city"]}, but your registered city is {user.city}.', 'warning')
    else:
        flash('Order placed successfully!', 'success')
    
    return redirect(url_for('web.orders'))


@web_bp.route('/orders')
@login_required_web
def orders():
    """View user orders"""
    user_id = session['user_id']
    user_orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=user_orders)


# Admin routes
@web_bp.route('/admin/menu')
@admin_required_web
def admin_menu():
    """Admin menu management"""
    items = MenuItem.query.all()
    return render_template('admin_menu.html', items=items)


@web_bp.route('/admin/menu/add', methods=['POST'])
@admin_required_web
def admin_add_menu_item():
    """Add menu item"""
    name = request.form.get('name')
    description = request.form.get('description', '')
    price = request.form.get('price', type=float)
    category = request.form.get('category')
    image_url = request.form.get('image_url', '')
    available = 'available' in request.form
    
    item = MenuItem(
        name=name,
        description=description,
        price=price,
        category=category,
        image_url=image_url if image_url else None,
        available=available
    )
    db.session.add(item)
    db.session.commit()
    
    flash('Menu item added successfully!', 'success')
    return redirect(url_for('web.admin_menu'))


@web_bp.route('/admin/menu/edit/<int:item_id>', methods=['GET', 'POST'])
@admin_required_web
def admin_edit_menu_item(item_id):
    """Edit menu item"""
    item = MenuItem.query.get(item_id)
    if not item:
        flash('Menu item not found.', 'danger')
        return redirect(url_for('web.admin_menu'))
    
    if request.method == 'POST':
        item.name = request.form.get('name')
        item.description = request.form.get('description', '')
        item.price = request.form.get('price', type=float)
        item.category = request.form.get('category')
        image_url = request.form.get('image_url', '')
        item.image_url = image_url if image_url else None
        item.available = 'available' in request.form
        
        db.session.commit()
        flash('Menu item updated successfully!', 'success')
        return redirect(url_for('web.admin_menu'))
    
    return render_template('admin_menu_edit.html', item=item)


@web_bp.route('/admin/menu/delete/<int:item_id>', methods=['POST'])
@admin_required_web
def admin_delete_menu_item(item_id):
    """Delete menu item"""
    item = MenuItem.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Menu item deleted successfully!', 'success')
    else:
        flash('Menu item not found.', 'danger')
    return redirect(url_for('web.admin_menu'))


@web_bp.route('/admin/orders')
@admin_required_web
def admin_orders():
    """View all orders"""
    all_orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin_orders.html', orders=all_orders)


@web_bp.route('/admin/orders/status/<int:order_id>', methods=['POST'])
@admin_required_web
def admin_update_order_status(order_id):
    """Update order status"""
    order = Order.query.get(order_id)
    if order:
        status = request.form.get('status')
        order.status = status
        db.session.commit()
        flash(f'Order #{order_id} status updated to {status}!', 'success')
    else:
        flash('Order not found.', 'danger')
    return redirect(url_for('web.admin_orders'))


@web_bp.route('/admin/locations')
@admin_required_web
def admin_locations():
    """View location tracking"""
    locations = UserLocation.query.order_by(UserLocation.timestamp.desc()).limit(100).all()
    return render_template('admin_locations.html', locations=locations)


@web_bp.route('/admin/statistics')
@admin_required_web
def admin_statistics():
    """View order statistics by user"""
    from sqlalchemy import func
    
    # Get user order statistics
    user_stats = db.session.query(
        User.id,
        User.username,
        User.email,
        User.city,
        func.count(Order.id).label('total_orders'),
        func.sum(Order.total_price).label('total_amount'),
        func.avg(Order.total_price).label('avg_order_amount'),
        func.max(Order.created_at).label('last_order_date')
    ).outerjoin(Order, User.id == Order.user_id)\
     .group_by(User.id, User.username, User.email, User.city)\
     .order_by(func.sum(Order.total_price).desc().nullslast())\
     .all()
    
    # Get all orders with details
    orders = Order.query.order_by(Order.created_at.desc()).all()
    
    # Calculate overall statistics
    total_revenue = db.session.query(func.sum(Order.total_price)).scalar() or 0
    total_orders = Order.query.count()
    total_users = User.query.count()
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    overall_stats = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_users': total_users,
        'avg_order_value': avg_order_value
    }
    
    return render_template('admin_statistics.html', 
                         user_stats=user_stats, 
                         orders=orders,
                         overall_stats=overall_stats)


@web_bp.route('/admin/settings', methods=['GET', 'POST'])
@admin_required_web
def admin_settings():
    """Admin settings page"""
    if request.method == 'POST':
        # Toggle demo mode
        demo_mode = request.form.get('demo_mode') == 'on'
        
        # Update .env file
        env_path = '.env'
        try:
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Update DEMO_MODE line
            updated = False
            for i, line in enumerate(lines):
                if line.startswith('DEMO_MODE='):
                    lines[i] = f'DEMO_MODE={str(demo_mode).lower()}\n'
                    updated = True
                    break
            
            # Add if not exists
            if not updated:
                lines.append(f'DEMO_MODE={str(demo_mode).lower()}\n')
            
            with open(env_path, 'w') as f:
                f.writelines(lines)
            
            # Update current app config
            current_app.config['DEMO_MODE'] = demo_mode
            
            flash('Settings saved! Demo mode ' + ('enabled' if demo_mode else 'disabled') + '.', 'success')
        except Exception as e:
            flash(f'Error saving settings: {e}', 'danger')
        
        return redirect(url_for('web.admin_settings'))
    
    return render_template('admin_settings.html')


@web_bp.route('/admin/graph')
@admin_required_web
def admin_graph():
    """View graph analytics"""
    # Get all location data
    locations = UserLocation.query.all()
    users = User.query.all()
    
    # Build graph data
    nodes = []
    edges = []
    node_ids = set()
    
    # Add user nodes
    for user in users:
        user_id = f"user_{user.id}"
        if user_id not in node_ids:
            nodes.append({
                'id': user_id,
                'label': user.username,
                'group': 'user',
                'color': '#4285f4',
                'title': f'User: {user.username}<br>Email: {user.email}<br>City: {user.city}'
            })
            node_ids.add(user_id)
        
        # Add email node
        email_id = f"email_{user.email}"
        if email_id not in node_ids:
            nodes.append({
                'id': email_id,
                'label': user.email,
                'group': 'email',
                'color': '#fbbc04',
                'title': f'Email: {user.email}'
            })
            node_ids.add(email_id)
        
        # Add edge from user to email
        edges.append({
            'from': user_id,
            'to': email_id,
            'label': 'has_email',
            'color': '#fbbc04'
        })
    
    # Add IP, city, region, and country nodes with connections
    for loc in locations:
        user_id = f"user_{loc.user_id}"
        ip_id = f"ip_{loc.ip_address}"
        
        # Add IP node
        if ip_id not in node_ids:
            nodes.append({
                'id': ip_id,
                'label': loc.ip_address,
                'group': 'ip',
                'color': '#ea4335',
                'title': f'IP: {loc.ip_address}'
            })
            node_ids.add(ip_id)
        
        # Add edge from user to IP
        edges.append({
            'from': user_id,
            'to': ip_id,
            'label': 'used_ip',
            'color': '#ea4335'
        })
        
        # Add city node if available
        if loc.city:
            city_id = f"city_{loc.city}_{loc.country}"
            if city_id not in node_ids:
                nodes.append({
                    'id': city_id,
                    'label': loc.city,
                    'group': 'city',
                    'color': '#34a853',
                    'title': f'City: {loc.city}<br>Region: {loc.region}<br>Country: {loc.country}'
                })
                node_ids.add(city_id)
            
            # Add edge from IP to city
            edges.append({
                'from': ip_id,
                'to': city_id,
                'label': 'from_city',
                'color': '#34a853'
            })
        
        # Add region node if available
        if loc.region:
            region_id = f"region_{loc.region}_{loc.country}"
            if region_id not in node_ids:
                nodes.append({
                    'id': region_id,
                    'label': loc.region,
                    'group': 'region',
                    'color': '#9c27b0',
                    'title': f'Region: {loc.region}<br>Country: {loc.country}'
                })
                node_ids.add(region_id)
            
            # Add edge from city to region if city exists
            if loc.city:
                city_id = f"city_{loc.city}_{loc.country}"
                edges.append({
                    'from': city_id,
                    'to': region_id,
                    'label': 'in_region',
                    'color': '#9c27b0'
                })
        
        # Add country node if available
        if loc.country:
            country_id = f"country_{loc.country}"
            if country_id not in node_ids:
                nodes.append({
                    'id': country_id,
                    'label': loc.country,
                    'group': 'country',
                    'color': '#ff9800',
                    'title': f'Country: {loc.country}'
                })
                node_ids.add(country_id)
            
            # Add edge from region to country if region exists, otherwise from city
            if loc.region:
                region_id = f"region_{loc.region}_{loc.country}"
                edges.append({
                    'from': region_id,
                    'to': country_id,
                    'label': 'in_country',
                    'color': '#ff9800'
                })
            elif loc.city:
                city_id = f"city_{loc.city}_{loc.country}"
                edges.append({
                    'from': city_id,
                    'to': country_id,
                    'label': 'in_country',
                    'color': '#ff9800'
                })
    
    graph_data = {
        'nodes': nodes,
        'edges': edges
    }
    
    # Calculate statistics
    ip_usage = {}
    for loc in locations:
        if loc.ip_address not in ip_usage:
            ip_usage[loc.ip_address] = set()
        ip_usage[loc.ip_address].add(loc.user_id)
    
    suspicious_ips = {ip: users for ip, users in ip_usage.items() if len(users) > 1}
    
    stats = {
        'total_users': len(users),
        'total_ips': len(set(loc.ip_address for loc in locations)),
        'total_cities': len(set(loc.city for loc in locations if loc.city)),
        'total_regions': len(set(loc.region for loc in locations if loc.region)),
        'total_countries': len(set(loc.country for loc in locations if loc.country)),
        'suspicious_ips': len(suspicious_ips)
    }
    
    # Fraud alerts
    fraud_alerts = []
    for ip, user_ids in suspicious_ips.items():
        user_names = [User.query.get(uid).username for uid in user_ids]
        fraud_alerts.append({
            'ip': ip,
            'user_count': len(user_ids),
            'users': user_names
        })
    
    return render_template('admin_graph.html', 
                         graph_data=graph_data, 
                         stats=stats,
                         fraud_alerts=fraud_alerts)
