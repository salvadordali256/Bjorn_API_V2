"""
HVAC abbreviation dictionary management
"""
import os
import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Dictionary of common HVAC abbreviations
DEFAULT_ABBREVIATIONS = {
    "Accessory": "Accy", 
    "Actuator": "Act", 
    "Adapter": "Adapt", 
    "Aluminum": "Alum", 
    "Aluminium": "Alum",
    "Analog": "Anlg", 
    "Assembly": "Assy", 
    "Averaging": "Avg", 
    "BACnet": "Bnet", 
    "Black": "Blk",
    "Blower": "Blwr", 
    "Breaker": "Brkr", 
    "Bronze": "Brz", 
    "Butterfly": "Bfly", 
    "Cable": "Cbl",
    "Capacitor": "Cap", 
    "Capillary": "Cap", 
    "Check": "Chk", 
    "Compressor": "Comp", 
    "Controller": "Ctrlr",
    "Control": "Ctrl", 
    "Copper": "Cu", 
    "Cover": "Cvr", 
    "Detector": "Detect", 
    "Differential": "Diff",
    "Electric": "Elec", 
    "Enclosure": "Encl", 
    "Evaporator": "Evap", 
    "Expansion": "Exp", 
    "Flange": "Flg",
    "Flare": "Flr", 
    "Floating": "Flt", 
    "Gasket": "Gskt", 
    "Hazardous": "Hzrd", 
    "Heater": "Htr",
    "Heat": "Ht", 
    "High": "Hi", 
    "Level": "Lvl", 
    "Low": "Lo", 
    "Modulating": "Mod", 
    "Modular": "Mod",
    "Motor": "Mtr", 
    "Mounted": "Mtd", 
    "Mount": "Mt", 
    "Mounting": "Mtg", 
    "Pack": "Pk", 
    "Package": "Pkg",
    "Panel": "Pnl", 
    "Plate": "Plt", 
    "Pressure": "Press", 
    "Probe": "Prb", 
    "Programmable": "Prog",
    "Programming": "Prog", 
    "Program": "Prog", 
    "Regulator": "Reg", 
    "Relay": "Rly", 
    "Relief": "Rlf",
    "Remote": "Rmt", 
    "Sensor": "Sens", 
    "Sens": "Sns", 
    "Setpoint": "SetPt", 
    "Set Point": "SetPt",
    "StainlessSteel": "SS", 
    "Stanless Steel": "SS", 
    "Sweat": "Swt", 
    "Switch": "Sw", 
    "Temperature": "Temp",
    "Thermistor": "Thrmst", 
    "Thermostat": "Tstat", 
    "Transceiver": "Trnsvr", 
    "Transmitter": "Trnsmt",
    "Valve": "Vlv", 
    "Water": "Wtr", 
    "White": "Wht", 
    "Without": "w/o", 
    "With": "w/", 
    "Explosion": "Expl",
    "Proof": "Prf", 
    "Protection": "Prot", 
    "Double": "Dbl", 
    "Minutes": "Min", 
    "Minute": "Min",
    "Inches": "\"", 
    "Inch": "\"", 
    "º": "Deg", 
    "Piece": "Pc", 
    "Voltage": "Volt", 
    "Amps": "Amp",
    "Board": "Brd", 
    "Extension": "Ext", 
    "Transformer": "Xfrmr", 
    "ExplPrf": "X-Prf", 
    "Standard": "Std",
    "Round": "Rnd", 
    "Density": "Dens", 
    "Reflector": "Rflctr", 
    "Disconnect": "Discon", 
    "Regulating": "Reg",
    "Replacement": "Repl", 
    "Infrared": "IR", 
    "Filter": "Filt", 
    "Pannel": "Pnl", 
    "Included": "Incl",
    "Includes": "Incl", 
    "Mted": "Mtd", 
    "Position": "Pos", 
    "Manual Reset": "MR", 
    "Damper": "Dmpr",
    "Label": "Lbl",
    "Assemblies": "ASSY",
    "Assembly": "ASSY",
    "Assembled": "ASSD",
    "Cabinet": "CAB",
    "Cabinets": "CABS",
    "Factory": "FACT",
    "Showers": "SHWR",
    "Shower": "SHWR",
    "Recirculation": "RECIRC",
    "Piping": "PIPE",
    "Stainless": "STSTL",
    "Chrome": "CHR",
    "Plated": "PLT",
    "Thermostatic": "THERM",
    "Mixing": "MIX",
    "Exposed": "EXP",
    "Single": "SNGL",
    "Series": "SER",
    "Hydrotherapy": "HYDRO",
    "Connection": "CONN",
    "Capacity": "CAP",
    "Group": "GRP"
}

def load_abbreviation_dict() -> Dict[str, str]:
    """
    Load abbreviation dictionary from file or use default
    
    Returns:
        Dictionary of abbreviations
    """
    dict_path = 'data/abbreviations.json'
    abbreviation_dict = DEFAULT_ABBREVIATIONS.copy()
    
    # Try to load custom abbreviations
    if os.path.exists(dict_path):
        try:
            with open(dict_path, 'r') as f:
                custom_abbrevs = json.load(f)
                abbreviation_dict.update(custom_abbrevs)
                logger.info(f"Loaded {len(custom_abbrevs)} custom abbreviations")
        except Exception as e:
            logger.error(f"Error loading custom abbreviations: {e}")
    else:
        # Create the abbreviations file with defaults
        os.makedirs(os.path.dirname(dict_path), exist_ok=True)
        try:
            with open(dict_path, 'w') as f:
                json.dump(DEFAULT_ABBREVIATIONS, f, indent=2)
                logger.info(f"Created default abbreviations file at {dict_path}")
        except Exception as e:
            logger.error(f"Error creating abbreviations file: {e}")
    
    return abbreviation_dict

def save_abbreviation_dict(abbreviation_dict: Dict[str, str]) -> bool:
    """
    Save abbreviation dictionary to file
    
    Args:
        abbreviation_dict: Dictionary of abbreviations
    
    Returns:
        Success status
    """
    dict_path = 'data/abbreviations.json'
    os.makedirs(os.path.dirname(dict_path), exist_ok=True)
    
    try:
        with open(dict_path, 'w') as f:
            json.dump(abbreviation_dict, f, indent=2)
            logger.info(f"Saved {len(abbreviation_dict)} abbreviations to {dict_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving abbreviations: {e}")
        return False