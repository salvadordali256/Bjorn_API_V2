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
    
    # Check for specialized patterns
    lineset_abbrev, lineset_rules = handle_lineset_pattern(text, target_length)
    if lineset_abbrev:
        elapsed = time.time() - start_time
        logger.debug(f"Specialized abbreviation: {len(text)} → {len(lineset_abbrev)} chars in {elapsed:.3f}s")
        return lineset_abbrev, original_length, lineset_rules, len(lineset_abbrev), "specialized_pattern"
    
    # Try ML approach if enabled and available
    if use_ml and ml_initialized:
        try:
            # Use the appropriate model for prediction
            model = get_model_for_prediction('hybrid', fallback_to_basic=True)
            
            if model:
                abbreviated = model.predict_abbreviation(text, target_length)
                rules_applied = ["ML model applied"]
                method_used = "ml_hybrid" if model.__class__.__name__ == "HybridAbbreviationModel" else "ml_basic"
                
                # Handle ellipsis if present in the ML result
                if "..." in abbreviated:
                    # Remove ellipsis
                    abbreviated = abbreviated.replace("...", "")
                    
                    # Further abbreviate if still over target length
                    if len(abbreviated) > target_length:
                        abbreviated = smart_truncate(abbreviated, target_length)
                
                # Log ML performance
                elapsed = time.time() - start_time
                logger.debug(f"ML abbreviation: {len(text)} → {len(abbreviated)} chars in {elapsed:.3f}s")
                
                return abbreviated, original_length, rules_applied, len(abbreviated), method_used
                
        except Exception as e:
            logger.error(f"Error in ML abbreviation: {str(e)}")
            # Will fall back to rule-based approach
    
    # If ML not available or failed, use rule-based approach
    try:
        abbreviated, rules_applied = rule_based_abbreviation(text, target_length)
        
        # Log rule-based performance
        elapsed = time.time() - start_time
        logger.debug(f"Rule-based abbreviation: {len(text)} → {len(abbreviated)} chars in {elapsed:.3f}s")
        
        return abbreviated, original_length, rules_applied, len(abbreviated), "rule_based"
        
    except Exception as e:
        logger.error(f"Error in rule-based abbreviation: {str(e)}")
        return text, original_length, ["Error: " + str(e)], original_length, "error"

def handle_lineset_pattern(text: str, target_length: int = 30) -> Tuple[Optional[str], List[str]]:
    """
    Specialized handler for lineset patterns that keeps all critical dimensions
    
    Args:
        text: Text to check for lineset patterns
        target_length: Target maximum length
        
    Returns:
        tuple: (abbreviated_text, rules_applied) or (None, []) if not a lineset
    """
    # Check if it's a lineset description
    lineset_pattern = re.search(r'(?i)(?:copper\s+)?lines?et', text)
    if not lineset_pattern:
        return None, []
        
    # This is a lineset, so use a specialized format
    rules_applied = ["Specialized lineset formatting"]
    
    # Extract important measurements using regex
    measurements = list(re.finditer(r'(\d+(?:/\d+)?")(?:\s*x\s*|\s+)(\d+(?:/\d+)?")|\d+(?:/\d+)?"|\d+\'', text))
    
    # Extract suction and liquid line references
    suction_match = re.search(r'(?i)suction\s+lines?', text)
    liquid_match = re.search(r'(?i)liquid\s+lines?', text)
    discharge_match = re.search(r'(?i)discharge\s+lines?', text)
    
    # Standard abbreviations
    abbreviations = {
        "copper": "Cop",
        "lineset": "Lin",
        "line": "Ln",
        "suction": "Suc",
        "liquid": "Liq",
        "discharge": "Dis"
    }
    
    # Construct a specialized format for linesets
    result = "Cop Lin"
    
    # Add the main dimensions (usually at the start)
    if measurements and len(measurements) >= 1:
        # Get the first measurement (usually the paired dimensions)
        first_match = measurements[0]
        result += " " + text[first_match.start():first_match.end()]
    
    # Add suction line info if present
    if suction_match:
        suction_info = " Suc Ln"
        # Find measurement near suction
        for m in measurements:
            if abs(m.start() - suction_match.end()) < 15:  # If measurement is close to suction text
                suction_info += " " + text[m.start():m.end()]
                break
        result += suction_info
    
    # Add liquid line info if present
    if liquid_match:
        liquid_info = " Liq Ln"
        # Find measurement near liquid
        for m in measurements:
            if abs(m.start() - liquid_match.end()) < 15:  # If measurement is close to liquid text
                liquid_info += " " + text[m.start():m.end()]
                break
        result += liquid_info
    
    # Add discharge line info if present
    if discharge_match:
        discharge_info = " Dis Ln"
        # Find measurement near discharge
        for m in measurements:
            if abs(m.start() - discharge_match.end()) < 15:
                discharge_info += " " + text[m.start():m.end()]
                break
        result += discharge_info
    
    # Add length if present (usually a foot measurement at the end)
    length_match = re.search(r'(\d+)\s*\'', text)
    if length_match:
        result += " " + length_match.group(0)
    
    # Clean up spaces
    result = ' '.join(result.split())
    
    return result, rules_applied

