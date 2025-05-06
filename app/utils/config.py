"""
Configuration management for the Bjorn HVAC Abbreviation System
"""
import os
import json
import logging
from pathlib import Path
import yaml

# Set up logging
logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Centralized configuration management for the application
    """
    
    def __init__(self, config_dir="config"):
        # Default configuration
        self.default_config = {
            "application": {
                "name": "Bjorn HVAC Abbreviation Tool",
                "version": "1.0.0",
                "debug": False,
                "log_level": "INFO"
            },
            "abbreviation": {
                "target_length": 30,
                "use_ml": True,
                "fallback_to_rules": True,
                "min_confidence": 0.5
            },
            "models": {
                "default_model": "hybrid",
                "models_dir": "models",
                "training_data_dir": "data/training"
            },
            "files": {
                "upload_dir": "uploads",
                "max_file_size_mb": 10,
                "allowed_extensions": ["csv", "xlsx", "xls", "txt"]
            },
            "api": {
                "rate_limit": 100,  # requests per minute
                "enable_cors": True,
                "allowed_origins": ["*"]
            },
            "ui": {
                "theme": "light",
                "enable_advanced_features": True,
                "show_debug_info": False
            }
        }
        
        # Active configuration
        self.config = self.default_config.copy()
        
        # Config directory and file paths
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "config.json")
        self.user_config_file = os.path.join(config_dir, "user_config.json")
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)
        
        # Initialize configuration
        self.load_config()
    
    def load_config(self):
        """Load configuration from files"""
        # Try to load base configuration
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    self._merge_config(file_config)
                    logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.error(f"Error loading configuration: {str(e)}")
        else:
            # Create default configuration file
            self.save_config()
        
        # Load user-specific configuration (overrides base config)
        if os.path.exists(self.user_config_file):
            try:
                with open(self.user_config_file, 'r') as f:
                    user_config = json.load(f)
                    self._merge_config(user_config)
                    logger.info(f"Loaded user configuration from {self.user_config_file}")
            except Exception as e:
                logger.error(f"Error loading user configuration: {str(e)}")
    
    def load_from_file(self, file_path):
        """Load configuration from a specific file"""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    if file_path.endswith('.json'):
                        file_config = json.load(f)
                    elif file_path.endswith(('.yaml', '.yml')):
                        file_config = yaml.safe_load(f)
                    else:
                        raise ValueError(f"Unsupported file format: {file_path}")
                        
                    self._merge_config(file_config)
                    logger.info(f"Loaded configuration from {file_path}")
                    return True
            except Exception as e:
                logger.error(f"Error loading configuration from {file_path}: {str(e)}")
                return False
        else:
            logger.error(f"Configuration file not found: {file_path}")
            return False
    
    def save_config(self, user_config=False):
        """
        Save configuration to file
        
        Args:
            user_config: Whether to save as user-specific config
        """
        target_file = self.user_config_file if user_config else self.config_file
        
        try:
            with open(target_file, 'w') as f:
                json.dump(self.config, f, indent=2)
                logger.info(f"Saved configuration to {target_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            return False
    
    def _merge_config(self, new_config):
        """
        Recursively merge new configuration into existing config
        
        Args:
            new_config: New configuration to merge
        """
        def _merge_dict(target, source):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    _merge_dict(target[key], value)
                else:
                    target[key] = value
        
        _merge_dict(self.config, new_config)
    
    def get(self, path, default=None):
        """
        Get configuration value by path
        
        Args:
            path: Dot notation path to configuration value
            default: Default value if path not found
            
        Returns:
            Configuration value or default
        """
        keys = path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, path, value, save_as_user=True):
        """
        Set configuration value by path
        
        Args:
            path: Dot notation path to configuration value
            value: New value to set
            save_as_user: Whether to save as user-specific config
            
        Returns:
            bool: Whether the operation succeeded
        """
        keys = path.split('.')
        target = self.config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        # Set the value
        target[keys[-1]] = value
        
        # Save the configuration
        return self.save_config(user_config=save_as_user)
    
    def reset(self, save=True):
        """
        Reset configuration to defaults
        
        Args:
            save: Whether to save the reset configuration
            
        Returns:
            bool: Whether the operation succeeded
        """
        self.config = self.default_config.copy()
        
        if save:
            return self.save_config()
        
        return True

# Create global configuration instance
config = ConfigManager()