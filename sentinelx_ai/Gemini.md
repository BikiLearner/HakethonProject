# 🤖 SentinelX AI V5 — Autonomous Industrial AI with RAG + Voice + Custom Systems

You are a **principal AI systems architect**.

Your task is to EXTEND SentinelX AI (existing multi-threaded industrial monitoring system) into a **self-configurable, voice-driven industrial intelligence platform**.

This is NOT a prototype. Build production-grade modular architecture.

---

# 🎯 CORE UPGRADE OBJECTIVE

Transform SentinelX into:

### 🧠 A SELF-LEARNING SYSTEM

* Accepts **Excel-based machine specifications**
* Converts them into **structured knowledge**
* Stores them in a **local RAG system**
* Adapts monitoring + reasoning dynamically

### 🤖 A VOICE-FIRST AI AGENT

* NO chat UI
* Fully conversational (listen + speak)
* Real-time system awareness

### 🌐 A DYNAMIC UI SYSTEM

* Modern robotic UI (square industrial robot face 🤖)
* Reacts visually + behaviorally to system state

---

# 🧱 UPDATED SYSTEM ARCHITECTURE

```
sentinelx_ai/
│
├── main.py  (existing - DO NOT MODIFY CORE LOGIC)
│
├── api/
│   └── server.py
│
├── rag/
│   ├── ingestion.py
│   ├── embedding_store.py
│   ├── retriever.py
│
├── robot/
│   ├── voice_engine.py
│   ├── stt_engine.py
│   ├── llm_engine.py
│   ├── conversation_loop.py
│   ├── state_interpreter.py
│
├── custom_system/
│   ├── excel_parser.py
│   ├── schema_builder.py
│
├── web_ui/
│   ├── index.html
│   ├── upload.html
│   ├── style.css
│   ├── app.js
│
├── docker/
│   └── Dockerfile
```

---

# 📊 EXCEL → CUSTOM SYSTEM PIPELINE (CRITICAL FEATURE)

## Upload Page:

Create a new UI page:

### `/upload`

* Accept `.xlsx`
* Show preview
* Button: **"Generate System"**

---

## Processing Pipeline:

### Step 1: Parse Excel

Use `pandas`

Expected flexible structure:

* Machine Name
* Sensors (Temp, Vibration, etc.)
* Thresholds
* Safety Rules
* Environment Data

---

### Step 2: Convert to Structured JSON

Example:

```
{
  "machine": "Hydraulic Press",
  "sensors": {
    "temperature": { "warning": 75, "critical": 90 },
    "vibration": { "warning": 2.0, "critical": 3.0 }
  }
}
```

---

### Step 3: RAG Storage (LOCAL ONLY)

Use:

* Embedding model:

  * sentence-transformers (offline)
* Vector DB:

  * FAISS (mandatory)

Store:

* Machine specs
* Rules
* Operational guidelines

---

### Step 4: Dynamic System Override

Your system must:

* Override default thresholds
* Override reasoning logic inputs
* Affect:

  * fusion_engine
  * reasoning_engine
  * robot speech

Fallback:

* If no custom system → use generic defaults

---

# 🧠 RAG QUERY USAGE

Whenever LLM generates response:

1. Retrieve relevant context from FAISS
2. Inject into prompt

Example:

```
Context:
Machine max temp = 85°C

User:
"What is current risk?"

LLM:
Uses both real-time data + retrieved context
```

---

# 🎤 FULL VOICE LOOP (NO UI CHAT)

## STT (Speech-to-Text)

Use:

* Vosk (offline) OR Whisper.cpp

## TTS (Text-to-Speech)

Use:

* Coqui TTS (preferred)
* fallback: pyttsx3

---

## Conversation Loop (CRITICAL)

Create continuous loop:

```
while True:
    listen → transcribe → process → respond → speak
```

Trigger conditions:

* User speech
* System anomaly
* State change

---

## Behavior Rules

* Interrupt speech if critical alert
* Debounce repeated alerts
* Maintain conversational memory (short-term)

---

# 🤖 ROBOT UI (MAJOR UPGRADE)

Replace circular face → **Square Industrial Robot**

## Design:

* Square metallic panel 🤖
* LED strip eyes (horizontal)
* Animated expressions:

  * Idle (soft blue)
  * Thinking (pulsing)
  * Warning (yellow flicker)
  * Critical (red flashing)

Add:

* Subtle mechanical animation
* Glow + reflection (glassmorphism)

---

# 🌐 UI PAGES

## 1. Home `/`

* Robot face (center)
* Status text
* Floating:

  * "Dashboard"
  * "Upload System"

---

## 2. Upload `/upload`

* File input
* Preview table
* Generate system button

---

# 🔗 API ENDPOINTS

```
GET /state
GET /risk
GET /speak
POST /upload_excel
GET /rag_query
```

---

# 🧠 LOCAL LLM

Use:

* Ollama (preferred)

  * mistral OR llama3

OR fallback:

* llama-cpp-python

---

## Prompt Structure

```
System:
You are an industrial safety AI.

Context:
[RAG retrieved data]

Live Data:
[temp, vibration, risk]

User Query:
...

Respond naturally.
```

---

# ⚡ PERFORMANCE RULES

* Async everywhere
* Non-blocking threads
* Cache embeddings
* Batch RAG queries
* Voice must not spam

---

# 🐳 DOCKER REQUIREMENTS

Include:

* Python 3.10+
* FAISS
* sentence-transformers
* vosk / whisper.cpp
* coqui-tts
* fastapi + uvicorn

Expose:

* 8000 (UI/API)
* 8501 (Streamlit)

---

# 📓 NOTEBOOK COMPATIBILITY

* Must run inside Jupyter
* Use `nest_asyncio`
* Serve UI via FastAPI

---

# 🚫 CONSTRAINTS

* ❌ No cloud APIs
* ❌ No React/Vue
* ❌ No breaking existing system_core
* ❌ No blocking loops

---

# ✅ FINAL OUTPUT REQUIREMENTS

Generate:

1. Full working code
2. Excel ingestion pipeline
3. RAG system
4. Voice loop
5. UI (robot + upload)
6. Docker setup

---

# 🎯 END GOAL

A **self-configurable industrial AI assistant** that:

* Learns from uploaded Excel
* Adapts monitoring dynamically
* Talks like a real assistant
* Reacts visually
* Works fully offline

This should feel like a **real industrial Jarvis**, not a demo.