def rule_based_abbreviation(text: str, target_length: int = 30) -> Tuple[str, List[str]]:
    """
    Improved rule-based abbreviation that preserves more information
    
    Args:
        text: The text to abbreviate
        target_length: Maximum length for the abbreviated text
        
    Returns:
        abbreviated_text, rules_applied
    """
    # Early return for already short text
    if len(text) <= target_length:
        return text, ["No abbreviation needed"]
    
    # Load abbreviation dictionary
    abbreviation_dict = load_abbreviation_dict()
    
    # Define HVAC-specific abbreviations
    hvac_abbreviations = {
        "copper": "Cop",
        "lineset": "Lin", 
        "suction": "Suc",
        "liquid": "Liq",
        "line": "Ln",
        "temperature": "Temp",
        "assembly": "Assy",
        "control": "Ctrl", 
        "system": "Sys",
        "valve": "Vlv",
        "conditioner": "Cond",
    }
    
    # Add HVAC abbreviations to the dictionary
    abbreviation_dict.update(hvac_abbreviations)
    
    abbreviated = text
    applied_rules = []
    
    # 1. First, try minimal abbreviation with standard replacements
    previous = abbreviated
    abbreviated = replace_words_with_abbreviations(abbreviated, abbreviation_dict)
    if abbreviated != previous:
        applied_rules.append("Applied dictionary abbreviations")
    
    # Clean up spaces
    abbreviated = ' '.join(abbreviated.split())
    
    # Check if we've reached the target length
    if len(abbreviated) <= target_length:
        return abbreviated, applied_rules
    
    # 2. Replace common phrases and word patterns
    common_phrases = {
        "with": "w/",
        "liquid line": "Liq Ln",
        "suction line": "Suc Ln",
        "factory assembled": "Fact Assy",
        "high efficiency": "Hi Eff",
    }
    
    previous = abbreviated
    for phrase, replacement in common_phrases.items():
        abbreviated = re.sub(r'\b' + re.escape(phrase) + r'\b', replacement, abbreviated, flags=re.IGNORECASE)
    
    if abbreviated != previous:
        applied_rules.append("Replaced common phrases")
    
    # Clean up spaces
    abbreviated = ' '.join(abbreviated.split())
    
    # Check if we've reached the target length
    if len(abbreviated) <= target_length:
        return abbreviated, applied_rules
    
    # 3. Remove less important information in parentheses if present
    if "(" in abbreviated and ")" in abbreviated:
        previous = abbreviated
        abbreviated = re.sub(r'\([^)]*\)', '', abbreviated)
        if abbreviated != previous:
            applied_rules.append("Removed text in parentheses")
            abbreviated = ' '.join(abbreviated.split())
    
    # 4. Intelligently abbreviate long words (preserve units and measurements)
    # This is critical for your example with measurements
    if len(abbreviated) > target_length:
        words = abbreviated.split()
        
        # Don't abbreviate measurements and numbers
        for i, word in enumerate(words):
            # Skip measurements, numbers, and short words
            if re.search(r'[\d./"]', word) or len(word) < 5:
                continue
                
            # For longer words, abbreviate more aggressively
            if len(word) > 7:
                # Keep first 3 characters
                words[i] = word[:3]
            elif len(word) > 5:
                # Keep first 4 characters
                words[i] = word[:4]
        
        previous = abbreviated
        abbreviated = ' '.join(words)
        
        if abbreviated != previous:
            applied_rules.append("Abbreviated long words")
    
    # 5. Prioritize different parts of the text
    if len(abbreviated) > target_length:
        # Split into parts based on common separators
        parts = re.split(r'[-,;]', abbreviated)
        
        if len(parts) > 1:
            # Keep first part fully, abbreviate others more aggressively
            first_part = parts[0].strip()
            other_parts = []
            
            # Current length with first part
            current_length = len(first_part)
            
            # Process other parts to fit in remaining space
            for part in parts[1:]:
                part = part.strip()
                
                # Calculate space including separator
                remaining_space = target_length - current_length - 1  # -1 for separator
                
                if remaining_space <= 3:
                    # No space left, stop adding parts
                    break
                
                if len(part) <= remaining_space:
                    # Part fits, add it as is
                    other_parts.append(part)
                    current_length += len(part) + 1  # +1 for separator
                else:
                    # Abbreviate this part to fit
                    words = part.split()
                    abbreviated_part = []
                    part_length = 0
                    
                    for word in words:
                        # Skip numbers and measurements
                        if re.search(r'[\d./"]', word):
                            word_to_add = word
                        elif len(word) > 4:
                            # Abbreviate longer words
                            word_to_add = word[:3]
                        else:
                            word_to_add = word
                        
                        # Check if word fits
                        if part_length + len(word_to_add) + (1 if abbreviated_part else 0) <= remaining_space:
                            if abbreviated_part:
                                abbreviated_part.append(" ")
                                part_length += 1
                            abbreviated_part.append(word_to_add)
                            part_length += len(word_to_add)
                        else:
                            break
                    
                    other_parts.append(''.join(abbreviated_part))
                    current_length += part_length + 1  # +1 for separator
            
            # Combine parts with original separators
            abbreviated = first_part
            separator_idx = 0
            
            for i, part in enumerate(other_parts):
                # Find the original separator
                while separator_idx < len(abbreviated) and not abbreviated[separator_idx] in '-,;':
                    separator_idx += 1
                
                if separator_idx < len(abbreviated):
                    separator = abbreviated[separator_idx]
                else:
                    separator = '-'  # Default separator
                
                abbreviated = abbreviated + separator + part
            
            applied_rules.append("Prioritized different parts of text")
    
    # Final truncation if still too long, but prefer completing with a measurement
    if len(abbreviated) > target_length:
        # Try to preserve measurements and their context
        match = re.search(r'(\d+[\'"])', abbreviated[target_length:])
        if match:
            # Find position of the measurement
            full_text = abbreviated
            measurement_pos = full_text.find(match.group(0), target_length)
            if measurement_pos > 0 and measurement_pos - target_length < 10:  # Only extend if close enough
                # Find a good breaking point after the measurement
                end_pos = full_text.find(' ', measurement_pos + len(match.group(0)))
                if end_pos > 0:
                    abbreviated = full_text[:end_pos]
                else:
                    abbreviated = full_text[:measurement_pos + len(match.group(0))]
                applied_rules.append("Extended to include measurement")
        
        # If still too long, do smart truncation preserving full words
        if len(abbreviated) > target_length:
            abbreviated = smart_truncate(abbreviated, target_length)
            applied_rules.append("Smart truncation applied")
    
    # Clean up whitespace and ensure no double spaces
    abbreviated = ' '.join(abbreviated.split())
    
    return abbreviated, applied_rules

