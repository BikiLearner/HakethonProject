import asyncio
import threading
import queue
import logging
import edge_tts
import os
from playsound import playsound

logger = logging.getLogger("SentinelX.TTS")


class TTSEngine:
    def __init__(self):
        self.queue = queue.Queue()
        self.is_speaking = False   # 🔥 THIS FIXES YOUR ERROR

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    async def _generate_audio(self, text, filename):
        communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
        await communicate.save(filename)

    def _run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while True:
            try:
                text = self.queue.get()

                self.is_speaking = True   # 🔊 START

                print("🔊 SPEAKING:", text)

                filename = "temp_voice.mp3"

                loop.run_until_complete(self._generate_audio(text, filename))

                playsound(filename)

                if os.path.exists(filename):
                    os.remove(filename)

                self.is_speaking = False   # 🔇 END

            except Exception as e:
                self.is_speaking = False   # 🔥 FAIL SAFE
                logger.error(f"TTS error: {e}")

    def speak(self, text, interrupt=False):
        if not text:
            return

        if interrupt:
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except:
                    break

        self.queue.put(text)