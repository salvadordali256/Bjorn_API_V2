"""
Verification of abbreviation quality and correctness
"""
import logging
from typing import Dict, List, Optional

from app.utils.config import config

logger = logging.getLogger(__name__)

def verify_abbreviation(original: str, abbreviated: str, abbreviations_applied: List[str]) -> Dict[str, any]:
    """
    Enhanced verification with better metrics and readability assessment
    
    Args:
        original: Original text
        abbreviated: Abbreviated text
        abbreviations_applied: List of applied abbreviation rules
        
    Returns:
        dict: Dictionary with verification metrics
    """
    target_length = config.get('abbreviation.target_length', 30)
    
    # Calculate metrics
    length_reduction = ((len(original) - len(abbreviated)) / len(original)) if len(original) > 0 else 0
    
    # Check if the abbreviation preserves meaning
    meaning_preserved = True
    severe_truncation = False
    
    for abbr in abbreviations_applied:
        if "Truncated entire phrase" in abbr:
            severe_truncation = True
            meaning_preserved = False
            break
    
    # Check readability
    readability_score = 1.0
    if severe_truncation:
        readability_score = 0.3
    elif "truncated" in str(abbreviations_applied).lower():
        readability_score = 0.6
    elif len(abbreviated) > target_length:
        readability_score = 0.7
    
    # Calculate confidence score
    if len(abbreviated) <= target_length and not severe_truncation:
        base_confidence = 0.7
    else:
        base_confidence = 0.4
        
    meaning_factor = 0.2 if meaning_preserved else 0
    standard_abbr_factor = 0.1 if not "truncated" in str(abbreviations_applied).lower() else 0
    
    confidence = min(base_confidence + meaning_factor + standard_abbr_factor, 1.0)
    
    # Generate suggestions
    suggestions = []
    if severe_truncation:
        suggestions.append("Phrase was severely truncated, meaning may be lost")
    if "truncated" in str(abbreviations_applied).lower():
        suggestions.append("Contains non-standard abbreviations")
    if readability_score < 0.7:
        suggestions.append("Some abbreviations may not be easily recognized")
    
    return {
        "confidence": round(confidence, 2),
        "readability": round(readability_score, 2),
        "meaning_preserved": meaning_preserved,
        "is_standard": not "truncated" in str(abbreviations_applied).lower(),
        "suggestions": suggestions
    }