def smart_truncate(text: str, length: int = 30) -> str:
    """
    Improved smart truncation to preserve meaningful information
    
    Args:
        text: The text to truncate
        length: Maximum length
        
    Returns:
        truncated_text
    """
    if len(text) <= length:
        return text
    
    # Prioritize preserving measurements and numbers
    # Try to find the last complete measurement before the length limit
    measurements = list(re.finditer(r'\d+(?:[./]\d+)?(?:\s*["\'\×xX]?\s*\d+(?:[./]\d+)?)?(?:\s*["\'])?', text[:length+15]))
    
    if measurements and measurements[-1].end() <= length + 10:
        # Found a measurement, truncate after it
        end_pos = measurements[-1].end()
        # Find next space after the measurement, if within reasonable distance
        next_space = text.find(' ', end_pos)
        if 0 < next_space < end_pos + 5:  # Only extend a bit to complete a word
            end_pos = next_space
        return text[:end_pos].strip()
    
    # If no measurements or they're too far, just find the last space
    truncated = text[:length]
    last_space = truncated.rfind(' ')
    
    if last_space > length * 0.5:  # Only truncate at word if we're not losing too much
        return truncated[:last_space].strip()
    else:
        return truncated.strip()

def replace_words_with_abbreviations(text: str, abbreviation_dict: Dict[str, str]) -> str:
    """
    Replace words in text with their abbreviations from the dictionary
    
    Args:
        text: Text to process
        abbreviation_dict: Dictionary of word -> abbreviation mappings
        
    Returns:
        text with words replaced by abbreviations
    """
    result = text
    
    # Sort words by length (longest first) to prioritize longer matches
    sorted_words = sorted(abbreviation_dict.keys(), key=len, reverse=True)
    
    for word in sorted_words:
        # Ensure we only match whole words
        pattern = r'\b' + re.escape(word) + r'\b'
        result = re.sub(pattern, abbreviation_dict[word], result, flags=re.IGNORECASE)
    
    return result

