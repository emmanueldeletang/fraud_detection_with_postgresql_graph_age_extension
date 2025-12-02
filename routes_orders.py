from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity
from models import db, Order, OrderItem, MenuItem, User, UserLocation
from utils import login_required, admin_required, get_ip_address, get_location_from_ip

orders_bp = Blueprint('orders', __name__, url_prefix='/api/orders')


@orders_bp.route('/', methods=['POST'])
@login_required
def create_order():
    """Create a new order with IP tracking"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Validate items
    if 'items' not in data or not data['items']:
        return jsonify({'error': 'Order must contain at least one item'}), 400
    
    # Track user location for this order
    ip_address = get_ip_address()
    location_data = get_location_from_ip(ip_address)
    
    # Check if IP city matches user's registered city
    matches_city = location_data['city'].lower() == user.city.lower() if location_data['city'] else None
    
    # Store location data
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
    
    # Calculate total and create order
    total_price = 0
    order_items = []
    
    for item_data in data['items']:
        menu_item = MenuItem.query.get(item_data['menu_item_id'])
        
        if not menu_item:
            return jsonify({'error': f'Menu item {item_data["menu_item_id"]} not found'}), 404
        
        if not menu_item.available:
            return jsonify({'error': f'{menu_item.name} is not currently available'}), 400
        
        quantity = item_data.get('quantity', 1)
        if quantity < 1:
            return jsonify({'error': 'Quantity must be at least 1'}), 400
        
        subtotal = menu_item.price * quantity
        total_price += subtotal
        
        order_items.append({
            'menu_item_id': menu_item.id,
            'quantity': quantity,
            'price_at_order': menu_item.price
        })
    
    # Create order
    order = Order(
        user_id=user_id,
        total_price=total_price,
        notes=data.get('notes', ''),
        status='pending'
    )
    
    db.session.add(order)
    db.session.flush()  # Get order ID
    
    # Add order items
    for item_data in order_items:
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=item_data['menu_item_id'],
            quantity=item_data['quantity'],
            price_at_order=item_data['price_at_order']
        )
        db.session.add(order_item)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Order created successfully',
        'order': order.to_dict(),
        'location_tracking': {
            'ip_address': ip_address,
            'detected_city': location_data['city'],
            'registered_city': user.city,
            'matches': matches_city,
            'warning': 'Location mismatch detected' if matches_city is False else None
        }
    }), 201


@orders_bp.route('/', methods=['GET'])
@login_required
def get_orders():
    """Get user's orders"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if user.role == 'admin':
        # Admins can see all orders
        orders = Order.query.order_by(Order.created_at.desc()).all()
    else:
        # Users see only their orders
        orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    
    return jsonify({
        'orders': [order.to_dict() for order in orders],
        'count': len(orders)
    }), 200


@orders_bp.route('/<int:order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    """Get a specific order"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    # Check permissions
    if user.role != 'admin' and order.user_id != user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Get location data for this order
    location = UserLocation.query.filter_by(
        user_id=order.user_id,
        action='order'
    ).order_by(UserLocation.timestamp.desc()).first()
    
    response = order.to_dict()
    if location:
        response['location_info'] = location.to_dict()
    
    return jsonify(response), 200


@orders_bp.route('/<int:order_id>/status', methods=['PUT'])
@admin_required
def update_order_status(order_id):
    """Update order status (Admin only)"""
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    data = request.get_json()
    
    if 'status' not in data:
        return jsonify({'error': 'Status is required'}), 400
    
    valid_statuses = ['pending', 'confirmed', 'preparing', 'delivered', 'cancelled']
    if data['status'] not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
    
    order.status = data['status']
    db.session.commit()
    
    return jsonify({
        'message': 'Order status updated successfully',
        'order': order.to_dict()
    }), 200


@orders_bp.route('/<int:order_id>', methods=['DELETE'])
@login_required
def cancel_order(order_id):
    """Cancel an order (only if pending)"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    # Check permissions
    if user.role != 'admin' and order.user_id != user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Only allow cancellation of pending orders
    if order.status != 'pending' and user.role != 'admin':
        return jsonify({'error': 'Only pending orders can be cancelled'}), 400
    
    order.status = 'cancelled'
    db.session.commit()
    
    return jsonify({
        'message': 'Order cancelled successfully',
        'order': order.to_dict()
    }), 200


@orders_bp.route('/statistics', methods=['GET'])
@admin_required
def get_statistics():
    """Get order statistics (Admin only)"""
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
    
    # Calculate overall statistics
    total_revenue = db.session.query(func.sum(Order.total_price)).scalar() or 0
    total_orders = Order.query.count()
    total_users = User.query.count()
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Format user stats
    user_stats_list = []
    for stat in user_stats:
        user_stats_list.append({
            'user_id': stat.id,
            'username': stat.username,
            'email': stat.email,
            'city': stat.city,
            'total_orders': stat.total_orders or 0,
            'total_amount': float(stat.total_amount or 0),
            'avg_order_amount': float(stat.avg_order_amount or 0),
            'last_order_date': stat.last_order_date.isoformat() if stat.last_order_date else None
        })
    
    return jsonify({
        'overall_stats': {
            'total_revenue': float(total_revenue),
            'total_orders': total_orders,
            'total_users': total_users,
            'avg_order_value': float(avg_order_value)
        },
        'user_stats': user_stats_list
    }), 200
