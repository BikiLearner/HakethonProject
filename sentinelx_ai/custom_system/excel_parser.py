import pandas as pd
import json
import os
import logging

logger = logging.getLogger("SentinelX.ExcelParser")

def parse_machine_excel(file_path):
    """
    Parses an Excel file containing machine specifications and thresholds.
    Expected columns: Machine Name, Sensor Name, Warning Threshold, Critical Threshold, Unit, Rule, Environment
    """
    try:
        df = pd.read_excel(file_path)
        
        # Normalize column names (strip whitespace and lowercase)
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        
        config = {
            "machine_name": "Generic Machine",
            "sensors": {},
            "rules": [],
            "environment": {}
        }
        
        if not df.empty:
            if "machine_name" in df.columns:
                config["machine_name"] = str(df["machine_name"].iloc[0])
            
            for _, row in df.iterrows():
                sensor_name = str(row.get("sensor_name", "")).strip().lower()
                if sensor_name:
                    config["sensors"][sensor_name] = {
                        "warning": float(row.get("warning_threshold", 0)),
                        "critical": float(row.get("critical_threshold", 0)),
                        "unit": str(row.get("unit", "")),
                        "description": str(row.get("description", f"{sensor_name} sensor"))
                    }
                
                rule = str(row.get("rule", "")).strip()
                if rule and rule not in config["rules"]:
                    config["rules"].append(rule)
                    
                env_key = str(row.get("environment_key", "")).strip()
                env_val = str(row.get("environment_value", "")).strip()
                if env_key:
                    config["environment"][env_key] = env_val

        return config
    except Exception as e:
        logger.error(f"Error parsing Excel: {e}")
        return None

def save_config_json(config, output_path="custom_system/active_config.json"):
    try:
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving config JSON: {e}")
        return False
