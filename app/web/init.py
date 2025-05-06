"""
Web interface module for the Bjorn HVAC Abbreviation System
"""
from flask import Flask

def init_web(app):
    """Initialize web routes"""
    from .routes import web_bp
    app.register_blueprint(web_bp)
    return app