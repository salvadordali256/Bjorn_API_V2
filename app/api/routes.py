"""
API routes for the Bjorn HVAC Abbreviation System
"""
from flask import Blueprint, request, jsonify
import os
import csv
import io
import pandas as pd
import logging
import time
import json

from app.utils.error_handling import api_error_handler, validate_file_upload, validate_form_data, log_api_call
from app.utils.config import config
from app.ml.model_manager import model_manager
from app.core.abbreviator import abbreviate_text, get_ml_status, log_abbreviation_result
from app.core.verification import verify_abbreviation
from app.core.abbreviation_dict import load_abbreviation_dict, save_abbreviation_dict

# Create logger
logger = logging.getLogger(__name__)

# Create Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Get abbreviation dictionary
abbreviation_dict = load_abbreviation_dict()

@api_bp.route('/abbreviate', methods=['POST'])
@api_error_handler
@log_api_call('abbreviate')
def api_abbreviate():
    """API endpoint for abbreviating text or file content"""
    # Validate inputs
    if 'file' in request.files:
        # File-based abbreviation
        file = validate_file_upload(
            request, 
            'file', 
            config.get('files.allowed_extensions', ['csv', 'xlsx', 'xls', 'txt'])
        )
        
        # Get additional parameters
        use_ml = request.form.get('use_ml', 'true').lower() == 'true'
        target_length = int(request.form.get('target_length', config.get('abbreviation.target_length', 30)))
        
        # Process the file
        return process_csv_file(file, use_ml, target_length)
    elif 'text' in request.form:
        # Text-based abbreviation
        form_data = validate_form_data(request, ['text'])
        
        # Get parameters
        text = form_data.get('text')
        use_ml = form_data.get('use_ml', 'true').lower() == 'true'
        target_length = int(form_data.get('target_length', config.get('abbreviation.target_length', 30)))
        
        # Abbreviate the text
        abbreviated, original_length, rules_applied, final_length, method_used = abbreviate_text(
            text, target_length, use_ml)
        
        # Log the abbreviation result
        log_abbreviation_result(text, abbreviated, method_used, final_length <= target_length)
        
        # Prepare response
        response = {
            "success": True,
            "original": text,
            "abbreviated": abbreviated,
            "original_length": original_length,
            "abbreviated_length": final_length,
            "reduction_percentage": ((original_length - final_length) / original_length * 100) if original_length > 0 else 0,
            "rules_applied": rules_applied,
            "method_used": method_used,
            "target_met": final_length <= target_length
        }
        
        return jsonify(response)
    else:
        # Batch text abbreviation
        form_data = validate_form_data(request, ['texts'])
        texts = json.loads(form_data.get('texts', '[]'))
        
        if not texts:
            return jsonify({
                "success": False,
                "error": "No texts provided for abbreviation"
            }), 400
        
        # Get parameters
        use_ml = form_data.get('use_ml', 'true').lower() == 'true'
        target_length = int(form_data.get('target_length', config.get('abbreviation.target_length', 30)))
        
        # Process each text
        results = []
        for text in texts:
            abbreviated, original_length, rules_applied, final_length, method_used = abbreviate_text(
                text, target_length, use_ml)
            
            # Log the abbreviation result
            log_abbreviation_result(text, abbreviated, method_used, final_length <= target_length)
            
            results.append({
                "original": text,
                "abbreviated": abbreviated,
                "original_length": original_length,
                "abbreviated_length": final_length,
                "reduction_percentage": ((original_length - final_length) / original_length * 100) if original_length > 0 else 0,
                "rules_applied": rules_applied,
                "method_used": method_used,
                "target_met": final_length <= target_length
            })
        
        return jsonify({
            "success": True,
            "results": results
        })

