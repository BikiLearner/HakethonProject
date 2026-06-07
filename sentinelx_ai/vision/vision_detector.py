"""
Vision Detection Module - Robust Lazy Loading
"""
import cv2
import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger("SentinelX.Vision")

@dataclass
class DetectionResult:
    person_detected: bool
    confidence: float
    detections_count: int
    ppe_detected: bool = False
    frame: Optional[np.ndarray] = None

class VisionDetector:
    def __init__(self, config: Dict = None, use_cpu: bool = True):
        from utils.config import VISION_CONFIG
        self.config = config or VISION_CONFIG
        self.use_cpu = use_cpu
        
        # Don't load anything heavy in __init__
        self.model = None
        self.cap = None
        self.dummy_mode = False
        self.is_initialized = False
        self.hazard_zone = np.array([[0.2, 0.5], [0.8, 0.5], [0.9, 0.9], [0.1, 0.9]], np.float32)
        self.zone_violation = False

    def initialize(self):
        """Perform heavy loading here (called from thread)"""
        if self.is_initialized:
            return
        
        logger.info("Vision Engine: Loading YOLOv8 Model...")
        try:
            from ultralytics import YOLO
            self.model = YOLO("yolov8n.pt")
            if self.use_cpu:
                self.model.to("cpu")
            logger.info("Vision Engine: Model Loaded.")
        except Exception as e:
            logger.error(f"Vision Engine: Model failed to load: {e}")
            self.dummy_mode = True
            
        logger.info(f"Vision Engine: Opening Camera {self.config['camera_id']}...")
        try:
            self.cap = cv2.VideoCapture(self.config["camera_id"], cv2.CAP_DSHOW)
            if not self.cap or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.config["camera_id"])
            
            if self.cap and self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                logger.info("Vision Engine: Camera Connected.")
            else:
                logger.warning("Vision Engine: Could not open camera. Running in dummy mode.")
                self.dummy_mode = True
        except Exception as e:
            logger.error(f"Vision Engine: Camera crash: {e}")
            self.dummy_mode = True
            
        self.is_initialized = True

    def detect(self) -> DetectionResult:
        if not self.is_initialized:
            return DetectionResult(False, 0.0, 0, False, None)

        if self.dummy_mode or self.model is None:
            dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(dummy_frame, "VISION OFFLINE", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return DetectionResult(False, 0.0, 0, False, dummy_frame)

        try:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                return DetectionResult(False, 0.0, 0, False, None)

            # Basic inference
            results = self.model(frame, conf=0.5, classes=0, verbose=False)
            
            person_count = 0
            ppe_count = 0
            max_conf = 0.0
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    person_count += 1
                    max_conf = max(max_conf, float(box.conf[0]))
                    # Simple center check for zone
                    coords = tuple(map(int, box.xyxy[0]))
                    cv2.rectangle(frame, (coords[0], coords[1]), (coords[2], coords[3]), (0, 255, 0), 2)
            
            return DetectionResult(person_count > 0, max_conf, person_count, False, frame)
        except Exception as e:
            logger.error(f"Detection Error: {e}")
            return DetectionResult(False, 0.0, 0, False, None)

    def close(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        self.is_initialized = False
