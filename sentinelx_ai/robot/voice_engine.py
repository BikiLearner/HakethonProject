import pyttsx3
import logging
import threading
import queue
import time
import pythoncom

logger = logging.getLogger("SentinelX.Voice")

class VoiceEngine:
    def __init__(self):
        self.speech_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.engine_ready = threading.Event()
        
        # Windows requires COM initialization for TTS in threads
        self.thread = threading.Thread(target=self._run_engine, daemon=True)
        self.thread.start()

    def _run_engine(self):
        """Dedicated thread for TTS playback to avoid blocking or driver hangs"""
        pythoncom.CoInitialize() # Crucial for Windows TTS
        
        try:
            logger.info("Starting High-Priority TTS Thread...")
            engine = pyttsx3.init()
            engine.setProperty('rate', 180)
            
            # Find a clear voice
            voices = engine.getProperty('voices')
            if len(voices) > 1:
                engine.setProperty('voice', voices[1].id) # Usually Zira/Female
            
            self.engine_ready.set()
            logger.info("TTS Subsystem ONLINE.")

            while not self.stop_event.is_set():
                try:
                    text = self.speech_queue.get(timeout=0.5)
                    logger.info(f"TTS EXEC: {text}")
                    
                    engine.say(text)
                    engine.runAndWait()
                    
                    self.speech_queue.task_done()
                    # Small cooldown to prevent engine lockup
                    time.sleep(0.1)
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"TTS Runtime Error: {e}")
                    time.sleep(1)
        finally:
            pythoncom.CoUninitialize()

    def speak(self, text, interrupt=False):
        if not text: return
        if not self.engine_ready.is_set():
            logger.warning("TTS not ready, dropping speech.")
            return
            
        if interrupt:
            while not self.speech_queue.empty():
                try: self.speech_queue.get_nowait()
                except: break
        
        self.speech_queue.put(text)
