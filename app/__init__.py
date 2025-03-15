from flask import Flask, jsonify
from app.config import get_config
from app.models.dynamic import init_db
from app.routes.api import api_bp
from app.routes.sse import sse_bp
import logging

def create_app(config_name=None):
    """
    Create and configure the Flask application.
    
    Args:
        config_name (str, optional): The configuration to use. Defaults to None (uses FLASK_ENV).
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Configure the application
    app.config.from_object(get_config())
    
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG if app.config.get('DEBUG') else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize extensions
    with app.app_context():
        init_db(app)
    
    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(sse_bp)
    
    # Add an index route
    @app.route('/')
    def index():
        """Index route to provide basic information about the API."""
        return jsonify({
            'name': 'Model Context Protocol (MCP)',
            'version': '1.0.0',
            'description': 'A Flask application integrated with PostgreSQL and LLM',
            'endpoints': {
                'api': '/api/tables',
                'sse': '/sse/llm'
            }
        })
    
    # Add error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'status': 'error',
            'message': 'Not found'
        }), 404
    
    @app.errorhandler(500)
    def server_error(error):
        app.logger.error(f"Server error: {str(error)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500
    
    return app 