def process_csv_file(file, use_ml=True, target_length=30):
    """Process CSV file with part descriptions"""
    try:
        # Read file contents
        file_content = file.read().decode('utf-8', errors='replace')
        
        # Parse CSV data
        csv_data = list(csv.reader(io.StringIO(file_content)))
        
        # Get headers
        headers = csv_data[0]
        
        # Check if Part Definition column exists
        if "Part Definition" not in headers:
            # Try to find it case-insensitively
            for i, header in enumerate(headers):
                if header.lower() == "part definition":
                    headers[i] = "Part Definition"
                    break
            else:
                return jsonify({
                    "success": False,
                    "error": "File must contain a 'Part Definition' column"
                }), 400
        
        # Find the index of Part Definition column
        part_def_idx = headers.index("Part Definition")
        
        # Create result headers
        result_headers = headers.copy()
        
        # Ensure all required columns exist
        required_columns = [
            "Abbreviation", "Original Length", "Final Length", 
            "Length Reduction", "Applied Rules", "AI Confidence", 
            "Is Standard", "Suggestions", "Method Used"
        ]
        
        for col in required_columns:
            if col not in result_headers:
                result_headers.append(col)
        
        # Process each row
        start_time = time.time()
        result_data = [result_headers]
        processed_count = 0
        success_count = 0
        total_reduction = 0
        
        for row_idx, row in enumerate(csv_data[1:], 1):
            if len(row) <= part_def_idx:
                # Skip rows that don't have enough columns
                continue
                
            # Get part definition
            part_def = row[part_def_idx]
            
            # Skip empty definitions
            if not part_def:
                continue
            
            # Use abbreviation function
            abbreviated, orig_len, applied_rules, final_len, method_used = abbreviate_text(
                part_def, target_length, use_ml)
            
            # Track statistics
            processed_count += 1
            if final_len <= target_length:
                success_count += 1
            
            if orig_len > 0:
                reduction_pct = ((orig_len - final_len) / orig_len) * 100
                total_reduction += reduction_pct
            
            # Get verification results
            verification = verify_abbreviation(part_def, abbreviated, applied_rules)
            
            # Create result row (copy original data and add our new columns)
            result_row = row.copy()
            
            # Add abbreviation columns if needed
            while len(result_row) < len(result_headers):
                result_row.append("")
            
            # Set abbreviation data
            abbr_idx = result_headers.index("Abbreviation")
            orig_len_idx = result_headers.index("Original Length")
            final_len_idx = result_headers.index("Final Length") 
            len_red_idx = result_headers.index("Length Reduction")
            applied_idx = result_headers.index("Applied Rules") 
            conf_idx = result_headers.index("AI Confidence")
            std_idx = result_headers.index("Is Standard")
            sugg_idx = result_headers.index("Suggestions")
            method_idx = result_headers.index("Method Used")
            
            result_row[abbr_idx] = abbreviated
            result_row[orig_len_idx] = str(orig_len)
            result_row[final_len_idx] = str(final_len)
            
            # Calculate length reduction percentage
            if orig_len > 0:
                reduction_str = f"{((orig_len - final_len) / orig_len) * 100:.1f}%"
            else:
                reduction_str = "0.0%"
                
            result_row[len_red_idx] = reduction_str
            result_row[applied_idx] = ", ".join(applied_rules)
            result_row[conf_idx] = str(verification["confidence"])
            result_row[std_idx] = "Yes" if verification.get("is_standard", False) else "No"
            result_row[sugg_idx] = ", ".join(verification.get("suggestions", []))
            result_row[method_idx] = method_used
            
            # Add to result data
            result_data.append(result_row)
            
            # Log every 100 rows for long files
            if processed_count % 100 == 0:
                logger.info(f"Processed {processed_count} rows...")
        
        # Calculate processing time and statistics
        processing_time = time.time() - start_time
        avg_reduction = total_reduction / processed_count if processed_count > 0 else 0
        success_rate = success_count / processed_count * 100 if processed_count > 0 else 0
        
        logger.info(f"File processing completed: {processed_count} rows in {processing_time:.2f}s")
        logger.info(f"Success rate: {success_rate:.1f}%, Avg reduction: {avg_reduction:.1f}%")
        
        # Create output CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerows(result_data)
        
        # Create statistics
        stats = {
            "processed_count": processed_count,
            "success_count": success_count,
            "success_rate": f"{success_rate:.1f}%",
            "avg_reduction": f"{avg_reduction:.1f}%",
            "processing_time": f"{processing_time:.2f}s",
            "method_used": "ML+Rules" if use_ml else "Rules only"
        }
        
        # Save statistics for dashboard
        try:
            os.makedirs("data", exist_ok=True)
            
            # Update running statistics
            stats_file = os.path.join("data", "abbreviation_stats.json")
            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    existing_stats = json.load(f)
                    
                # Update cumulative stats
                existing_stats["total_processed"] = existing_stats.get("total_processed", 0) + processed_count
                existing_stats["files_processed"] = existing_stats.get("files_processed", 0) + 1
                
                # Calculate weighted average for success rate and reduction
                old_total = existing_stats.get("total_processed", 0) - processed_count
                old_success_rate = float(existing_stats.get("success_rate", "0").rstrip('%'))
                old_reduction = float(existing_stats.get("avg_reduction", "0").rstrip('%'))
                
                new_success_rate = ((old_total * old_success_rate) + (processed_count * success_rate)) / existing_stats["total_processed"]
                new_reduction = ((old_total * old_reduction) + (processed_count * avg_reduction)) / existing_stats["total_processed"]
                
                existing_stats["success_rate"] = f"{new_success_rate:.1f}%"
                existing_stats["avg_reduction"] = f"{new_reduction:.1f}%"
                
                # Update method counts
                method_key = "ml_hybrid" if use_ml else "rule_based"
                if "methods" not in existing_stats:
                    existing_stats["methods"] = {}
                existing_stats["methods"][method_key] = existing_stats["methods"].get(method_key, 0) + processed_count
                
                # Save updated stats
                with open(stats_file, 'w') as f:
                    json.dump(existing_stats, f, indent=2)
            else:
                # Create new stats file
                initial_stats = {
                    "total_processed": processed_count,
                    "files_processed": 1,
                    "success_rate": f"{success_rate:.1f}%",
                    "avg_reduction": f"{avg_reduction:.1f}%",
                    "methods": {
                        "ml_hybrid" if use_ml else "rule_based": processed_count
                    }
                }
                
                with open(stats_file, 'w') as f:
                    json.dump(initial_stats, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving statistics: {str(e)}")
        
        # Return file for download
        return jsonify({
            "success": True,
            "message": "File processed successfully",
            "csv_data": output.getvalue(),
            "stats": stats,
            "filename": file.filename
        })
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/ml/status', methods=['GET'])
@api_error_handler
def api_ml_status():
    """Get the status of ML components"""
    ml_status = get_ml_status()
    
    # Add more detailed model information if available
    models_info = {}
    for model_type, model_id in ml_status.get('model_registry', {}).items():
        model_details = model_manager.model_metrics.get(model_type, {}).get(model_id, {})
        models_info[model_type] = {
            'id': model_id,
            'metrics': model_details.get('metrics', {}),
            'timestamp': model_details.get('timestamp', '')
        }
    
    return jsonify({
        "success": True,
        "status": ml_status,
        "models": models_info
    })

@api_bp.route('/dictionary', methods=['GET'])
@api_error_handler
def api_get_dictionary():
    """Get the current abbreviation dictionary"""
    # Convert to list of entries for easier consumption
    entries = [{"original": key, "abbreviated": value} for key, value in abbreviation_dict.items()]
    
    return jsonify({
        "success": True,
        "entries": entries,
        "count": len(entries)
    })

@api_bp.route('/dictionary', methods=['POST'])
@api_error_handler
def api_update_dictionary():
    """Update the abbreviation dictionary"""
    # Validate form data
    form_data = validate_form_data(request, ['entries'])
    
    try:
        # Parse entries
        entries = json.loads(form_data.get('entries', '[]'))
        
        if not isinstance(entries, list):
            return jsonify({
                "success": False,
                "error": "Entries must be a list of {original, abbreviated} objects"
            }), 400
        
        # Track changes
        added = 0
        updated = 0
        invalid = 0
        
        # Process entries
        for entry in entries:
            if not isinstance(entry, dict) or 'original' not in entry or 'abbreviated' not in entry:
                invalid += 1
                continue
                
            original = entry['original']
            abbreviated = entry['abbreviated']
            
            if not original or not abbreviated:
                invalid += 1
                continue
                
            if original in abbreviation_dict:
                updated += 1
            else:
                added += 1
                
            abbreviation_dict[original] = abbreviated
        
        # Save the updated dictionary
        save_abbreviation_dict(abbreviation_dict)
        
        return jsonify({
            "success": True,
            "added": added,
            "updated": updated,
            "invalid": invalid,
            "total": len(abbreviation_dict)
        })
        
    except json.JSONDecodeError:
        return jsonify({
            "success": False,
            "error": "Invalid JSON format for entries"
        }), 400

@api_bp.route('/config', methods=['GET'])
@api_error_handler
def api_get_config():
    """Get the current configuration"""
    # Get only the user-facing configuration (not internal settings)
    user_config = {
        "abbreviation": config.get("abbreviation"),
        "ui": config.get("ui"),
        "files": {
            "allowed_extensions": config.get("files.allowed_extensions"),
            "max_file_size_mb": config.get("files.max_file_size_mb")
        }
    }
    
    return jsonify({
        "success": True,
        "config": user_config
    })

@api_bp.route('/config', methods=['POST'])
@api_error_handler
def api_update_config():
    """Update configuration settings"""
    # Validate form data
    form_data = validate_form_data(request)
    
    try:
        # Parse config updates
        config_updates = json.loads(form_data.get('config', '{}'))
        
        if not isinstance(config_updates, dict):
            return jsonify({
                "success": False,
                "error": "Config updates must be a dictionary"
            }), 400
        
        # Process updates
        updated_keys = []
        
        def process_config_updates(updates, prefix=""):
            nonlocal updated_keys
            
            for key, value in updates.items():
                full_key = f"{prefix}.{key}" if prefix else key
                
                if isinstance(value, dict):
                    # Recursively process nested dictionaries
                    process_config_updates(value, full_key)
                else:
                    # Update the setting
                    config.set(full_key, value)
                    updated_keys.append(full_key)
        
        # Process all updates
        process_config_updates(config_updates)
        
        return jsonify({
            "success": True,
            "updated_keys": updated_keys
        })
        
    except json.JSONDecodeError:
        return jsonify({
            "success": False,
            "error": "Invalid JSON format for config updates"
        }), 400

@api_bp.route('/stats', methods=['GET'])
@api_error_handler
def api_get_stats():
    """Get abbreviation statistics"""
    # Read from stats file if it exists
    stats_file = os.path.join("data", "abbreviation_stats.json")
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r') as f:
                stats = json.load(f)
                return jsonify({
                    "success": True,
                    "stats": stats
                })
        except:
            pass
    
    # Return placeholder data
    return jsonify({
        "success": True,
        "stats": {
            "total_processed": 1243,
            "files_processed": 8,
            "success_rate": "87.2%",
            "avg_reduction": "43.5%",
            "methods": {
                "ml_hybrid": 782,
                "ml_basic": 124,
                "rule_based": 337
            },
            "patterns": {
                "truncation": 542,
                "vowel_removal": 287,
                "first_last": 164,
                "custom": 250
            }
        }
    })