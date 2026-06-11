import logging
import os
import threading
import requests
import random

# Silence warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from ctransformers import AutoModelForCausalLM
from rag.retriever import get_rag_context

logger = logging.getLogger("SentinelX.LLM")


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

        self.ollama_url = "http://localhost:11434/api/generate"
        self.ollama_active = False
        self.local_model = None

        # 🔍 Check Ollama
        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=1)
            if resp.status_code == 200:
                self.ollama_active = True
                logger.info("✅ Ollama detected")
        except:
            logger.warning("⚠️ Ollama not available")

        # 🧠 Load local model (ONLY ONCE)
        if not self.ollama_active:
            model_path = "models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
            if os.path.exists(model_path):
                try:
                    logger.info("🧠 Loading local model (TinyLlama)...")
                    self.local_model = AutoModelForCausalLM.from_pretrained(
                        model_path,
                        model_type="llama",
                        threads=4,
                        gpu_layers=0
                    )
                    logger.info("✅ Local model ready")
                except Exception as e:
                    logger.error(f"❌ Model load failed: {e}")
            else:
                logger.error("❌ No local model found")

        self._initialized = True

    def generate_speech(self, data: dict, user_query: str = None) -> str:
        temp = data.get("temp", 0)
        vib = data.get("vib", 0)
        risk = data.get("risk", 0)
        status = data.get("status", "NORMAL")
        machine_name = data.get("machine_name", "Machine")

        # 🔎 Get RAG context
        query_for_rag = user_query if user_query else f"{machine_name} safety"
        rag_context = get_rag_context(query_for_rag)

        # 🎭 Random speaking style
        styles = [
            "Speak like a calm industrial assistant.",
            "Respond like a friendly technician.",
            "Be slightly conversational and natural.",
            "Keep tone professional but human."
        ]
        style = random.choice(styles)

        # 🧠 Build prompt
        prompt = f"""
You are SentinelX, an industrial AI assistant.

{style}

Machine: {machine_name}
Temperature: {temp:.1f}°C
Vibration: {vib:.2f}
Risk Level: {risk:.2f}
Status: {status}

Context:
{rag_context}

Rules:
- Speak like a human, not a robot
- Keep response under 12 words
- Do NOT repeat the same sentence
- If warning/danger → explain WHY
- Be clear and natural
"""

        if user_query:
            prompt += f"\nUser: {user_query}\nAnswer:"
        else:
            prompt += "\nGive a short system status update:"

        # 🟢 Try Ollama
        if self.ollama_active:
            try:
                payload = {
                    "model": "mistral:latest",
                    "prompt": prompt,
                    "stream": False
                }
                response = requests.post(self.ollama_url, json=payload, timeout=10)

                if response.status_code == 200:
                    text = response.json().get("response", "").strip()
                    if text:
                        return text
            except Exception as e:
                logger.warning(f"Ollama failed: {e}")

        # 🟡 Local fallback
        if self.local_model:
            try:
                output = self.local_model(
                    prompt,
                    max_new_tokens=40,
                    temperature=0.7,
                    top_p=0.9
                )
                return output.strip()
            except Exception as e:
                logger.error(f"Local inference error: {e}")

        # 🔴 Final fallback
        return fallback_response(temp, vib, status)
    

def fallback_response(temp, vib, status):
    openings = [
        "Everything looks stable right now.",
        "System is operating normally.",
        "No immediate concerns detected.",
        "All parameters seem within limits.",
        "System check complete, everything looks good."
    ]

    temp_lines = [
        f"Temperature is around {temp:.1f} degrees.",
        f"I'm seeing temperature near {temp:.1f}°C.",
        f"Thermal levels are stable at {temp:.1f} degrees."
    ]

    vib_lines = [
        f"Vibration is at {vib:.2f}, which is normal.",
        f"Vibration levels are steady around {vib:.2f}.",
        f"No unusual vibration detected, currently {vib:.2f}."
    ]

    endings = [
        "No action needed.",
        "You’re good to go.",
        "Everything is under control.",
        "Monitoring will continue.",
        "Nothing to worry about right now."
    ]

    return f"{random.choice(openings)} {random.choice(temp_lines)} {random.choice(vib_lines)} {random.choice(endings)}"