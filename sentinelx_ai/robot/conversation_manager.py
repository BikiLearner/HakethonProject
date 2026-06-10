import logging
import queue
import threading
import time

from robot.llm_engine import LLMEngine
from robot.stt_engine import STTEngine
from robot.tts_engine import TTSEngine

logger = logging.getLogger("SentinelX.Converse")


class ConversationManager:
    def __init__(self, core):
        self.core = core

        self.mic_queue = queue.Queue()

        self.llm = LLMEngine()
        self.stt = STTEngine(self.mic_queue)
        self.tts = TTSEngine()
        self.core.tts_engine = self.tts   # 🔥 ADD THIS

        self.last_state = None
        self.last_spoken_time = 0

        self.running = False
        self.thread = threading.Thread(target=self._loop, daemon=True)

    def start(self):
        self.running = True
        self.thread.start()
        logger.info("🧠 Conversation Manager Started")

    def _handle_user(self, query, snapshot):
        logger.info(f"USER ASKED: {query}")

        query = query.lower()

        # 🔥 HARD CODED INTENTS (FOR DEMO)
        if "temperature" in query:
            response = f"Current temperature is {snapshot['machine_state'].temperature:.1f} degrees."

        elif "vibration" in query:
            response = f"Vibration level is {snapshot['machine_state'].vibration:.2f}."

        elif "status" in query or "health" in query:
            response = f"System status is {snapshot['decision'].status}."

        elif "risk" in query:
            response = f"Risk level is {snapshot['fusion_result'].risk_score:.2f}."

        elif "shutdown" in query:
            response = "System recommends shutdown due to safety concerns."

        elif "hello" in query or "hi" in query:
            response = "Hello, I am Sentinel X. System is running smoothly."

        else:
            # fallback to LLM (optional)
            state = self._format(snapshot)
            response = self.llm.generate_speech(state, user_query=query)

        # ✅ store for UI
        self.core.set_ai_response(response)

        # ✅ speak
        self.tts.speak(response, interrupt=True)


    def _speak_state(self, snapshot, interrupt=False):
        state = self._format(snapshot)

        msg = self.llm.generate_speech(state)

        # ✅ ADD THIS
        self.core.set_ai_response(msg)

        self.tts.speak(msg, interrupt=interrupt)

    def _loop(self):
        while self.running:
            snapshot = self.core.get_snapshot()
            now = time.time()

            # 1. USER INPUT
            try:
                query = self.mic_queue.get_nowait()
                self._handle_user(query, snapshot)
                continue
            except queue.Empty:
                pass

            # 2. STATE CHANGE SPEAK
            current_state = (
                snapshot["decision"].status if snapshot["decision"] else "NORMAL"
            )

            if current_state != self.last_state:
                self._speak_state(snapshot, interrupt=True)
                self.last_state = current_state
                self.last_spoken_time = now

            # 3. PERIODIC SPEAK
            elif now - self.last_spoken_time > 10:
                self._speak_state(snapshot)
                self.last_spoken_time = now

            time.sleep(0.3)


    def _speak_state(self, snapshot, interrupt=False):
        state = self._format(snapshot)

        msg = self.llm.generate_speech(state)

        self.tts.speak(msg, interrupt=interrupt)

    def _format(self, snapshot):
        return {
            "machine_name": "Machine",
            "temp": snapshot["machine_state"].temperature if snapshot["machine_state"] else 0,
            "vib": snapshot["machine_state"].vibration if snapshot["machine_state"] else 0,
            "risk": snapshot["fusion_result"].risk_score if snapshot["fusion_result"] else 0,
            "status": snapshot["decision"].status if snapshot["decision"] else "NORMAL"
        }

    def stop(self):
        self.running = False
        self.stt.stop()