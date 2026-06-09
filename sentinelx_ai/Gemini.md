# 🤖 BUILD INSTRUCTION PROMPT — SentinelX AI Voice Robot + Web UI (Notebook + Docker + Local LLM)

You are a senior AI systems engineer.

Your task is to EXTEND an existing industrial AI system called **SentinelX AI (Streamlit + Python backend)** into a **multi-interface system** with:

1. A **Home Screen (HTML/CSS/JS UI)**
2. A **Speaking Robot Assistant (with animated face)**
3. Integration with a **Local LLM (offline)**
4. Full support for **Docker + Notebook-only environments**
5. Seamless navigation to existing **Streamlit Dashboard**

---

# 🎯 CORE OBJECTIVE

Transform SentinelX from a Streamlit-only dashboard into a **dual-interface system**:

* 🧠 Backend → existing Python multi-threaded system (DO NOT BREAK)
* 🌐 Frontend → new HTML/CSS UI (runs in notebook environment)
* 🤖 Robot → voice + animated assistant connected to system state
* 🐳 Deployment → fully Dockerized and runnable inside Jupyter/Notebook

---

# 🧱 SYSTEM ARCHITECTURE (MANDATORY)

Follow this structure strictly:

```
sentinelx_ai/
│
├── main.py  (existing - DO NOT BREAK)
├── api/
│   └── server.py  <-- NEW (FastAPI bridge)
│
├── robot/
│   ├── voice_engine.py
│   ├── llm_engine.py
│   ├── state_interpreter.py
│
├── web_ui/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│
├── docker/
│   └── Dockerfile
```

---

# 🌐 FRONTEND REQUIREMENTS (HTML/CSS/JS ONLY)

Create a **modern industrial UI homepage**:

## Home Screen:

* Fullscreen dark UI
* Center → **Robot Face**
* Floating button → **"Open Dashboard"**

## Robot Face Design:

* Circular robotic face
* Two animated eyes

### Eye Colors:

* 🟢 Green → Normal
* 🟡 Yellow → Warning
* 🔴 Red → Critical

Use smooth CSS animations (glow/pulse effect).

---

# 🎤 ROBOT BEHAVIOR (CRITICAL)

The robot must:

### 1. Speak System Status

Examples:

* "System operating normally"
* "Warning: Temperature rising"
* "Critical alert: Machine overheating"

### 2. Speak ONLY on:

* State change
* Critical anomaly
* User interaction

### 3. Voice Engine:

Use:

* `pyttsx3` (offline TTS) OR
* Coqui TTS (preferred if possible)

---

# 🧠 LOCAL LLM INTEGRATION

Use a **local LLM (NO API CALLS)**:

Preferred:

* Ollama (Mistral / LLaMA3)
* OR llama-cpp-python

## LLM ROLE:

Convert raw system data → human speech

Example:

Input:

```
temperature=92, vibration=3.2, risk=0.87
```

Output:

```
"Critical condition detected. Temperature and vibration exceed safe limits."
```

---

# 🔗 BACKEND INTEGRATION (VERY IMPORTANT)

DO NOT modify core system threads.

Instead:

### Create FastAPI bridge:

`api/server.py`

Endpoints:

```
GET /state
→ returns system state JSON

GET /risk
→ returns risk level (normal/warning/critical)

GET /speak
→ returns LLM-generated speech text
```

This API pulls data from:

* system_core
* fusion_engine
* reasoning_engine

---

# 🔄 FRONTEND ↔ BACKEND FLOW

JS should:

1. Poll `/state` every 1 second
2. Update:

   * Eye color
   * Status text
3. If state changes:

   * Call `/speak`
   * Trigger robot voice

---

# 🧭 DASHBOARD BUTTON

Floating button behavior:

* On click → open Streamlit dashboard

Since notebook environment:
Use:

```
window.open("http://localhost:8501", "_blank")
```

---

# 🐳 DOCKER SUPPORT (MANDATORY)

Create Dockerfile:

* Python 3.10+
* Install:

  * streamlit
  * fastapi
  * uvicorn
  * pyttsx3
  * opencv
  * sklearn
* Expose:

  * 8501 (Streamlit)
  * 8000 (FastAPI)

Start BOTH:

* Streamlit
* FastAPI

---

# 📓 NOTEBOOK ENVIRONMENT SUPPORT

Since no direct UI:

* Serve HTML using FastAPI (`/`)
* OR use simple HTTP server

Ensure:

```
http://localhost:8000 → Home UI
http://localhost:8501 → Dashboard
```

---

# 🧠 STATE INTERPRETER LOGIC

Create mapping:

| Condition  | State    |
| ---------- | -------- |
| Risk < 0.4 | NORMAL   |
| 0.4–0.7    | WARNING  |
| > 0.7      | CRITICAL |

Return:

```
{
  "status": "CRITICAL",
  "message": "...",
  "color": "red"
}
```

---

# ⚡ PERFORMANCE RULES

* DO NOT block threads
* Use async API
* Use caching for LLM
* Voice must not spam (debounce events)

---

# 🎨 UI QUALITY (IMPORTANT)

* Smooth animations
* Glassmorphism panels
* Industrial futuristic look
* Responsive design

---

# 🚫 STRICT CONSTRAINTS

* ❌ No cloud APIs
* ❌ No breaking existing system
* ❌ No heavy frontend frameworks (React not allowed)
* ❌ Must run inside notebook + Docker

---

# ✅ FINAL OUTPUT

You must generate:

1. Full folder structure
2. All Python files
3. HTML/CSS/JS UI
4. Dockerfile
5. Run instructions

System must run with:

```
docker build -t sentinelx .
docker run -p 8000:8000 -p 8501:8501 sentinelx
```

---

# 🎯 END GOAL

A **Jarvis-like industrial assistant**:

* Sees system state
* Thinks using local LLM
* Speaks to user
* Visually reacts (robot face)
* Runs fully offline

---

Build this as production-quality code, not prototype.