def remove_vowels_from_long_words(text: str, min_length: int = 5) -> str:
    """
    Remove vowels from words longer than min_length, keeping first vowel
    
    Args:
        text: Text to process
        min_length: Minimum word length to apply this rule
        
    Returns:
        text with vowels removed from long words
    """
    words = text.split()
    vowels = "aeiouAEIOU"
    
    for i, word in enumerate(words):
        if len(word) > min_length:
            # Keep first character even if it's a vowel
            first_char = word[0]
            rest = word[1:]
            
            # Remove vowels from the rest of the word
            vowels_removed = ''.join([c for c in rest if c.lower() not in vowels])
            
            # Combine and update
            words[i] = first_char + vowels_removed
    
    return ' '.join(words)

def abbreviate_common_phrases(text: str) -> str:
    """
    Abbreviate common HVAC-specific phrases
    
    Args:
        text: Text to process
        
    Returns:
        text with common phrases abbreviated
    """
    # Define common phrases and their abbreviations
    common_phrases = {
        "temperature control": "temp ctrl",
        "building management system": "BMS",
        "heating ventilation and air conditioning": "HVAC",
        "air handling unit": "AHU",
        "factory assembled": "FACT ASSY",
        "cabinet assemblies": "CAB ASSY",
        "cabinet assembly": "CAB ASSY",
        "chrome plated": "CP",
        "stainless steel": "SS",
        "air conditioner": "AC",
        "high efficiency": "HE",
        "variable frequency drive": "VFD",
        "electronic control": "ELEC CTRL",
        "pressure regulator": "PRESS REG",
        "temperature sensor": "TEMP SENS",
        "recirculation pump": "RECIRC PUMP",
        "thermostatic mixing valve": "THERM MIX VLV"
    }
    
    result = text
    
    # Sort phrases by length (longest first) to prioritize longer matches
    sorted_phrases = sorted(common_phrases.keys(), key=len, reverse=True)
    
    for phrase in sorted_phrases:
        # Create a case-insensitive pattern
        pattern = re.escape(phrase)
        result = re.sub(pattern, common_phrases[phrase], result, flags=re.IGNORECASE)
    
    return result

def replace_prepositions_and_conjunctions(text: str) -> str:
    """
    Replace common prepositions and conjunctions with shorter versions
    
    Args:
        text: Text to process
        
    Returns:
        text with shortened prepositions and conjunctions
    """
    replacements = {
        r'\band\b': '&',
        r'\bwith\b': 'w/',
        r'\bfor\b': '4',
        r'\bto\b': '2',
        r'\bat\b': '@',
        r'\bwithout\b': 'w/o',
        r'\bthrough\b': 'thru',
        r'\bbetween\b': 'btwn',
        r'\bincluding\b': 'incl',
        r'\babout\b': 'abt'
    }
    
    result = text
    
    for pattern, replacement in replacements.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result

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
            abbreviated, rules = rule_based_abbreviation(description, 30 - len(code) - 1)
            return f"{code} {abbreviated}", rules
            
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