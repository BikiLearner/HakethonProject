# 🔥 CRITICAL FIX PROMPT — SentinelX Voice + Mic + Real-Time Talking System

You are a **senior AI systems engineer specializing in real-time voice agents**.

Your task is to FIX and IMPROVE the existing SentinelX AI system.

⚠️ The system is already built, but has these CRITICAL issues:

---

# ❌ CURRENT PROBLEMS

1. 🎤 Microphone input is NOT working reliably
2. 🔊 AI does NOT speak on warnings/critical states
3. 🤖 UI updates but voice does NOT explain the issue
4. 🧠 No conversational ability:

   * User cannot ask: "What is current status?"
   * No real-time Q&A
5. ⚠️ System only reacts visually, NOT verbally

---

# 🎯 GOAL

Transform system into a **REAL-TIME VOICE-FIRST INDUSTRIAL AI**

It must behave like:

👉 A **talking industrial assistant**
👉 Always aware
👉 Always responding

---

# 🎤 MICROPHONE SYSTEM (MANDATORY FIX)

Implement a **continuous non-blocking STT loop**

### Requirements:

* Runs in a separate thread
* Uses:

  * Whisper.cpp (preferred) OR Vosk
* Must continuously listen:

```python
while True:
    listen → transcribe → push to queue
```

### CRITICAL:

* DO NOT wait for button click
* DO NOT block main thread
* Use queue to communicate with main loop

---

# 🧠 CONVERSATION ENGINE (MANDATORY)

Create a **central conversation controller**

### Behavior:

If user says:

* "What is current status?"
* "What is the problem?"
* "Is everything normal?"

👉 System MUST respond using:

* real-time system data
* RAG context (if available)

---

# 🔊 VOICE OUTPUT RULES (STRICT)

System MUST speak in ALL these cases:

---

## 1. STATE CHANGE (MANDATORY)

If system goes:

* NORMAL → WARNING
* WARNING → CRITICAL
* CRITICAL → NORMAL

👉 MUST speak:

Example:
"Warning detected. Temperature is rising above safe threshold."

---

## 2. PERIODIC STATUS (VERY IMPORTANT)

Every 10–15 seconds:

👉 Speak short update:

* "System operating normally"
* "System under moderate stress"
* "Critical condition persists"

---

## 3. ON USER QUERY

When user speaks → ALWAYS respond via voice

---

## 4. ON ANOMALY DETECTION

If ML anomaly > threshold:

👉 Speak reason:

* "Unusual vibration pattern detected relative to RPM"

---

# ⚠️ SPEECH DEBOUNCE (IMPORTANT)

Prevent spam:

* Do NOT repeat same message within 10 seconds
* Use last_spoken_state tracking

---

# 🔄 CENTRAL EVENT LOOP (CRITICAL)

Create unified loop:

```python
while True:
    check system state
    check mic input queue
    decide response
    send to TTS
```

---

# 🧠 RESPONSE GENERATION (IMPORTANT)

Use LLM ONLY for:

* Explanation
* Human-friendly reasoning

DO NOT use LLM for:

* raw state detection

---

### Example:

Input:

```
temp=92, vibration=3.2, risk=0.85
```

Output:

```
"Critical alert. Temperature and vibration are beyond safe limits. Immediate inspection required."
```

---

# 🔊 TTS ENGINE (FIX)

Use:

* Coqui TTS (preferred)
* fallback: pyttsx3

### MUST:

* Run async
* Interrupt speech if CRITICAL alert comes

---

# 🤖 UI SYNC (IMPORTANT)

UI and voice MUST be synchronized:

* If UI shows WARNING → voice must explain WHY
* If CRITICAL → voice must describe issue

---

# 🧪 DEBUG REQUIREMENTS

Add logs:

* mic input detected
* speech triggered
* reason generated

---

# 🚫 STRICT RULES

* ❌ No button-based voice trigger
* ❌ No silent state changes
* ❌ No blocking loops
* ❌ No missing speech on alerts

---

# ✅ FINAL RESULT

System should behave like:

🎤 User: "What is happening now?"

🤖 AI:
"System is currently in warning state. Temperature is approaching critical levels."

---

🎤 System auto:
"Critical alert. Vibration exceeds safe range."

---

🎯 This must feel like a REAL talking AI system, not UI-only.

Fix EVERYTHING required to achieve this.
