from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config
from models import db
from routes_auth import auth_bp
from routes_menu import menu_bp
from routes_orders import orders_bp
from routes_web import web_bp
from sqlalchemy import event
from sqlalchemy.engine import Engine
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app():
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SECRET_KEY'] = app.config['JWT_SECRET_KEY']  # For session management
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    CORS(app)
    
    # Add connection event handlers
    @event.listens_for(Engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        logger.info("Database connection established")
    
    @event.listens_for(Engine, "close")
    def receive_close(dbapi_conn, connection_record):
        logger.warning("Database connection closed")
    
    # Register blueprints
    app.register_blueprint(auth_bp)  # API routes
    app.register_blueprint(menu_bp)  # API routes
    app.register_blueprint(orders_bp)  # API routes
    app.register_blueprint(web_bp)  # Web UI routes
    
    # API health check endpoint
    @app.route('/api')
    def api_index():
        return jsonify({
            'message': 'Restaurant API',
            'version': '1.0',
            'endpoints': {
                'auth': '/api/auth',
                'menu': '/api/menu',
                'orders': '/api/orders'
            }
        })
    
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'healthy'}), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token'}), 401
    
    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return jsonify({'error': 'Missing authorization token'}), 401
    
    return app


if __name__ == '__main__':
    app = create_app()
    
    # Create tables
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
