"""
Model management for the Bjorn HVAC Abbreviation System
"""
import os
import json
import joblib
import logging
import shutil
import datetime
from pathlib import Path
import numpy as np

# Create logger
logger = logging.getLogger(__name__)

class ModelManager:
    """
    Manages abbreviation models with versioning, caching, and metrics
    """
    
    def __init__(self, models_dir="models"):
        self.models_dir = models_dir
        self.active_models = {}
        self.model_metrics = {}
        self.model_cache = {}
        
        # Ensure models directory exists
        os.makedirs(models_dir, exist_ok=True)
        
        # Load model registry
        self.registry_path = os.path.join(models_dir, "model_registry.json")
        self.load_registry()
    
    def load_registry(self):
        """Load model registry from disk"""
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, 'r') as f:
                    registry_data = json.load(f)
                    self.active_models = registry_data.get('active_models', {})
                    self.model_metrics = registry_data.get('model_metrics', {})
                    logger.info(f"Loaded model registry with {len(self.active_models)} active models")
            except Exception as e:
                logger.error(f"Error loading model registry: {str(e)}")
                # Initialize empty registry
                self.active_models = {}
                self.model_metrics = {}
        else:
            # Initialize empty registry
            self.active_models = {}
            self.model_metrics = {}
            self.save_registry()
    
    def save_registry(self):
        """Save model registry to disk"""
        try:
            registry_data = {
                'active_models': self.active_models,
                'model_metrics': self.model_metrics,
                'last_updated': datetime.datetime.now().isoformat()
            }
            
            with open(self.registry_path, 'w') as f:
                json.dump(registry_data, f, indent=2)
                
            logger.info("Saved model registry")
        except Exception as e:
            logger.error(f"Error saving model registry: {str(e)}")
    
    def register_model(self, model_type, model_path, metrics=None, make_active=True):
        """
        Register a new model in the registry
        
        Args:
            model_type: Type of model (e.g., 'hybrid', 'basic')
            model_path: Path to the model file
            metrics: Dictionary of model metrics
            make_active: Whether to make this the active model for its type
            
        Returns:
            model_id: Unique ID for the registered model
        """
        # Generate a version-based model ID
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        model_id = f"{model_type}_{timestamp}"
        
        # Add to registry
        if model_type not in self.model_metrics:
            self.model_metrics[model_type] = {}
        
        self.model_metrics[model_type][model_id] = {
            'path': model_path,
            'timestamp': timestamp,
            'metrics': metrics or {},
            'type': model_type
        }
        
        # Set as active model if requested
        if make_active:
            self.active_models[model_type] = model_id
        
        # Save updated registry
        self.save_registry()
        
        logger.info(f"Registered model {model_id} of type {model_type}")
        return model_id
    
    def get_active_model(self, model_type):
        """
        Get the active model for a given type
        
        Args:
            model_type: Type of model to retrieve
            
        Returns:
            model: The loaded model instance or None if not found
        """
        # Check if we have an active model of this type
        if model_type not in self.active_models:
            logger.warning(f"No active model of type {model_type}")
            return None
        
        model_id = self.active_models[model_type]
        
        # Check if model is already loaded in cache
        if model_id in self.model_cache:
            logger.debug(f"Using cached model {model_id}")
            return self.model_cache[model_id]
        
        # Get model info from registry
        if model_type not in self.model_metrics or model_id not in self.model_metrics[model_type]:
            logger.error(f"Model {model_id} not found in registry")
            return None
        
        model_info = self.model_metrics[model_type][model_id]
        model_path = model_info['path']
        
        # Ensure model file exists
        if not os.path.exists(model_path):
            logger.error(f"Model file not found: {model_path}")
            return None
        
        # Load model based on type
        try:
            if model_type == 'hybrid':
                from app.ml.hybrid_model import HybridAbbreviationModel
                model = HybridAbbreviationModel()
            else:
                from app.ml.abbreviation_model import AbbreviationModel
                model = AbbreviationModel()
            
            # Load the model
            model.load(model_path)
            
            # Add to cache
            self.model_cache[model_id] = model
            
            logger.info(f"Loaded model {model_id} from {model_path}")
            return model
            
        except Exception as e:
            logger.error(f"Error loading model {model_id}: {str(e)}")
            return None
    
    def list_available_models(self, model_type=None):
        """
        List available models
        
        Args:
            model_type: Optional type filter
            
        Returns:
            models: Dictionary of available models and their metrics
        """
        if model_type:
            return self.model_metrics.get(model_type, {})
        else:
            return self.model_metrics
    
    def set_active_model(self, model_type, model_id):
        """
        Set the active model for a given type
        
        Args:
            model_type: Type of model
            model_id: ID of model to make active
            
        Returns:
            success: Whether the operation succeeded
        """
        # Validate model exists
        if model_type not in self.model_metrics or model_id not in self.model_metrics[model_type]:
            logger.error(f"Model {model_id} not found in registry")
            return False
        
        # Update active model
        self.active_models[model_type] = model_id
        
        # Clear cache for this model type to force reload
        for cached_id in list(self.model_cache.keys()):
            if cached_id.startswith(model_type + '_'):
                del self.model_cache[cached_id]
        
        # Save registry
        self.save_registry()
        
        logger.info(f"Set {model_id} as active model for type {model_type}")
        return True
    
    def update_model_metrics(self, model_id, metrics):
        """
        Update metrics for a model
        
        Args:
            model_id: ID of the model
            metrics: Dictionary of metrics to update
            
        Returns:
            success: Whether the operation succeeded
        """
        # Find model in registry
        for model_type, models in self.model_metrics.items():
            if model_id in models:
                # Update metrics
                current_metrics = models[model_id].get('metrics', {})
                current_metrics.update(metrics)
                models[model_id]['metrics'] = current_metrics
                
                # Save registry
                self.save_registry()
                
                logger.info(f"Updated metrics for model {model_id}")
                return True
        
        logger.error(f"Model {model_id} not found in registry")
        return False
    
    def cleanup_cache(self):
        """Clear the model cache to free memory"""
        self.model_cache.clear()
        logger.info("Cleared model cache")

# Initialize model manager
model_manager = ModelManager()

def get_model_for_prediction(model_type='hybrid', fallback_to_basic=True):
    """
    Get a model for prediction, with fallback options
    
    Args:
        model_type: Preferred model type
        fallback_to_basic: Whether to fall back to basic model if hybrid not available
        
    Returns:
        model: Model instance for prediction
    """
    # Try to get requested model type
    model = model_manager.get_active_model(model_type)
    
    # If not found and fallback enabled, try basic model
    if model is None and fallback_to_basic and model_type == 'hybrid':
        logger.warning("Hybrid model not available, falling back to basic model")
        model = model_manager.get_active_model('basic')
    
    return model