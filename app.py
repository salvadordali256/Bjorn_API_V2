#!/usr/bin/env python3
"""
Bjorn HVAC Abbreviation System
Main application entry point
"""
import os
import sys
import logging
from flask import Flask, request
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Make sure Python can find the actual modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import application components
from app.utils.config import config
from app.utils.logging import setup_logging
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
    
    # Initialize API routes - ONLY use the direct approach that works
    try:
        from app.api.routes import api_bp
        app.register_blueprint(api_bp)
        logger.info("API routes initialized directly")
    except (ImportError, AttributeError) as e:
        logger.error(f"Error initializing API routes: {e}")
    
    # Initialize web routes
    try:
        from app.web.routes import web_bp
        app.register_blueprint(web_bp)
        logger.info("Web routes initialized")
    except (ImportError, AttributeError) as e:
        logger.error(f"Error initializing web routes: {e}")
    
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

        try:
            # Import the model manager to check its configuration
            from app.ml.model_manager import model_manager
            
            # Print model paths and any other configuration
            logger.info(f"Model directory paths: {model_manager.model_dirs if hasattr(model_manager, 'model_dirs') else 'Unknown'}")
            logger.info(f"Expected model types: {model_manager.model_types if hasattr(model_manager, 'model_types') else 'Unknown'}")
            
            # Check for file existence
            if os.path.exists('/app/models/basic/model.pkl'):
                logger.info("Basic model file exists")
            if os.path.exists('/app/models/basic/info.json'):
                logger.info("Basic model info exists")
            if os.path.exists('/app/models/hybrid/model.pkl'):
                logger.info("Hybrid model file exists")
            if os.path.exists('/app/models/hybrid/info.json'):
                logger.info("Hybrid model info exists")
        except Exception as e:
            logger.error(f"Error checking model configuration: {e}")
    
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