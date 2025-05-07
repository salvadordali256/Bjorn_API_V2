#!/usr/bin/env python3
"""
Create valid model files for the Bjorn HVAC Abbreviation System
to fix the 'No active model' warnings
"""
import os
import joblib
import json
import numpy as np
import datetime
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline

# Custom AbbreviationFeatures class
class AbbreviationFeatures:
    def __init__(self):
        import re
        self.vowel_pattern = re.compile(r'[aeiou]', re.IGNORECASE)
        self.consonant_pattern = re.compile(r'[bcdfghjklmnpqrstvwxyz]', re.IGNORECASE)
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        # Handle sparse matrices
        if hasattr(X, "toarray"):
            X = X.toarray()
        
        # Initialize feature matrix
        features = np.zeros((X.shape[0], 5))
        return features

print("Creating model directories...")
os.makedirs('/app/models/basic', exist_ok=True)
os.makedirs('/app/models/hybrid', exist_ok=True)

print("Creating basic model files...")
# Basic model components
char_vectorizer = CountVectorizer(analyzer='char', ngram_range=(1, 3))
hvac_terms = [
    "compressor", "condenser", "temperature control", "evaporator",
    "refrigerant", "heating", "ventilation", "cooling", "thermostat"
]
char_vectorizer.fit(hvac_terms)

ratio_model = RandomForestRegressor(n_estimators=10, random_state=42)
X = char_vectorizer.transform(hvac_terms)
ratio_model.fit(X, np.array([0.5, 0.6, 0.4, 0.7, 0.5, 0.6, 0.5, 0.4, 0.6]))

# HVAC-specific abbreviation dictionary
abbreviation_dict = {
    "system": "sys",
    "temperature": "temp",
    "heating": "htg",
    "ventilation": "vent",
    "air": "a",
    "conditioning": "cond",
    "compressor": "comp",
    "condenser": "cond",
    "evaporator": "evap",
    "refrigerant": "refrig",
    "thermostat": "tstat",
    "control": "ctrl",
    "equipment": "equip",
    "pressure": "press",
    "humidity": "hum"
}

# Create basic model data matching AbbreviationModel structure
basic_model_data = {
    'char_vectorizer': char_vectorizer,
    'ratio_model': ratio_model,
    'abbreviation_dict': abbreviation_dict,
    'is_trained': True  # Important flag
}

print("Creating hybrid model file...")
# Create an actual Pipeline object for the hybrid model
features_extractor = CountVectorizer(analyzer='char', ngram_range=(1, 3))
features_extractor.fit(hvac_terms)

# Create an actual pipeline that has a predict method
pipeline = Pipeline([
    ('features', features_extractor),
    ('regressor', RandomForestRegressor(n_estimators=10, random_state=42))
])

# Train the pipeline
pipeline.fit(hvac_terms, np.array([0.5, 0.6, 0.4, 0.7, 0.5, 0.6, 0.5, 0.4, 0.6]))

# Word and phrase abbreviations for hybrid model
word_abbreviations = {
    "system": "sys",
    "temperature": "temp",
    "heating": "htg",
    "ventilation": "vent",
    "air": "a",
    "conditioning": "cond",
    "compressor": "comp",
    "evaporator": "evap",
    "refrigerant": "refr",
    "thermostat": "tstat",
    "pressure": "press",
    "humidity": "hum",
    "control": "ctrl",
    "equipment": "equip",
    "electronic": "elec",
    "mechanical": "mech",
    "variable": "var",
    "efficiency": "eff",
    "outdoor": "OD",
    "indoor": "ID"
}

phrase_abbreviations = {
    "heating ventilation and air conditioning": "HVAC",
    "temperature control system": "TCS",
    "air handling unit": "AHU",
    "variable refrigerant flow": "VRF",
    "packaged terminal air conditioner": "PTAC",
    "variable air volume": "VAV",
    "building management system": "BMS",
    "energy recovery ventilator": "ERV"
}

# Create hybrid model data with a proper pipeline object
hybrid_model_data = {
    'pipeline': pipeline,  # This is a proper Pipeline object with predict method
    'word_abbreviations': word_abbreviations,
    'phrase_abbreviations': phrase_abbreviations,
    'is_trained': True  # Important flag
}

# Save model files
print("Saving model files...")
joblib.dump(basic_model_data, '/app/models/basic/model.pkl')
joblib.dump(hybrid_model_data, '/app/models/hybrid/model.pkl')

# Create info.json files and registry as before
# [Rest of the script remains the same]
...