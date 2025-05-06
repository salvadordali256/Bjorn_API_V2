"""
Logging configuration for the Bjorn HVAC Abbreviation System
"""
import os
import logging
import logging.handlers
import json
from datetime import datetime

def setup_logging(log_dir='logs', log_level=None):
    """Set up application logging
    
    Args:
        log_dir: Directory for log files
        log_level: Log level (INFO, DEBUG, etc.)
        
    Returns:
        Logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Get logger
    logger = logging.getLogger()
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Determine log level
    if log_level is None:
        # Try to load from config
        try:
            from app.utils.config import config
            log_level = config.get('application.log_level', 'INFO')
        except ImportError:
            log_level = 'INFO'
    
    # Set log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Create file handlers
    # Main log file
    main_log_file = os.path.join(log_dir, 'app.log')
    file_handler = logging.handlers.RotatingFileHandler(
        main_log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Error log file
    error_log_file = os.path.join(log_dir, 'error.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file, maxBytes=10*1024*1024, backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(pathname)s:%(lineno)d\n%(message)s'
    )
    error_handler.setFormatter(error_formatter)
    logger.addHandler(error_handler)
    
    # Log initialization
    logger.info(f"Logging initialized at level {log_level}")
    
    return logger