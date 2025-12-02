from flask import Blueprint, request, jsonify
from models import db, MenuItem
from utils import admin_required, login_required

menu_bp = Blueprint('menu', __name__, url_prefix='/api/menu')


@menu_bp.route('/', methods=['GET'])
def get_menu():
    """Get all menu items (available to everyone)"""
    # Optional filters
    category = request.args.get('category')
    available_only = request.args.get('available', 'true').lower() == 'true'
    
    query = MenuItem.query
    
    if category:
        query = query.filter_by(category=category)
    
    if available_only:
        query = query.filter_by(available=True)
    
    items = query.all()
    
    return jsonify({
        'items': [item.to_dict() for item in items],
        'count': len(items)
    }), 200


@menu_bp.route('/<int:item_id>', methods=['GET'])
def get_menu_item(item_id):
    """Get a specific menu item"""
    item = MenuItem.query.get(item_id)
    
    if not item:
        return jsonify({'error': 'Menu item not found'}), 404
    
    return jsonify(item.to_dict()), 200


@menu_bp.route('/', methods=['POST'])
@admin_required
def create_menu_item():
    """Create a new menu item (Admin only)"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'price']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields (name, price)'}), 400
    
    # Create menu item
    item = MenuItem(
        name=data['name'],
        description=data.get('description', ''),
        price=data['price'],
        category=data.get('category', 'general'),
        available=data.get('available', True)
    )
    
    db.session.add(item)
    db.session.commit()
    
    return jsonify({
        'message': 'Menu item created successfully',
        'item': item.to_dict()
    }), 201


@menu_bp.route('/<int:item_id>', methods=['PUT'])
@admin_required
def update_menu_item(item_id):
    """Update a menu item (Admin only)"""
    item = MenuItem.query.get(item_id)
    
    if not item:
        return jsonify({'error': 'Menu item not found'}), 404
    
    data = request.get_json()
    
    # Update fields if provided
    if 'name' in data:
        item.name = data['name']
    if 'description' in data:
        item.description = data['description']
    if 'price' in data:
        item.price = data['price']
    if 'category' in data:
        item.category = data['category']
    if 'available' in data:
        item.available = data['available']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Menu item updated successfully',
        'item': item.to_dict()
    }), 200


@menu_bp.route('/<int:item_id>', methods=['DELETE'])
@admin_required
def delete_menu_item(item_id):
    """Delete a menu item (Admin only)"""
    item = MenuItem.query.get(item_id)
    
    if not item:
        return jsonify({'error': 'Menu item not found'}), 404
    
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({
        'message': 'Menu item deleted successfully'
    }), 200


@menu_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all unique menu categories"""
    categories = db.session.query(MenuItem.category).distinct().all()
    category_list = [cat[0] for cat in categories if cat[0]]
    
    return jsonify({
        'categories': category_list
    }), 200
