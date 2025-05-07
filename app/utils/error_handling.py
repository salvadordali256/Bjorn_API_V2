"""
Error handling utilities for the Bjorn HVAC Abbreviation System
"""
import logging
import traceback
import functools
import json
from flask import jsonify, request
import os
import time

# Set up logging
logger = logging.getLogger(__name__)

class AppError(Exception):
    """Base exception for application errors"""
    def __init__(self, message, status_code=400, details=None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)

class ValidationError(AppError):
    """Exception for input validation errors"""
    def __init__(self, message, details=None):
        super().__init__(message, status_code=400, details=details)

class ProcessingError(AppError):
    """Exception for processing errors"""
    def __init__(self, message, details=None):
        super().__init__(message, status_code=500, details=details)

class NotFoundError(AppError):
    """Exception for resource not found errors"""
    def __init__(self, message, details=None):
        super().__init__(message, status_code=404, details=details)

def api_error_handler(f):
    """Decorator to handle API errors consistently"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except AppError as e:
            logger.error(f"AppError: {str(e)}")
            if e.details:
                logger.error(f"Details: {e.details}")
            
            return jsonify({
                "success": False,
                "error": str(e),
                "details": e.details,
                "code": e.status_code
            }), e.status_code
        except Exception as e:
            # Log unexpected errors with stack trace
            logger.error(f"Unexpected error: {str(e)}")
            logger.error(traceback.format_exc())
            
            return jsonify({
                "success": False,
                "error": "An unexpected error occurred",
                "code": 500
            }), 500
    
    return decorated_function

def validate_file_upload(request, required_field='file', allowed_extensions=None):
    """Validate file upload request"""
    if required_field not in request.files:
        raise ValidationError(f"No {required_field} part in the request")
        
    file = request.files[required_field]
    if file.filename == '':
        raise ValidationError("No selected file")
    
    if allowed_extensions:
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if ext not in allowed_extensions:
            raise ValidationError(f"File extension not allowed. Allowed extensions: {', '.join(allowed_extensions)}")
    
    return file

def validate_form_data(request, required_fields=None, field_types=None):
    """Validate form data in request"""
    errors = {}
    
    # Check required fields
    if required_fields:
        for field in required_fields:
            if field not in request.form:
                errors[field] = f"Field '{field}' is required"
    
    # Check field types
    if field_types:
        for field, expected_type in field_types.items():
            if field in request.form:
                if expected_type == int:
                    try:
                        int(request.form[field])
                    except ValueError:
                        errors[field] = f"Field '{field}' must be an integer"
                elif expected_type == float:
                    try:
                        float(request.form[field])
                    except ValueError:
                        errors[field] = f"Field '{field}' must be a number"
                elif expected_type == bool:
                    if request.form[field].lower() not in ('true', 'false', '0', '1'):
                        errors[field] = f"Field '{field}' must be a boolean"
    
    if errors:
        raise ValidationError("Invalid form data", details=errors)
    
    return request.form

def log_api_call(endpoint):
    """Log API call with timing information"""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            # Log request
            request_data = {}
            if request.form:
                request_data['form'] = {k: v for k, v in request.form.items()}
            if request.files:
                request_data['files'] = [f.filename for f in request.files.values()]
            
            logger.info(f"API call to {endpoint}: {json.dumps(request_data)}")
            
            # Execute function
            result = f(*args, **kwargs)
            
            # Log timing
            execution_time = time.time() - start_time
            logger.info(f"API call to {endpoint} completed in {execution_time:.2f}s")
            
            return result
        return decorated_function
    return decorator