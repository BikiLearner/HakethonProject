import json
import os
import logging

logger = logging.getLogger("SentinelX.ConfigManager")

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.config = None
            cls._instance.load_config()
        return cls._instance

    def load_config(self, path="custom_system/active_config.json"):
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Loaded custom configuration from {path}")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        else:
            logger.info("No custom config found, using defaults.")
            self.config = None

    def get_thresholds(self, sensor_name, default_warning, default_critical):
        if self.config and "sensors" in self.config:
            sensor_cfg = self.config["sensors"].get(sensor_name.lower())
            if sensor_cfg:
                return sensor_cfg.get("warning", default_warning), sensor_cfg.get("critical", default_critical)
        return default_warning, default_critical

    def get_machine_name(self):
        if self.config:
            return self.config.get("machine_name", "Generic Machine")
        return "Generic Machine"
    
    def get_all_sensors(self):
        if self.config and "sensors" in self.config:
            return self.config["sensors"]
        return {}
