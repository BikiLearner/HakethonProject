"""
Machine Simulator Module
Simulates realistic industrial machine telemetry data (Digital Twin)
"""

import math
import time
import random
from dataclasses import dataclass
from typing import Dict, Any
from utils.config import MACHINE_CONFIG


@dataclass
class MachineState:
    """Data class for machine telemetry"""
    temperature: float
    vibration: float
    rpm: int
    timestamp: float
    state: str  # NORMAL, WARNING, CRITICAL
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "temperature": round(self.temperature, 2),
            "vibration": round(self.vibration, 3),
            "rpm": self.rpm,
            "timestamp": self.timestamp,
            "state": self.state,
        }


class MachineSimulator:
    """
    Simulates a real industrial machine with realistic dynamics.
    Generates temperature, vibration, and RPM readings using a Digital Twin approach.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the machine simulator
        
        Args:
            config: Configuration dictionary (uses defaults if None)
        """
        self.config = config or MACHINE_CONFIG
        
        # State variables
        self.temperature = self.config["initial_temperature"]
        self.vibration = self.config["initial_vibration"]
        self.rpm = self.config["initial_rpm"]
        self.load = 0.5  # 0.0 to 1.0
        self.wear_level = 0.0  # Increases over time
        self.state = "NORMAL"
        self.last_update = time.time()
        
        # History for trend detection
        self.temp_history = [self.temperature]
        
        # Manual override triggers
        self.trigger_warning = False
        self.trigger_critical = False

    def set_load(self, load: float):
        """Set machine load (0.0 to 1.0)"""
        self.load = max(0.0, min(1.0, load))

    def set_critical_trigger(self, enabled: bool = True):
        """Manually trigger critical state"""
        self.trigger_critical = enabled
    
    def set_warning_trigger(self, enabled: bool = True):
        """Manually trigger warning state"""
        self.trigger_warning = enabled
    
    def reset(self):
        """Reset machine to normal state"""
        self.temperature = self.config["initial_temperature"]
        self.vibration = self.config["initial_vibration"]
        self.rpm = self.config["initial_rpm"]
        self.wear_level = 0.0
        self.load = 0.5
        self.state = "NORMAL"
        self.trigger_warning = False
        self.trigger_critical = False
        self.temp_history = [self.temperature]

    def _update_temperature(self, dt: float):
        """Update temperature with physics-based coupling"""
        # Base ambient cooling/heating
        ambient_temp = 25.0
        cooling_constant = 0.05
        
        # Heating from RPM and Load
        # Heat generated is proportional to RPM^2 and Load
        normalized_rpm = self.rpm / 3000.0
        heat_generated = (normalized_rpm**2 * self.load * 5.0) + (self.wear_level * 2.0)
        
        if self.trigger_critical:
            heat_generated *= 3.0
        elif self.trigger_warning:
            heat_generated *= 1.5
            
        # Newton's law of cooling + internal heating
        temp_change = (heat_generated - cooling_constant * (self.temperature - ambient_temp)) * dt
        self.temperature += temp_change
        
        # Add realistic noise
        self.temperature += random.gauss(0, 0.05)
        
        # Prevent going below ambient
        self.temperature = max(self.temperature, ambient_temp)
        
        # Update history
        self.temp_history.append(self.temperature)
        if len(self.temp_history) > 600:
            self.temp_history.pop(0)

    def _update_vibration(self, dt: float):
        """Update vibration coupled with RPM and Wear"""
        # Base vibration from RPM
        # Vibration increases with RPM and Wear
        normalized_rpm = self.rpm / 1500.0
        base_vibration = 0.1 * (normalized_rpm**1.5)
        
        # Wear adds stochastic spikes and increases baseline
        wear_effect = self.wear_level * 0.5
        
        self.vibration = base_vibration + wear_effect
        
        if self.trigger_critical:
            self.vibration *= (2.0 + random.random())
        elif self.trigger_warning:
            self.vibration *= (1.2 + random.random() * 0.3)
            
        # Add random noise
        self.vibration += random.gauss(0, 0.01)
        self.vibration = max(0.05, self.vibration)

    def _update_rpm(self, dt: float):
        """Update RPM based on load and triggers"""
        target_rpm = self.config["initial_rpm"]
        
        if self.trigger_critical:
            target_rpm = 3200 + random.randint(-100, 100)
        elif self.trigger_warning:
            target_rpm = 2600 + random.randint(-50, 50)
        else:
            # Fluctuate based on load
            target_rpm = 1500 + (self.load * 500)
            
        # Smooth RPM transition
        rpm_step = 200 * dt
        if self.rpm < target_rpm:
            self.rpm = min(self.rpm + rpm_step, target_rpm)
        elif self.rpm > target_rpm:
            self.rpm = max(self.rpm - rpm_step, target_rpm)
            
        # Add jitter
        self.rpm += random.randint(-5, 5)

    def _update_wear(self, dt: float):
        """Simulate machine wear and tear over time"""
        # Wear increases faster with high RPM and high Temperature
        wear_rate = (self.rpm / 3000.0) * (self.temperature / 100.0) * 0.00001
        self.wear_level += wear_rate * dt
        self.wear_level = min(1.0, self.wear_level)

    def _determine_state(self):
        """Determine machine state based on current values and triggers"""
        if self.trigger_critical or self.temperature > self.config["temp_critical_threshold"] or self.vibration > self.config["vibration_critical_threshold"]:
            self.state = "CRITICAL"
        elif self.trigger_warning or self.temperature > self.config["temp_warning_threshold"] or self.vibration > self.config["vibration_warning_threshold"]:
            self.state = "WARNING"
        else:
            self.state = "NORMAL"

    def update(self) -> MachineState:
        """
        Update machine state and return current telemetry
        
        Returns:
            MachineState: Current machine telemetry
        """
        current_time = time.time()
        dt = current_time - self.last_update
        self.last_update = current_time
        
        # Cap dt
        dt = min(dt, 1.0)
        
        # Update all parameters in order of physical dependency
        self._update_rpm(dt)
        self._update_temperature(dt)
        self._update_vibration(dt)
        self._update_wear(dt)
        
        # Determine state
        self._determine_state()
        
        # Create and return state
        return MachineState(
            temperature=self.temperature,
            vibration=self.vibration,
            rpm=self.rpm,
            timestamp=current_time,
            state=self.state,
        )
    
    def get_state(self) -> MachineState:
        """Get current state without updating"""
        return MachineState(
            temperature=self.temperature,
            vibration=self.vibration,
            rpm=self.rpm,
            timestamp=time.time(),
            state=self.state,
        )
    
    def get_temperature_trend(self, seconds: int = 30) -> float:
        """
        Calculate temperature trend (rate of change)
        
        Args:
            seconds: Lookback period in seconds
        
        Returns:
            float: Temperature change rate (degrees/second)
        """
        if len(self.temp_history) < 2:
            return 0.0
        
        # Get samples from lookback period
        lookback_samples = min(seconds, len(self.temp_history))
        
        if lookback_samples < 2:
            return 0.0
        
        temp_change = self.temp_history[-1] - self.temp_history[-lookback_samples]
        rate = temp_change / lookback_samples
        
        return rate
