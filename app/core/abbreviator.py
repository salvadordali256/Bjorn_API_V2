"""
Core abbreviation logic for the HVAC abbreviation system
"""
import re
import logging
import time
from typing import Tuple, List, Dict, Optional

from app.utils.config import config
from app.ml.model_manager import model_manager, get_model_for_prediction

# Set up logging
logger = logging.getLogger(__name__)

# Global flags for ML availability
ml_initialized = False
ml_available_models = []

# Load abbreviation dictionary
from app.core.abbreviation_dict import load_abbreviation_dict
abbreviation_dict = load_abbreviation_dict()

def init_ml() -> bool:
    """
    Initialize ML components and check available models
    
    Returns:
        bool: Whether ML is available for use
    """
    global ml_initialized, ml_available_models
    
    logger.info("Initializing ML components")
    
    try:
        # Check for hybrid model
        hybrid_model = model_manager.get_active_model('hybrid')
        if hybrid_model:
            ml_available_models.append('hybrid')
            logger.info("Hybrid ML model available")
        
        # Check for basic model
        basic_model = model_manager.get_active_model('basic')
        if basic_model:
            ml_available_models.append('basic')
            logger.info("Basic ML model available")
        
        # Clean up model cache to free memory
        model_manager.cleanup_cache()
        
        # Set initialization flag
        ml_initialized = len(ml_available_models) > 0
        
        if ml_initialized:
            logger.info(f"ML initialization successful. Available models: {', '.join(ml_available_models)}")
        else:
            logger.warning("No ML models available. Using rule-based abbreviation only.")
        
        return ml_initialized
        
    except Exception as e:
        logger.error(f"Error initializing ML: {str(e)}")
        ml_initialized = False
        return False

def abbreviate_text(text: str, target_length: int = 30, use_ml: bool = True) -> Tuple[str, int, List[str], int, str]:
    """
    Abbreviate text using the appropriate method (ML or rule-based)
    
    Args:
        text: Text to abbreviate
        target_length: Target maximum length
        use_ml: Whether to use ML models if available
        
    Returns:
        tuple: (abbreviated_text, original_length, rules_applied, final_length, method_used)
    """
    # Early return for empty text
    if not text or not isinstance(text, str):
        return text, 0, [], 0, "none"
    
    # Early return for already short text
    if len(text) <= target_length:
        return text, len(text), [], len(text), "no_change"
    
    start_time = time.time()
    original_length = len(text)
    method_used = "rule_based"  # Default method
    
    # Try ML approach if enabled and available
    if use_ml and ml_initialized:
        try:
            # Use the appropriate model for prediction
            model = get_model_for_prediction('hybrid', fallback_to_basic=True)
            
            if model:
                abbreviated = model.predict_abbreviation(text, target_length)
                rules_applied = ["ML model applied"]
                method_used = "ml_hybrid" if model.__class__.__name__ == "HybridAbbreviationModel" else "ml_basic"
                
                # Log ML performance
                elapsed = time.time() - start_time
                logger.debug(f"ML abbreviation: {len(text)} → {len(abbreviated)} chars in {elapsed:.3f}s")
                
                return abbreviated, original_length, rules_applied, len(abbreviated), method_used
                
        except Exception as e:
            logger.error(f"Error in ML abbreviation: {str(e)}")
            # Will fall back to rule-based approach
    
    # If ML not available or failed, use rule-based approach
    try:
        abbreviated, original_length, rules_applied, final_length = apply_abbreviation_rules(
            text, target_length)
        
        # Log rule-based performance
        elapsed = time.time() - start_time
        logger.debug(f"Rule-based abbreviation: {len(text)} → {len(abbreviated)} chars in {elapsed:.3f}s")
        
        return abbreviated, original_length, rules_applied, final_length, "rule_based"
        
    except Exception as e:
        logger.error(f"Error in rule-based abbreviation: {str(e)}")
        return text, original_length, ["Error: " + str(e)], original_length, "error"

