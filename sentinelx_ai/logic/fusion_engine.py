"""
Fusion Engine Module
Combines telemetry data with vision data for comprehensive analysis
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime
from utils.config import FUSION_CONFIG


@dataclass
class FusedData:
    """Data class for fused telemetry and vision data"""
    timestamp: float
    
    # Telemetry
    temperature: float
    vibration: float
    rpm: int
    
    # Vision
    person_detected: bool
    person_confidence: float
    
    # Fused analysis
    risk_level: str  # LOW, MEDIUM, HIGH
    risk_score: float  # 0.0 to 1.0
    fusion_reason: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "temperature": round(self.temperature, 2),
            "vibration": round(self.vibration, 3),
            "rpm": self.rpm,
            "person_detected": self.person_detected,
            "person_confidence": round(self.person_confidence, 2),
            "risk_level": self.risk_level,
            "risk_score": round(self.risk_score, 2),
            "fusion_reason": self.fusion_reason,
        }


class FusionEngine:
    """
    Fusion engine that combines telemetry and vision data
    Implements intelligent logic to assess operational risk
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize fusion engine
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or FUSION_CONFIG
        self.history: List[FusedData] = []
        self.last_fusion = None
    
    def fuse(
        self,
        temperature: float,
        vibration: float,
        rpm: int,
        person_detected: bool,
        person_confidence: float,
        temp_trend: float = 0.0,
        timestamp: float = None,
    ) -> FusedData:
        """
        Fuse telemetry and vision data
        
        Args:
            temperature: Machine temperature in Celsius
            vibration: Vibration level in mm/s
            rpm: Machine RPM
            person_detected: Whether person is detected
            person_confidence: Confidence of person detection
            temp_trend: Temperature trend (degrees/second)
            timestamp: Timestamp of reading
        
        Returns:
            FusedData: Fused analysis result
        """
        if timestamp is None:
            import time
            timestamp = time.time()
        
        # Calculate individual risk factors
        temp_risk = self._assess_temperature_risk(temperature)
        vib_risk = self._assess_vibration_risk(vibration)
        rpm_risk = self._assess_rpm_risk(rpm)
        person_risk = self._assess_person_risk(person_detected, person_confidence)
        trend_risk = self._assess_trend_risk(temp_trend)
        
        # Combine risks with fusion logic
        risk_score, risk_level, reason = self._combine_risks(
            temp_risk, vib_risk, rpm_risk, person_risk, trend_risk,
            person_detected, temperature, temp_trend
        )
        
        # Create fused data object
        fused = FusedData(
            timestamp=timestamp,
            temperature=temperature,
            vibration=vibration,
            rpm=rpm,
            person_detected=person_detected,
            person_confidence=person_confidence,
            risk_level=risk_level,
            risk_score=risk_score,
            fusion_reason=reason,
        )
        
        # Store in history
        self.history.append(fused)
        if len(self.history) > 300:  # Keep last 5 minutes at 1 Hz
            self.history.pop(0)
        
        self.last_fusion = fused
        return fused
    
    def _assess_temperature_risk(self, temperature: float) -> float:
        """
        Assess risk based on temperature
        
        Args:
            temperature: Temperature in Celsius
        
        Returns:
            float: Risk score 0.0-1.0
        """
        if temperature < 70:
            return 0.0
        elif temperature < 80:
            return 0.3
        elif temperature < 85:
            return 0.6
        else:
            return 1.0
    
    def _assess_vibration_risk(self, vibration: float) -> float:
        """
        Assess risk based on vibration
        
        Args:
            vibration: Vibration level in mm/s
        
        Returns:
            float: Risk score 0.0-1.0
        """
        if vibration < 1.0:
            return 0.0
        elif vibration < 2.0:
            return 0.3
        elif vibration < 3.0:
            return 0.6
        else:
            return 1.0
    
    def _assess_rpm_risk(self, rpm: int) -> float:
        """
        Assess risk based on RPM
        
        Args:
            rpm: RPM value
        
        Returns:
            float: Risk score 0.0-1.0
        """
        if rpm < 2000:
            return 0.0
        elif rpm < 2500:
            return 0.2
        elif rpm < 3000:
            return 0.5
        else:
            return 1.0
    
    def _assess_person_risk(self, person_detected: bool, confidence: float) -> float:
        """
        Assess risk based on person detection
        
        Args:
            person_detected: Whether person is in the area
            confidence: Detection confidence
        
        Returns:
            float: Risk score 0.0-1.0
        """
        if not person_detected:
            return 0.0
        
        # Higher confidence = higher risk (more certain detection)
        return confidence
    
    def _assess_trend_risk(self, temp_trend: float) -> float:
        """
        Assess risk based on temperature trend
        
        Args:
            temp_trend: Temperature change rate (degrees/second)
        
        Returns:
            float: Risk score 0.0-1.0
        """
        from utils.config import REASONING_CONFIG
        
        threshold = REASONING_CONFIG["temperature_rise_rate_threshold"]
        
        if temp_trend < threshold:
            return 0.0
        elif temp_trend < threshold * 2:
            return 0.4
        else:
            return 0.8
    
    def _combine_risks(
        self, temp_risk: float, vib_risk: float, rpm_risk: float,
        person_risk: float, trend_risk: float,
        person_detected: bool, temperature: float, temp_trend: float
    ) -> tuple:
        """
        Probabilistic risk fusion using weighted Bayesian-like approach
        """
        
        # Weights for different factors (Industry-standard weights)
        weights = {
            "temperature": 0.35,
            "vibration": 0.25,
            "rpm": 0.15,
            "trend": 0.25
        }
        
        # Base machine risk (weighted average)
        machine_risk = (
            temp_risk * weights["temperature"] +
            vib_risk * weights["vibration"] +
            rpm_risk * weights["rpm"] +
            trend_risk * weights["trend"]
        )
        
        # Person detection acts as a risk amplifier/multiplier (Contextual Fusion)
        if person_detected:
            # If person is present, machine risk is amplified because of safety implications
            # Using a non-linear amplification
            amplified_risk = 1.0 - (1.0 - machine_risk) * (1.0 - person_risk)
            risk_score = amplified_risk
        else:
            risk_score = machine_risk
        
        # Normalize to 0-1
        risk_score = max(0.0, min(1.0, risk_score))
        
        # Determine risk level and generate reason
        if risk_score >= 0.75:
            risk_level = "HIGH"
            reason = self._generate_high_risk_reason(
                temp_risk, vib_risk, rpm_risk, person_risk, temp_trend
            )
        elif risk_score >= 0.4:
            risk_level = "MEDIUM"
            reason = self._generate_medium_risk_reason(
                temp_risk, vib_risk, rpm_risk, person_risk
            )
        else:
            risk_level = "LOW"
            reason = "Operational state within nominal bounds"
        
        return risk_score, risk_level, reason
    
    def _generate_high_risk_reason(
        self, temp_risk: float, vib_risk: float, rpm_risk: float,
        person_risk: float, temp_trend: float
    ) -> str:
        """Generate reason for high risk"""
        reasons = []
        
        if temp_risk > 0.7:
            reasons.append("High temperature detected")
        if vib_risk > 0.7:
            reasons.append("High vibration levels")
        if rpm_risk > 0.7:
            reasons.append("High RPM")
        if person_risk > 0.5:
            reasons.append("Person detected near machine")
        if temp_trend > 0.2:
            reasons.append("Rapid temperature increase")
        
        if not reasons:
            reasons.append("Multiple risk factors detected")
        
        return " + ".join(reasons)
    
    def _generate_medium_risk_reason(
        self, temp_risk: float, vib_risk: float, rpm_risk: float,
        person_risk: float
    ) -> str:
        """Generate reason for medium risk"""
        reasons = []
        
        if temp_risk > 0.4:
            reasons.append("Elevated temperature")
        if vib_risk > 0.4:
            reasons.append("Elevated vibration")
        if rpm_risk > 0.4:
            reasons.append("Elevated RPM")
        if person_risk > 0.3:
            reasons.append("Person in vicinity")
        
        if not reasons:
            reasons.append("Some risk factors present")
        
        return " + ".join(reasons)
    
    def get_history(self, seconds: int = 60) -> List[FusedData]:
        """
        Get fusion history for last N seconds
        
        Args:
            seconds: Number of seconds to retrieve
        
        Returns:
            List of FusedData objects
        """
        import time
        current_time = time.time()
        cutoff = current_time - seconds
        
        return [f for f in self.history if f.timestamp >= cutoff]
    
    def get_last_fusion(self) -> FusedData:
        """Get last fusion result"""
        return self.last_fusion
