"""
System Core - Orchestrates background processing tasks
Stabilized for Python 3.14 + Streamlit
"""
import threading
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from simulator.machine_simulator import MachineSimulator
from vision.vision_detector import VisionDetector, DetectionResult
from logic.fusion_engine import FusionEngine
from logic.reasoning_engine import ReasoningEngine

logger = logging.getLogger("SentinelX.Core")

@dataclass
class SystemState:
    machine_state: Any = None
    detection_result: Any = None
    fusion_result: Any = None
    decision: Any = None
    fusion_history: List[Any] = None
    last_frame: Any = None
    is_running: bool = False
    last_update_time: float = 0.0
    camera_error: Optional[str] = None

class SystemCore:
    def __init__(self):
        # Engines
        self.simulator = MachineSimulator()
        self.vision_detector = VisionDetector(use_cpu=True)
        self.fusion_engine = FusionEngine()
        self.reasoning_engine = ReasoningEngine()
        
        # Shared State
        self.state = SystemState(
            machine_state=self.simulator.get_state(),
            detection_result=DetectionResult(False, 0.0, 0, False, None),
            fusion_history=[],
            is_running=False
        )
        self.lock = threading.Lock()
        self._stop_event = threading.Event()
        self._threads = []

    def start(self):
        if self.state.is_running:
            return
        logger.info("Core: Starting background threads...")
        self._stop_event.clear()
        self._threads = [
            threading.Thread(target=self._telemetry_loop, name="Telemetry", daemon=True),
            threading.Thread(target=self._vision_loop, name="Vision", daemon=True),
            threading.Thread(target=self._logic_loop, name="Logic", daemon=True)
        ]
        for t in self._threads:
            t.start()
        self.state.is_running = True

    def _telemetry_loop(self):
        logger.info("Thread: Telemetry started.")
        while not self._stop_event.is_set():
            try:
                with self.lock:
                    self.state.machine_state = self.simulator.update()
            except Exception as e:
                logger.error(f"Telemetry error: {e}")
            time.sleep(0.1)

    def _vision_loop(self):
        logger.info("Thread: Vision started. Initializing hardware...")
        self.vision_detector.initialize()
        while not self._stop_event.is_set():
            try:
                res = self.vision_detector.detect()
                with self.lock:
                    self.state.detection_result = res
                    if res.frame is not None:
                        self.state.last_frame = res.frame.copy()
            except Exception as e:
                logger.error(f"Vision error: {e}")
            time.sleep(0.1)

    def _logic_loop(self):
        logger.info("Thread: Logic started. Initializing ML...")
        self.reasoning_engine.initialize()
        while not self._stop_event.is_set():
            try:
                with self.lock:
                    if self.state.machine_state and self.state.detection_result:
                        fused = self.fusion_engine.fuse(
                            temperature=self.state.machine_state.temperature,
                            vibration=self.state.machine_state.vibration,
                            rpm=self.state.machine_state.rpm,
                            person_detected=self.state.detection_result.person_detected,
                            person_confidence=self.state.detection_result.confidence,
                            temp_trend=self.simulator.get_temperature_trend(30),
                            timestamp=self.state.machine_state.timestamp,
                        )
                        self.state.fusion_result = fused
                        self.state.fusion_history.append(fused)
                        if len(self.state.fusion_history) > 300:
                            self.state.fusion_history.pop(0)
                        
                        self.state.decision = self.reasoning_engine.analyze(fused.to_dict())
                        self.state.last_update_time = time.time()
                        
                        # High-fidelity trace log
                        logger.debug(f"[CORE LOOP] Fused State -> Temp: {self.state.machine_state.temperature:.2f}, Status: {self.state.decision.status}")
            except Exception as e:
                logger.error(f"Logic error: {e}")
            time.sleep(0.5)

    def get_snapshot(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "machine_state": self.state.machine_state,
                "detection_result": self.state.detection_result,
                "fusion_result": self.state.fusion_result,
                "decision": self.state.decision,
                "fusion_history": list(self.state.fusion_history),
                "last_frame": self.state.last_frame,
                "load": self.simulator.load,
                "wear_level": self.simulator.wear_level,
                "last_update": self.state.last_update_time
            }

    def set_triggers(self, warning: bool, critical: bool):
        with self.lock:
            self.simulator.set_warning_trigger(warning)
            self.simulator.set_critical_trigger(critical)

    def set_load(self, load: float):
        with self.lock:
            self.simulator.set_load(load)

    def change_camera(self, camera_id: int):
        with self.lock:
            self.vision_detector.close()
            self.vision_detector.config["camera_id"] = camera_id
            self.vision_detector.initialize()

    def probe_cameras(self) -> List[int]:
        # Return a simple list to avoid crashing during UI probe
        return [0, 1, 2]
