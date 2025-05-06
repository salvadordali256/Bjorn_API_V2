#!/usr/bin/env python3
"""
Bjorn HVAC Abbreviation System
Main application entry point
"""
import os
from flask import Flask, request
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import application components
from app.utils.config import config
from app.utils.logging import setup_logging
from app.api import init_api
from app.web import init_web
from app.ml.model_manager import model_manager

# Initialize logging
logger = setup_logging()

def create_app(config_path=None):
    """Create and configure the Flask application"""
    # Initialize Flask app
    app = Flask(__name__)
    
    # Load configuration
    if config_path:
        config.load_from_file(config_path)
    
    # Configure app from settings
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'development-key')
    app.config['MAX_CONTENT_LENGTH'] = config.get('files.max_file_size_mb', 10) * 1024 * 1024
    
    # Initialize API routes
    init_api(app)
    
    # Initialize web routes
    init_web(app)
    
    # Initialize ML models
    if not os.getenv('SKIP_ML_INIT', 'false').lower() == 'true':
        try:
            from app.core.abbreviator import init_ml
            ml_available = init_ml()
            if ml_available:
                logger.info("ML models initialized successfully")
            else:
                logger.warning("ML models not available, using rule-based abbreviation only")
        except Exception as e:
            logger.error(f"Error initializing ML models: {e}")
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def register_error_handlers(app):
    """Register application-wide error handlers"""
    from flask import jsonify, render_template
    
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({"success": False, "error": "Resource not found"}), 404
        return render_template('error.html', error=error), 404
    
    @app.errorhandler(500)
    def server_error(error):
        if request.path.startswith('/api/'):
            return jsonify({"success": False, "error": "Internal server error"}), 500
        return render_template('error.html', error=error), 500

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Run the application
    debug = config.get('application.debug', False)
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    
    app.run(host=host, port=port, debug=debug)