def apply_abbreviation_rules(phrase: str, target_length: int = 30) -> Tuple[str, int, List[str], int]:
    """
    Apply rule-based abbreviation to a phrase to fit target length
    
    Args:
        phrase: Text to abbreviate
        target_length: Target maximum length
        
    Returns:
        tuple: (abbreviated_text, original_length, rules_applied, final_length)
    """
    # Early return for empty or short phrases
    if not phrase or not isinstance(phrase, str) or len(phrase) <= target_length:
        return phrase, len(phrase) if phrase else 0, [], len(phrase) if phrase else 0
    
    original_length = len(phrase)
    abbreviations_applied = []
    processed_phrase = phrase
    
    # Industry-specific patterns and their abbreviations
    pattern_replacements = {
        r"CABINET ASSEMBLIES-SHOWERS, FACTORY ASSEMBLED": "CAB SHWR ASSY",
        r"CABINET ASSEMBLIES-HYDROTHERAPY, FACT\. ASSLD": "CAB HYDRO ASSY",
        r"Single Thermostatic Water Mixing Valves[,]?": "SNGL THERM MIX VLV",
        r"EXPOSED RECIRCULATION PIPING ASSEMBLY": "EXP RECIRC PIPE ASSY",
        r"EXPOSED VALVE ASSEMBLIES-Group shower": "EXP VLV GSHWR ASSY",
        r"GROUP SHOWER XL": "GRP SHWR XL",
        r"HIGH CAPACITY XL": "HI CAP XL",
        r"LV SERIES SINGLE VALVE": "LV SER SGL VLV",
        r"\(RF-rough bronze\)": "(RF-BRZ)",
        r"\(CP-chrome plate\)": "(CP-PLT)"
    }
    
    # First pass: Apply pattern-based replacements
    for pattern, replacement in pattern_replacements.items():
        if re.search(pattern, processed_phrase, re.IGNORECASE):
            old_phrase = processed_phrase
            processed_phrase = re.sub(pattern, replacement, processed_phrase, flags=re.IGNORECASE)
            if processed_phrase != old_phrase:
                abbreviations_applied.append(f"{pattern}→{replacement}")
    
    # Second pass: Dictionary-based abbreviation with optimization for maximum character savings
    if len(processed_phrase) > target_length:
        # Extract words that could be abbreviated
        words = []
        word_positions = []
        for match in re.finditer(r'\b\w+\b', processed_phrase):
            words.append(match.group())
            word_positions.append((match.start(), match.end()))
        
        # Calculate potential savings for each word
        potential_abbreviations = []
        for i, word in enumerate(words):
            # Skip words that are too short
            if len(word) <= 3:
                continue
                
            # Try different forms for lookup
            for lookup in [word, word.capitalize(), word.upper(), word.lower()]:
                clean_lookup = re.sub(r'[^\w/]', '', lookup)
                if clean_lookup in abbreviation_dict:
                    abbrev = abbreviation_dict[clean_lookup]
                    
                    # Preserve original case
                    if word.isupper():
                        abbrev = abbrev.upper()
                    elif word[0].isupper():
                        abbrev = abbrev[0].upper() + abbrev[1:].lower() if len(abbrev) > 1 else abbrev.upper()
                    
                    chars_saved = len(word) - len(abbrev)
                    if chars_saved > 0:
                        potential_abbreviations.append((i, word, abbrev, chars_saved))
                    break
        
        # Sort by character savings (highest first)
        potential_abbreviations.sort(key=lambda x: x[3], reverse=True)
        
        # Apply abbreviations until we reach target length or run out of abbreviations
        for i, word, abbrev, _ in potential_abbreviations:
            if len(processed_phrase) <= target_length:
                break
                
            # Calculate the positions for this specific occurrence
            start, end = word_positions[i]
            
            # Create new phrase by replacing just this instance
            processed_phrase = processed_phrase[:start] + abbrev + processed_phrase[end:]
            
            # Update remaining word positions
            length_diff = len(abbrev) - (end - start)
            for j in range(i + 1, len(word_positions)):
                word_positions[j] = (word_positions[j][0] + length_diff, word_positions[j][1] + length_diff)
            
            abbreviations_applied.append(f"{word}→{abbrev}")
    
    # Third pass: Intelligent word reduction
    if len(processed_phrase) > target_length:
        # Remove unnecessary words and punctuation
        remove_patterns = [
            (r', ', ' '),  # Replace commas with spaces
            (r'\s+', ' '),  # Consolidate multiple spaces
            (r'\s*\([^)]*\)\s*', ' ')  # Remove parenthetical phrases
        ]
        
        for pattern, replacement in remove_patterns:
            old_phrase = processed_phrase
            processed_phrase = re.sub(pattern, replacement, processed_phrase)
            processed_phrase = processed_phrase.strip()
            if old_phrase != processed_phrase:
                abbreviations_applied.append(f"Removed '{pattern}' pattern")
    
    # Fourth pass: Word truncation for longer words
    if len(processed_phrase) > target_length:
        words = processed_phrase.split()
        
        # Sort words by length (longest first)
        word_indices = sorted(range(len(words)), key=lambda i: len(words[i]), reverse=True)
        
        for idx in word_indices:
            if len(processed_phrase) <= target_length:
                break
                
            word = words[idx]
            if len(word) <= 3:
                continue
            
            # Intelligent truncation strategy
            if len(word) >= 8:
                # For very long words, keep first 3 chars + last char
                shortened = word[:3] + word[-1]
            elif len(word) >= 6:
                # For medium words, keep first 3 chars
                shortened = word[:3]
            elif len(word) > 4:
                # For shorter words, just remove a character or two
                shortened = word[:len(word)-1]
            else:
                continue  # Don't shorten 4-letter words
            
            # Apply the truncation
            words[idx] = shortened
            new_phrase = ' '.join(words)
            
            # Only apply if it actually helps
            if len(new_phrase) < len(processed_phrase):
                abbreviations_applied.append(f"{word}→{shortened}")
                processed_phrase = new_phrase
    
    # Final pass: If still over target length, truncate intelligently with ellipsis
    if len(processed_phrase) > target_length:
        # Try to truncate at a word boundary
        last_space = processed_phrase[:target_length-3].rfind(' ')
        if last_space > target_length * 0.7:  # Only truncate at word if we're not losing too much
            truncated = processed_phrase[:last_space] + "..."
        else:
            truncated = processed_phrase[:target_length-3] + "..."
        
        abbreviations_applied.append("Truncated entire phrase")
        processed_phrase = truncated
    
    return processed_phrase, original_length, abbreviations_applied, len(processed_phrase)

