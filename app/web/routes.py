"""
Web routes for the Bjorn HVAC Abbreviation System
"""
from flask import Blueprint, render_template, redirect, url_for, request, send_file, jsonify
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint
web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def index():
    """Main application interface"""
    return render_template('index.html')

@web_bp.route('/dashboard')
def dashboard():
    """Dashboard interface"""
    return render_template('dashboard.html')

@web_bp.route('/train')
def train():
    """ML training interface"""
    return render_template('train.html')

@web_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@web_bp.route('/error')
def error():
    """Error page"""
    error_message = request.args.get('message', 'An unknown error occurred')
    return render_template('error.html', error=error_message)