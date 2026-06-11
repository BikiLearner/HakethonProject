import cv2
import time
import threading
import logging
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SentinelX.Standalone")

app = FastAPI(title="SentinelX AI Standalone Core")

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for the video feed
last_frame = None
lock = threading.Lock()

def vision_worker():
    """Background worker for camera capture and YOLO detection."""
    global last_frame
    
    logger.info("Initializing Vision Engine...")
    
    # Try to load YOLO
    model = None
    try:
        from ultralytics import YOLO
        # Look for model in current dir or parent sentinelx_ai if exists
        model_path = "yolov8n.pt"
        if not os.path.exists(model_path):
            alt_path = os.path.join("..", "sentinelx_ai", "yolov8n.pt")
            if os.path.exists(alt_path):
                model_path = alt_path
        
        model = YOLO(model_path)
        logger.info(f"YOLOv8 loaded from {model_path}")
    except Exception as e:
        logger.warning(f"YOLOv8 could not be loaded (Simulation Mode): {e}")

    # Try to open the camera (using CAP_DSHOW for better Windows compatibility)
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        logger.warning("CAP_DSHOW failed. Trying default capture...")
        cap = cv2.VideoCapture(0)
    
    if cap.isOpened():
        logger.info("✅ CAMERA CONNECTED: Hardware access granted.")
        # Set resolution for better performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    else:
        logger.error("❌ COULD NOT OPEN CAMERA. Please check privacy settings or if another app is using it.")
        cap = None

    while True:
        frame = None
        if cap:
            ret, frame = cap.read()
            if not ret:
                logger.warning("Failed to grab frame. Reconnecting...")
                cap.release()
                time.sleep(1)
                cap = cv2.VideoCapture(0)
                continue
        
        # If no camera, create a high-tech placeholder
        if frame is None:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "SIMULATED FEED", (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            time.sleep(0.05)
        else:
            # Run YOLO if available
            if model:
                results = model.predict(frame, conf=0.5, verbose=False)
                for r in results:
                    for box in r.boxes:
                        if int(box.cls[0]) == 0: # Person
                            b = box.xyxy[0]
                            # Draw Red Box for Safety Issue
                            cv2.rectangle(frame, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), (49, 49, 255), 2)
                            cv2.putText(frame, "SAFETY ISSUE", (int(b[0]), int(b[1])-10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (49, 49, 255), 2)

        # Update global frame
        with lock:
            last_frame = frame.copy()
        
        time.sleep(0.03)

@app.get("/video_feed")
async def video_feed():
    """Endpoint for the MJPEG stream."""
    def generate():
        while True:
            with lock:
                if last_frame is None:
                    continue
                ret, buffer = cv2.imencode('.jpg', last_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if not ret:
                    continue
                frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.05)

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/api/status")
async def get_status():
    """Simple status endpoint for the frontend to check backend health."""
    return {"status": "online", "vision_active": True}

# Serve the current directory (llm_demo) as static files
# This makes main.py the host for the whole app
app.mount("/", StaticFiles(directory=".", html=True), name="static")

if __name__ == "__main__":
    # Start the vision thread
    t = threading.Thread(target=vision_worker, daemon=True)
    t.start()
    
    logger.info("Starting Standalone Server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
