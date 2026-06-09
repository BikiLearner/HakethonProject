import time
from robot.voice_engine import VoiceEngine
from robot.llm_engine import LLMEngine

class StateInterpreter:
    def __init__(self, core):
        self.core = core
        self.voice = VoiceEngine()
        self.llm = LLMEngine()
        self.last_state = "NORMAL"
        self.last_speech_time = 0
        self.debounce_seconds = 10

    def step(self):
        snapshot = self.core.get_snapshot()
        if not snapshot["fusion_result"]:
            return

        risk = snapshot["fusion_result"].risk_score
        current_state = "NORMAL"
        if risk > 0.7:
            current_state = "CRITICAL"
        elif risk > 0.4:
            current_state = "WARNING"

        # Speak if state changed or if it's been a while in a bad state
        should_speak = False
        if current_state != self.last_state:
            should_speak = True
        elif current_state != "NORMAL" and (time.time() - self.last_speech_time > 60):
            # Remind every minute if still in danger
            should_speak = True

        if should_speak and (time.time() - self.last_speech_time > self.debounce_seconds):
            state_data = {
                "temp": snapshot["machine_state"].temperature if snapshot["machine_state"] else 0,
                "vib": snapshot["machine_state"].vibration if snapshot["machine_state"] else 0,
                "risk": risk,
                "status": current_state
            }
            speech_text = self.llm.generate_speech(state_data)
            self.voice.speak(speech_text)
            self.last_speech_time = time.time()
            self.last_state = current_state

def start_robot_loop(core):
    interpreter = StateInterpreter(core)
    def _loop():
        while True:
            try:
                interpreter.step()
            except Exception:
                pass
            time.sleep(2)
    
    import threading
    threading.Thread(target=_loop, daemon=True).start()