def detect_product_patterns(text: str) -> Tuple[Optional[str], List[str]]:
    """
    Identify specific product code patterns and handle them intelligently
    
    Args:
        text: Text to check for product patterns
        
    Returns:
        tuple: (modified_text, patterns_found) or (None, []) if no patterns found
    """
    # Pattern for XL and LV series product codes
    xl_pattern = re.compile(r'(XL|LV)-(\d+)-([\w-]+)')
    
    if xl_pattern.search(text):
        # Product code found, don't abbreviate the code itself
        # but focus on abbreviating the description
        parts = text.split('\t', 1) if '\t' in text else text.split(None, 1)
        if len(parts) > 1:
            code, description = parts
            # Abbreviate only the description
            abbr_desc, _, abbrevs, _ = apply_abbreviation_rules(description, 30 - len(code) - 1)
            return f"{code} {abbr_desc}", abbrevs
            
    return None, []

def log_abbreviation_result(original: str, abbreviated: str, method: str, success: bool):
    """
    Log abbreviation result for analysis and improvement
    
    Args:
        original: Original text
        abbreviated: Abbreviated text
        method: Method used for abbreviation
        success: Whether abbreviation was successful
    """
    try:
        import os
        log_dir = "logs/abbreviations"
        os.makedirs(log_dir, exist_ok=True)
        
        # Get today's log file
        from datetime import datetime
        log_file = os.path.join(log_dir, f"abbreviations_{datetime.now().strftime('%Y-%m-%d')}.log")
        
        # Log abbreviation result
        with open(log_file, "a") as f:
            f.write(f"{datetime.now().isoformat()},{method},{success},{len(original)},{len(abbreviated)},{original},{abbreviated}\n")
            
    except Exception as e:
        logger.error(f"Error logging abbreviation result: {str(e)}")

def get_ml_status() -> Dict[str, any]:
    """
    Get the current status of ML components
    
    Returns:
        dict: Status information about ML components
    """
    return {
        "initialized": ml_initialized,
        "available_models": ml_available_models,
        "model_registry": model_manager.active_models
    }