import os
import json
import queue
import sounddevice as sd
import vosk
import logging
import threading
import time
from robot.llm_engine import LLMEngine
from robot.voice_engine import VoiceEngine
from custom_system.config_manager import ConfigManager

logger = logging.getLogger("SentinelX.Conversation")

class ConversationLoop:
    def __init__(self, core):
        self.core = core
        self.llm = LLMEngine()
        self.voice = VoiceEngine()
        self.cm = ConfigManager()
        
        model_path = "models/vosk-model-small-en-us-0.15"
        self.model = vosk.Model(model_path) if os.path.exists(model_path) else None
        
        self.is_running = False
        self.last_proactive = time.time()

    def start(self):
        if self.is_running or not self.model: return
        self.is_running = True
        
        # 1. Listen Thread (Using blocking read for higher reliability)
        threading.Thread(target=self._blocking_listen, daemon=True).start()
        
        # 2. Proactive Status Thread
        threading.Thread(target=self._status_broadcaster, daemon=True).start()
        
        logger.info("Conversation Loop Synchronized.")

    def _blocking_listen(self):
        """Robust listening loop using blocking reads instead of callbacks"""
        try:
            device_info = sd.query_devices(None, 'input')
            samplerate = int(device_info['default_samplerate'])
            
            # Force 16000Hz for Vosk stability if possible, otherwise use device default
            # Vosk works best at 16k
            rec = vosk.KaldiRecognizer(self.model, samplerate)
            
            with sd.RawInputStream(samplerate=samplerate, blocksize=8000, device=None, 
                                   dtype='int16', channels=1) as stream:
                
                logger.info(f"MICROPHONE ACTIVE: {device_info['name']}")
                
                while self.is_running:
                    data, overflowed = stream.read(4000)
                    if overflowed:
                        logger.debug("Audio buffer overflow")
                        
                    if rec.AcceptWaveform(bytes(data)):
                        res = json.loads(rec.Result())
                        text = res.get("text", "").strip()
                        if text:
                            logger.info(f"USER SAYS: {text}")
                            self._handle_input(text)
        except Exception as e:
            logger.error(f"Listen Loop Failure: {e}")

    def _handle_input(self, text):
        snapshot = self.core.get_snapshot()
        state = self._format_state(snapshot)
        
        self.core.llm_thinking = True
        try:
            response = self.llm.generate_speech(state, user_query=text)
            self.voice.speak(response)
        finally:
            self.core.llm_thinking = False

    def _status_broadcaster(self):
        """Ensures the robot speaks real-time updates frequently"""
        while self.is_running:
            try:
                now = time.time()
                snapshot = self.core.get_snapshot()
                status = snapshot["decision"].status if snapshot["decision"] else "NORMAL"
                
                # Immediate alert for danger
                if status == "DANGER":
                    state = self._format_state(snapshot)
                    msg = self.llm.generate_speech(state)
                    self.voice.speak(msg, interrupt=True)
                    self.last_proactive = now + 10 # Delay next status
                
                # Regular heartbeat (every 30s)
                elif now - self.last_proactive > 30:
                    state = self._format_state(snapshot)
                    msg = self.llm.generate_speech(state)
                    self.voice.speak(msg)
                    self.last_proactive = now
                    
            except: pass
            time.sleep(1)

    def _format_state(self, snapshot):
        return {
            "machine_name": self.cm.get_machine_name(),
            "temp": snapshot["machine_state"].temperature if snapshot["machine_state"] else 0,
            "vib": snapshot["machine_state"].vibration if snapshot["machine_state"] else 0,
            "risk": snapshot["fusion_result"].risk_score if snapshot["fusion_result"] else 0,
            "status": snapshot["decision"].status if snapshot["decision"] else "NORMAL"
        }

def start_conversation_loop(core):
    conv = ConversationLoop(core)
    conv.start()
    return conv
