"""
Configuration module for SentinelX AI System
Centralized configuration for all system parameters
"""

# ==================== MACHINE SIMULATOR CONFIG ====================
MACHINE_CONFIG = {
    "sampling_rate": 1.0,  # seconds per reading
    "initial_temperature": 60.0,  # Celsius
    "initial_vibration": 0.5,  # mm/s
    "initial_rpm": 1500,  # rotations per minute
    
    # Thresholds
    "temp_warning_threshold": 75.0,
    "temp_critical_threshold": 90.0,
    "vibration_warning_threshold": 2.0,
    "vibration_critical_threshold": 3.5,
    "rpm_warning_threshold": 2500,
    "rpm_critical_threshold": 3000,
    
    # Realistic change rates (per second)
    "temp_normal_rate": 0.1,  # degrees per second
    "temp_critical_rate": 0.5,  # when in critical state
    "vibration_normal_rate": 0.01,
    "vibration_critical_rate": 0.05,
}

# ==================== VISION CONFIG ====================
VISION_CONFIG = {
    "camera_id": 0,
    "confidence_threshold": 0.5,
    "max_detection_distance": 5.0,  # meters (simulated)
    "frame_width": 640,
    "frame_height": 480,
    "fps": 30,
}

# ==================== FUSION ENGINE CONFIG ====================
FUSION_CONFIG = {
    "temp_person_risk_multiplier": 1.5,  # High temp + person = higher risk
    "history_window": 60,  # seconds of data to consider
    "trend_threshold": 0.05,  # rate of change to consider as trend
}

# ==================== REASONING ENGINE CONFIG ====================
REASONING_CONFIG = {
    "enable_trend_analysis": True,
    "trend_lookback_period": 30,  # seconds
    "temperature_rise_rate_threshold": 0.3,  # degrees/second
    "confidence_level": "high",
}

# ==================== DASHBOARD CONFIG ====================
DASHBOARD_CONFIG = {
    "theme": "dark",
    "refresh_rate": 1.0,  # seconds
    "chart_history_points": 100,
    "show_debug_info": True,
}

# ==================== STATUS COLORS ====================
STATUS_COLORS = {
    "NORMAL": "#00FF00",      # Green
    "WARNING": "#FFA500",     # Orange/Yellow
    "CRITICAL": "#FF0000",    # Red
    "UNKNOWN": "#808080",     # Gray
}

STATUS_EMOJI = {
    "NORMAL": "✅",
    "WARNING": "⚠️",
    "CRITICAL": "🚨",
    "UNKNOWN": "❓",
}

# ==================== LOGGING CONFIG ====================
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}
