"""
Reasoning Engine - Robust Lazy Loading
"""
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger("SentinelX.Reasoning")

@dataclass
class Decision:
    status: str
    confidence: float
    reason: str
    recommended_action: str
    predicted_issue: str
    details: Dict[str, Any]
    anomaly_score: float = 0.0

class ReasoningEngine:
    def __init__(self, config: Dict = None):
        self.config = config
        self.model = None
        self.is_initialized = False
        self.training_data = []

    def initialize(self):
        if self.is_initialized:
            return
        logger.info("Reasoning Engine: Initializing ML Model...")
        try:
            from sklearn.ensemble import IsolationForest
            self.model = IsolationForest(contamination=0.05, random_state=42)
            logger.info("Reasoning Engine: Model Ready.")
        except Exception as e:
            logger.error(f"Reasoning Engine: ML Init failed: {e}")
        self.is_initialized = True

    def analyze(self, fused_data: Dict[str, Any]) -> Decision:
        if not self.is_initialized:
            self.initialize()

        temp = fused_data.get("temperature", 0)
        vib = fused_data.get("vibration", 0)
        person = fused_data.get("person_detected", False)
        risk = fused_data.get("risk_score", 0)
        
        from custom_system.config_manager import ConfigManager
        cm = ConfigManager()
        temp_warning, temp_critical = cm.get_thresholds("temperature", 70.0, 85.0)
        vib_warning, vib_critical = cm.get_thresholds("vibration", 1.0, 3.0)
        
        # Safe rule-based fallback if ML fails
        status = "SAFE"
        action = "NORMAL"
        issue = "NONE"
        
        if temp > temp_critical or vib > vib_critical:
            status = "DANGER"
            action = "SHUTDOWN"
            issue = f"CRITICAL LIMIT (Temp: {temp_critical}, Vib: {vib_critical})"
        elif temp > temp_warning or vib > vib_warning:
            status = "CAUTION"
            action = "MONITOR"
            issue = "ELEVATED PARAMETERS"
        elif person:
            status = "CAUTION"
            action = "WATCH"
            issue = "PERSONNEL PRESENT"

        return Decision(status, 0.9, "Steady", action, issue, {}, 0.0)
