from fastapi import FastAPI, Response, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import cv2
import logging
from pydantic import BaseModel

app = FastAPI(title="SentinelX AI Bridge")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_system_core = None

def set_core(core):
    global _system_core
    _system_core = core

class ChatRequest(BaseModel):
    message: str

class LogRequest(BaseModel):
    level: str
    message: str

@app.post("/log")
async def receive_client_log(request: LogRequest):
    logger = logging.getLogger("SentinelX.WebUI")
    if request.level.upper() == "ERROR":
        logger.error(f"[CLIENT] {request.message}")
    elif request.level.upper() == "WARN":
        logger.warning(f"[CLIENT] {request.message}")
    else:
        logger.info(f"[CLIENT] {request.message}")
    return {"status": "ok"}

@app.get("/state")
async def get_state():
    if _system_core:
        snapshot = _system_core.get_snapshot()
        return {
            "machine_state": snapshot["machine_state"].__dict__ if snapshot["machine_state"] else None,
            "risk_score": snapshot["fusion_result"].risk_score if snapshot["fusion_result"] else 0.0,
            "status": snapshot["decision"].status if snapshot["decision"] else "INITIALIZING",
            "person_detected": snapshot["detection_result"].person_detected if snapshot["detection_result"] else False,
            "anomaly_score": snapshot["decision"].anomaly_score if snapshot["decision"] else 0.0,
            "wear_level": snapshot.get("wear_level", 0.0),
            "load": snapshot.get("load", 0.5),
            "recommendation": snapshot["decision"].recommended_action if snapshot["decision"] else "Analyzing...",
            "issue": snapshot["decision"].predicted_issue if snapshot["decision"] else "None",
            "reason": snapshot["decision"].reason if snapshot["decision"] else "Steady operation"
        }
    return {"error": "Core not initialized"}

@app.get("/video_feed")
async def video_feed():
    def generate():
        while True:
            if _system_core:
                snapshot = _system_core.get_snapshot()
                frame = snapshot.get("last_frame")
                if frame is not None:
                    frame_small = cv2.resize(frame, (640, 480))
                    ret, buffer = cv2.imencode('.jpg', frame_small, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    if ret:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            import time
            time.sleep(0.05)
    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/history")
async def get_history():
    if _system_core:
        snapshot = _system_core.get_snapshot()
        history = snapshot["fusion_history"]
        return [f.to_dict() for f in history[-50:]]
    return []

@app.post("/control/load")
async def set_load(value: float):
    if _system_core:
        _system_core.set_load(value)
        return {"status": "ok"}
    return {"error": "Core not initialized"}

@app.post("/control/trigger")
async def trigger(type: str):
    if _system_core:
        if type == "critical":
            _system_core.set_triggers(False, True)
        elif type == "warning":
            _system_core.set_triggers(True, False)
        elif type == "reset":
            _system_core.set_triggers(False, False)
            _system_core.simulator.reset()
        return {"status": "ok"}
    return {"error": "Core not initialized"}

@app.get("/speak")
async def get_speak():
    logger = logging.getLogger("SentinelX.API")
    if _system_core:
        from robot.llm_engine import LLMEngine
        llm = LLMEngine()
        snapshot = _system_core.get_snapshot()
        state_data = {
            "temp": snapshot["machine_state"].temperature if snapshot["machine_state"] else 0,
            "vib": snapshot["machine_state"].vibration if snapshot["machine_state"] else 0,
            "risk": snapshot["fusion_result"].risk_score if snapshot["fusion_result"] else 0,
            "status": snapshot["decision"].status if snapshot["decision"] else "UNKNOWN"
        }
        speech_text = llm.generate_speech(state_data)
        return {"text": speech_text}
    return {"error": "Core not initialized"}

@app.post("/chat")
async def chat(request: ChatRequest):
    logger = logging.getLogger("SentinelX.API")
    if _system_core:
        from robot.llm_engine import LLMEngine
        llm = LLMEngine()
        snapshot = _system_core.get_snapshot()
        state_data = {
            "temp": snapshot["machine_state"].temperature if snapshot["machine_state"] else 0,
            "vib": snapshot["machine_state"].vibration if snapshot["machine_state"] else 0,
            "risk": snapshot["fusion_result"].risk_score if snapshot["fusion_result"] else 0,
            "status": snapshot["decision"].status if snapshot["decision"] else "UNKNOWN"
        }
        response_text = llm.generate_speech(state_data, user_query=request.message)
        return {"text": response_text}
    return {"error": "Core not initialized"}

static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web_ui")
app.mount("/", StaticFiles(directory=static_path, html=True), name="web_ui")

import asyncio

def custom_exception_handler(loop, context):
    exception = context.get('exception')
    if isinstance(exception, ConnectionResetError) and exception.winerror == 10054:
        return
    loop.default_exception_handler(context)

def run_server(core, host="0.0.0.0", port=8000):
    set_core(core)
    
    if os.name == 'nt':
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except AttributeError:
            pass

    try:
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(custom_exception_handler)
    except RuntimeError:
        pass

    config = uvicorn.Config(app, host=host, port=port, log_level="error")
    server = uvicorn.Server(config)
    server.run()
