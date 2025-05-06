"""
API module for the Bjorn HVAC Abbreviation System
"""
from flask import Flask

def init_api(app: Flask):
    """Initialize API routes"""
    from .routes import api_bp
    app.register_blueprint(api_bp)
    return app