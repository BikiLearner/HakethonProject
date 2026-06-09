import logging
import os
import threading
from ctransformers import AutoModelForCausalLM

class LLMEngine:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(LLMEngine, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.logger = logging.getLogger("SentinelX.LLM")
        self.model_path = "models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
        self.llm = None
        self._load_model()
        self._initialized = True

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.logger.info(f"Loading LLM from {self.model_path} (Singleton)...")
                self.llm = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    model_type="llama",
                    gpu_layers=0
                )
                self.logger.info("LLM Loaded successfully.")
            except Exception as e:
                self.logger.error(f"Failed to load LLM: {e}")
        else:
            self.logger.warning("LLM model file not found.")

    def generate_speech(self, data: dict, user_query: str = None) -> str:
        temp = data.get("temp", 0)
        vib = data.get("vib", 0)
        risk = data.get("risk", 0)
        status = data.get("status", "NORMAL")
        
        # 1. DETERMINISTIC SYSTEM ALERTS (Zero Hallucination)
        # If there is no user query, we MUST use strict rules for safety and accuracy.
        if not user_query:
            if status == "DANGER" or risk > 0.7:
                return f"Critical Alert. Machine state is Danger. Temperature has reached {temp:.1f} degrees Celsius, with severe vibration levels. Immediate action required."
            elif status == "CAUTION" or risk > 0.4:
                return f"Caution. Machine parameters are rising. Temperature is currently {temp:.1f} degrees Celsius. Please monitor the situation closely."
            else:
                return f"System is operating normally. Temperature is stable at {temp:.1f} degrees Celsius. No hazards detected."

        # 2. LLM CHAT (For direct user questions)
        prompt = (
            f"LATEST SENSOR DATA: Status is {status}. Temperature is {temp:.1f}C. Vibration is {vib:.2f}. Risk Score is {risk*100:.0f}%.\n"
            f"USER QUESTION: {user_query}\n"
            "INSTRUCTION: You are SentinelX, an industrial safety AI. Answer the user's question accurately using ONLY the sensor data provided above. Keep it very short."
        )

        if self.llm:
            try:
                full_prompt = f"<|system|>\nYou are SentinelX. Always tell the truth using the sensor data provided. Keep answers under 2 sentences.</s>\n<|user|>\n{prompt}</s>\n<|assistant|>\n"
                response = self.llm(full_prompt, max_new_tokens=50, stop=["</s>"])
                return response.strip()
            except Exception as e:
                self.logger.error(f"Inference error: {e}")

        return "I am experiencing a neural link error, but my deterministic safety monitors are still active."
