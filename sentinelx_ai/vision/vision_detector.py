import cv2
import logging
import threading
import time
import numpy as np
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class DetectionResult:
    person_detected: bool
    confidence: float
    person_count: int
    ppe_detected: bool
    frame: Optional[Any] = None

class VisionDetector:
    def __init__(self, use_cpu: bool = True):
        self.logger = logging.getLogger("SentinelX.Vision")
        self.config = {"camera_id": 0, "model_path": "yolov8n.pt"}
        self.model = None
        self.cap = None
        self.use_cpu = use_cpu
        self._lock = threading.Lock()
        self.is_initialized = False
        self.camera_available = True
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3

    def initialize(self):
        with self._lock:
            if self.is_initialized:
                return
            self.logger.info("Vision Engine: Loading YOLOv8 Model...")
            try:
                from ultralytics import YOLO
                self.model = YOLO(self.config["model_path"])
                if self.use_cpu:
                    self.model.to('cpu')
                self.logger.info("Vision Engine: Model Loaded.")
            except Exception as e:
                self.logger.error(f"Model Load Error: {e}")
                return

            self._open_camera()
            self.is_initialized = True

    def _open_camera(self):
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.logger.warning("Vision Engine: Max reconnect attempts reached. Switching to Offline Mode.")
            self.camera_available = False
            return

        try:
            self.logger.info(f"Vision Engine: Opening Camera {self.config['camera_id']}...")
            if self.cap is not None:
                self.cap.release()
            
            # Suppress OpenCV warnings temporarily
            # cv2.VideoCapture can be noisy if no camera exists
            self.cap = cv2.VideoCapture(self.config["camera_id"], cv2.CAP_V4L2 if self.config["camera_id"] == 0 else cv2.CAP_ANY)
            
            if not self.cap.isOpened():
                # Try generic API if V4L2 fails
                self.cap = cv2.VideoCapture(self.config["camera_id"])

            if self.cap.isOpened():
                self.logger.info("Vision Engine: Camera Connected.")
                self.camera_available = True
                self.reconnect_attempts = 0
            else:
                self.logger.warning("Vision Engine: Failed to open camera.")
                self.camera_available = False
                self.reconnect_attempts += 1
        except Exception as e:
            self.logger.error(f"Camera Open Error: {e}")
            self.camera_available = False
            self.reconnect_attempts += 1

    def _get_placeholder_frame(self):
        # Create a black frame with text indicating no camera
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, "VISION OFFLINE", (150, 240), font, 1.5, (0, 0, 255), 3, cv2.LINE_AA)
        cv2.putText(frame, "No physical camera detected.", (150, 280), font, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
        return frame

    def detect(self) -> DetectionResult:
        if not self.is_initialized:
            return DetectionResult(False, 0.0, 0, False, None)

        with self._lock:
            try:
                if not self.camera_available or self.cap is None:
                    # Provide a placeholder and simulate no detection
                    frame = self._get_placeholder_frame()
                    time.sleep(0.1) # Simulate camera delay so thread doesn't spin at 100% CPU
                    return DetectionResult(False, 0.0, 0, False, frame)

                ret, frame = self.cap.read()
                if not ret or frame is None:
                    # Attempt reconnection
                    self._open_camera()
                    return DetectionResult(False, 0.0, 0, False, self._get_placeholder_frame())

                # Process Frame
                results = self.model.predict(frame, conf=0.5, verbose=False)
                
                person_detected = False
                confidence = 0.0
                person_count = 0
                
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        cls = int(box.cls[0])
                        if cls == 0: # Person in COCO
                            person_detected = True
                            person_count += 1
                            confidence = max(confidence, float(box.conf[0]))
                            
                            # Draw BBox
                            b = box.xyxy[0]
                            cv2.rectangle(frame, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), (0, 255, 204), 2)

                return DetectionResult(person_detected, confidence, person_count, False, frame)

            except Exception as e:
                self.logger.error(f"Detection Loop Error: {e}")
                return DetectionResult(False, 0.0, 0, False, self._get_placeholder_frame())

    def close(self):
        with self._lock:
            if self.cap:
                self.cap.release()
            self.is_initialized = False
