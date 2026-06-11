import logging
import os
import queue
import threading
import json
import sounddevice as sd
import vosk

logger = logging.getLogger("SentinelX.STT")


class STTEngine:
    def __init__(self, output_queue: queue.Queue):
        self.output_queue = output_queue
        self.stop_event = threading.Event()

        model_path = "models/vosk-model-small-en-us-0.15"
        if not os.path.exists(model_path):
            logger.error("❌ Vosk model not found.")
            self.model = None
            return

        self.model = vosk.Model(model_path)

        # 🔥 FORCE CORRECT SAMPLE RATE
        self.samplerate = 16000

        self.audio_queue = queue.Queue()

        # 🎯 Select correct mic (IMPORTANT)
        self.device = self._find_input_device()

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _find_input_device(self):
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                logger.info(f"🎤 Found input device {i}: {dev['name']}")
        return None  # default device

    def _audio_callback(self, indata, frames, time, status):
        if status:
            logger.warning(status)

        # 🔥 Debug: confirm audio is coming
        print("🎤 Audio chunk received")

        self.audio_queue.put(bytes(indata))

    def _run(self):
        try:
            recognizer = vosk.KaldiRecognizer(self.model, self.samplerate)

            with sd.RawInputStream(
                samplerate=self.samplerate,
                blocksize=8000,
                dtype='int16',
                channels=1,
                callback=self._audio_callback,
                device=self.device
            ):
                logger.info("🎤 STT Engine started (speak now)")

                while not self.stop_event.is_set():
                    data = self.audio_queue.get()

                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text = result.get("text", "").strip()

                        if text:
                            print("🧠 FINAL TEXT:", text)
                            self.output_queue.put(text)
                    else:
                        partial = json.loads(recognizer.PartialResult()).get("partial", "")
                        if partial:
                            print("...partial:", partial)

        except Exception as e:
            logger.error(f"❌ STT crashed: {e}")

    def stop(self):
        self.stop_event.set()