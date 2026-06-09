import cv2
import logging
import threading
import time
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
        try:
            self.logger.info(f"Vision Engine: Opening Camera {self.config['camera_id']}...")
            if self.cap is not None:
                self.cap.release()
            self.cap = cv2.VideoCapture(self.config["camera_id"])
            if self.cap.isOpened():
                self.logger.info("Vision Engine: Camera Connected.")
            else:
                self.logger.warning("Vision Engine: Failed to open camera.")
        except Exception as e:
            self.logger.error(f"Camera Open Error: {e}")

    def detect(self) -> DetectionResult:
        if not self.is_initialized or self.cap is None:
            return DetectionResult(False, 0.0, 0, False, None)

        with self._lock:
            try:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    # Attempt one-time reconnection
                    self._open_camera()
                    return DetectionResult(False, 0.0, 0, False, None)

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
                return DetectionResult(False, 0.0, 0, False, None)

    def close(self):
        with self._lock:
            if self.cap:
                self.cap.release()
            self.is_initialized = False
