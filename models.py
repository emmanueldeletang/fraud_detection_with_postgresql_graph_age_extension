from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication and orders"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', back_populates='user', lazy=True)
    locations = db.relationship('UserLocation', back_populates='user', lazy=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Verify password"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'city': self.city,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }


class MenuItem(db.Model):
    """Menu item model"""
    __tablename__ = 'menu_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))  # e.g., 'appetizer', 'main', 'dessert', 'drink'
    image_url = db.Column(db.String(500))  # URL to the dish image
    available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert menu item to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'category': self.category,
            'image_url': self.image_url,
            'available': self.available,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Order(db.Model):
    """Order model"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'confirmed', 'preparing', 'delivered', 'cancelled'
    total_price = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='orders')
    items = db.relationship('OrderItem', back_populates='order', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert order to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user': self.user.to_dict() if self.user else None,
            'status': self.status,
            'total_price': self.total_price,
            'notes': self.notes,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class OrderItem(db.Model):
    """Order items (junction table with additional fields)"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_at_order = db.Column(db.Float, nullable=False)  # Store price at time of order
    
    # Relationships
    order = db.relationship('Order', back_populates='items')
    menu_item = db.relationship('MenuItem')
    
    @property
    def subtotal(self):
        """Calculate subtotal for this order item"""
        return self.quantity * self.price_at_order
    
    def to_dict(self):
        """Convert order item to dictionary"""
        return {
            'id': self.id,
            'menu_item_id': self.menu_item_id,
            'menu_item': self.menu_item.to_dict() if self.menu_item else None,
            'quantity': self.quantity,
            'price_at_order': self.price_at_order,
            'subtotal': self.subtotal
        }


class UserLocation(db.Model):
    """Track user IP addresses and locations for security and analytics"""
    __tablename__ = 'user_locations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)  # IPv6 support
    city = db.Column(db.String(100))
    region = db.Column(db.String(100))
    country = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    matches_user_city = db.Column(db.Boolean)  # Whether IP city matches user's registered city
    action = db.Column(db.String(50))  # 'login', 'order', etc.
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='locations')
    
    def to_dict(self):
        """Convert location to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'city': self.city,
            'region': self.region,
            'country': self.country,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'matches_user_city': self.matches_user_city,
            'action': self.action,
            'timestamp': self.timestamp.isoformat()
        }
