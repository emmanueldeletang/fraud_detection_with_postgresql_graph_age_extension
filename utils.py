from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from models import User, db
import requests
from sqlalchemy.exc import OperationalError
import time
import random

# Demo IP addresses with their locations
DEMO_IPS = [
    {
        'ip': '195.154.122.113',
        'city': 'Paris',
        'region': 'Île-de-France',
        'country': 'France',
        'latitude': 48.8566,
        'longitude': 2.3522
    },
    {
        'ip': '81.2.69.142',
        'city': 'London',
        'region': 'England',
        'country': 'United Kingdom',
        'latitude': 51.5074,
        'longitude': -0.1278
    },
    {
        'ip': '90.119.169.42',
        'city': 'Bordeaux',
        'region': 'Nouvelle-Aquitaine',
        'country': 'France',
        'latitude': 44.8378,
        'longitude': -0.5792
    },
    {
        'ip': '87.98.154.146',
        'city': 'Lyon',
        'region': 'Auvergne-Rhône-Alpes',
        'country': 'France',
        'latitude': 45.7640,
        'longitude': 4.8357
    }
]

# Track demo IP rotation per session
_demo_ip_counter = 0


def retry_on_db_error(max_retries=3, delay=1):
    """Decorator to retry database operations on connection errors"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return fn(*args, **kwargs)
                except OperationalError as e:
                    if attempt < max_retries - 1:
                        print(f"Database connection error, retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        # Force connection pool refresh
                        db.session.rollback()
                        db.engine.dispose()
                    else:
                        raise
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_ip_address():
    """Get client IP address from request (or demo IP in demo mode)"""
    global _demo_ip_counter
    
    # Check if we're in demo mode
    if hasattr(current_app, 'config') and current_app.config.get('DEMO_MODE', False):
        # Rotate through demo IPs
        demo_data = DEMO_IPS[_demo_ip_counter % len(DEMO_IPS)]
        _demo_ip_counter += 1
        return demo_data['ip']
    
    # Production mode - get real IP
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0]
    else:
        ip = request.remote_addr
    return ip


def get_location_from_ip(ip_address):
    """Get geolocation data from IP address using ipapi.co"""
    try:
        # Check if this is a demo IP
        for demo_data in DEMO_IPS:
            if demo_data['ip'] == ip_address:
                return {
                    'city': demo_data['city'],
                    'region': demo_data['region'],
                    'country': demo_data['country'],
                    'latitude': demo_data['latitude'],
                    'longitude': demo_data['longitude']
                }
        
        # Use ipapi.co for geolocation (free tier available)
        if ip_address in ['127.0.0.1', 'localhost', '::1']:
            # Return default for localhost
            return {
                'city': 'Local',
                'region': 'Local',
                'country': 'Local',
                'latitude': 0.0,
                'longitude': 0.0
            }
        
        response = requests.get(f'https://ipapi.co/{ip_address}/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                'city': data.get('city', ''),
                'region': data.get('region', ''),
                'country': data.get('country_name', ''),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude')
            }
    except Exception as e:
        print(f"Error getting location: {e}")
    
    return {
        'city': 'Unknown',
        'region': 'Unknown',
        'country': 'Unknown',
        'latitude': None,
        'longitude': None
    }


def admin_required(fn):
    """Decorator to require admin role"""
    @wraps(fn)
    @retry_on_db_error(max_retries=3, delay=1)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return fn(*args, **kwargs)
    
    return wrapper


def login_required(fn):
    """Decorator to require authentication"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        return fn(*args, **kwargs)
    
    return wrapper
