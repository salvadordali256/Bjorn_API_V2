"""
Basic ML model for HVAC part abbreviation
"""
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib
import re
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

class AbbreviationModel:
    """Machine learning model for abbreviating text"""
    
    def __init__(self):
        # Feature extraction
        self.char_vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, 3))
        
        # ML model for predicting abbreviation ratio
        self.ratio_model = RandomForestRegressor(n_estimators=100, random_state=42)
        
        # Dictionary for common abbreviation patterns
        self.abbreviation_dict = {}
        
        # Status flag
        self.is_trained = False
    
    def extract_features(self, texts):
        """Extract character n-gram features from texts"""
        return self.char_vectorizer.transform(texts)
    
    def fit(self, training_data):
        """Train the model on pairs of (original, abbreviated) texts"""
        # Extract original and abbreviated texts
        original_texts = [item[0] for item in training_data]
        abbreviated_texts = [item[1] for item in training_data]
        
        # Create abbreviation dictionary from training data
        self._build_abbreviation_dict(training_data)
        
        # Extract character n-gram features
        self.char_vectorizer.fit(original_texts)
        X = self.char_vectorizer.transform(original_texts)
        
        # Calculate abbreviation ratios as target variable
        y = np.array([len(abbr)/len(orig) for orig, abbr in training_data])
        
        # Train a regression model to predict abbreviation ratio
        self.ratio_model.fit(X, y)
        
        # Set trained flag
        self.is_trained = True
        
        # Validate on training data
        predictions = self.ratio_model.predict(X)
        mse = mean_squared_error(y, predictions)
        
        logger.info(f"Model trained on {len(training_data)} examples")
        logger.info(f"Mean Squared Error on training data: {mse:.4f}")
        logger.info(f"Learned {len(self.abbreviation_dict)} common word abbreviations")
        
        return mse
    
    def _build_abbreviation_dict(self, training_data):
        """Extract word-level abbreviation patterns from training data"""
        word_patterns = {}
        
        for original, abbreviated in training_data:
            # Split into words
            orig_words = original.split()
            abbr_words = abbreviated.split()
            
            # Process word by word if same number of words
            if len(orig_words) == len(abbr_words):
                for orig, abbr in zip(orig_words, abbr_words):
                    if orig != abbr and len(orig) > len(abbr):
                        if orig not in word_patterns:
                            word_patterns[orig] = {}
                        
                        if abbr in word_patterns[orig]:
                            word_patterns[orig][abbr] += 1
                        else:
                            word_patterns[orig][abbr] = 1
        
        # Find most common abbreviation for each word
        for word, abbrevs in word_patterns.items():
            if abbrevs:
                self.abbreviation_dict[word] = max(abbrevs.items(), key=lambda x: x[1])[0]
    
    def predict_abbreviation(self, text, target_length=30):
        """Predict abbreviation for a given text"""
        if not self.is_trained:
            return text
            
        # If already short enough, return as is
        if len(text) <= target_length:
            return text
            
        # First, try applying known abbreviation patterns
        words = text.split()
        abbreviated_words = []
        
        for word in words:
            # If we have a known abbreviation for this word, use it
            if word in self.abbreviation_dict:
                abbreviated_words.append(self.abbreviation_dict[word])
            else:
                abbreviated_words.append(word)
        
        result = ' '.join(abbreviated_words)
        
        # If still too long, apply ML prediction for individual words
        if len(result) > target_length:
            # Start with the longest words
            word_indices = sorted(range(len(words)), key=lambda i: len(abbreviated_words[i]), reverse=True)
            
            for idx in word_indices:
                if len(result) <= target_length:
                    break
                    
                word = abbreviated_words[idx]
                # Skip short words and already abbreviated words
                if len(word) <= 3 or word in self.abbreviation_dict.values():
                    continue
                
                # Extract features for this word
                X_word = self.char_vectorizer.transform([word])
                
                # Predict abbreviation ratio
                ratio = self.ratio_model.predict(X_word)[0]
                
                # Apply the predicted ratio
                target_word_len = max(3, int(len(word) * ratio))
                if target_word_len < len(word):
                    # Simple strategy: keep the first n characters
                    abbreviated_words[idx] = word[:target_word_len]
                    # Recalculate the result
                    result = ' '.join(abbreviated_words)
        
        # If still too long, use truncation as a last resort
        if len(result) > target_length:
            # Try to truncate at a word boundary
            last_space = result[:target_length-3].rfind(' ')
            if last_space > 0:
                result = result[:last_space] + "..."
            else:
                result = result[:target_length-3] + "..."
        
        return result
    
    def save(self, model_path):
        """Save the trained model to disk"""
        if not self.is_trained:
            logger.warning("Model not trained yet, nothing to save")
            return False
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Save the model components
        joblib.dump({
            'char_vectorizer': self.char_vectorizer,
            'ratio_model': self.ratio_model,
            'abbreviation_dict': self.abbreviation_dict
        }, model_path)
        
        logger.info(f"Model saved to {model_path}")
        return True
    
    def load(self, model_path):
        """Load a trained model from disk"""
        try:
            model_data = joblib.load(model_path)
            
            self.char_vectorizer = model_data['char_vectorizer']
            self.ratio_model = model_data['ratio_model']
            self.abbreviation_dict = model_data['abbreviation_dict']
            self.is_trained = True
            
            logger.info(f"Model loaded from {model_path}")
            logger.info(f"Loaded {len(self.abbreviation_dict)} abbreviation patterns")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False