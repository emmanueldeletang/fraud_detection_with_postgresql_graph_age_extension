from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity
from models import db, User, UserLocation
from utils import get_ip_address, get_location_from_ip, login_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['username', 'email', 'password', 'city']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409
    
    # Create new user
    user = User(
        username=data['username'],
        email=data['email'],
        city=data['city'],
        role=data.get('role', 'user')  # Default to 'user', can be 'admin'
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    data = request.get_json()
    
    if not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    # Find user
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Track login location
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
        action='login'
    )
    db.session.add(user_location)
    db.session.commit()
    
    # Create JWT token
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'user': user.to_dict(),
        'location': {
            'ip_address': ip_address,
            'detected_city': location_data['city'],
            'registered_city': user.city,
            'matches': matches_city
        }
    }), 200


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user information"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200


@auth_bp.route('/locations', methods=['GET'])
@login_required
def get_user_locations():
    """Get user's location history"""
    user_id = get_jwt_identity()
    locations = UserLocation.query.filter_by(user_id=user_id).order_by(UserLocation.timestamp.desc()).all()
    
    return jsonify({
        'locations': [loc.to_dict() for loc in locations]
    }), 200
