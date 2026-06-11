# SentinelX AI V5 - System Architecture Overview

This document provides a high-level overview of each key Python file in the SentinelX AI project, explaining its purpose and role within the system.

---

## 1. Core Application & Entry Point

### 📄 `main.py`
*   **Purpose:** The main entry point of the entire application.
*   **Functionality:**
    *   Initializes the system-wide logging configuration.
    *   Creates the central `SystemCore` object, which manages all the background logic threads.
    *   Initializes and starts the `ConversationManager`, which controls the AI's voice and listening capabilities.
    *   Launches the `FastAPI` web server (`api/server.py`) which serves the UI and data endpoints.

### 📄 `setup_and_run.py`
*   **Purpose:** A one-click script to set up and launch the entire application.
*   **Functionality:**
    *   Installs all Python dependencies from `requirements.txt`.
    *   Downloads and extracts the required voice model (`Vosk`) into the `models/` directory.
    *   Checks if an `Ollama` server is running and provides guidance.
    *   Starts `main.py` in a new terminal window.

---

## 2. AI & Conversation Logic (`robot/`)

This directory contains the "brain" and "personality" of the AI.

### 📄 `robot/conversation_manager.py`
*   **Purpose:** The central orchestrator for all voice interactions.
*   **Functionality:**
    *   Runs the main decision-making loop in a dedicated thread.
    *   Listens for transcribed text from the `STTEngine`.
    *   Provides frequent, periodic status updates (every 4 seconds).
    *   Decides when to speak and what to say based on system state and user input.
    *   Implements a debounce mechanism to prevent spamming the same message.

### 📄 `robot/stt_engine.py` (Speech-to-Text)
*   **Purpose:** To listen to the microphone and convert speech into text.
*   **Functionality:**
    *   Runs in a dedicated thread to continuously listen without blocking.
    *   Uses the `sounddevice` library to capture microphone audio.
    *   Uses the `Vosk` model to transcribe the audio into text.
    *   Puts the transcribed text into a queue for the `ConversationManager` to process.

### 📄 `robot/tts_engine.py` (Text-to-Speech)
*   **Purpose:** To convert text into audible speech.
*   **Functionality:**
    *   Uses the `pyttsx3` library for reliable, cross-platform voice synthesis.
    *   Manages a speaking queue to handle requests from the `ConversationManager`.
    *   Runs in a COM-initialized thread to ensure stability on Windows.

### 📄 `robot/llm_engine.py` (Large Language Model)
*   **Purpose:** The reasoning core of the AI.
*   **Functionality:**
    *   **Hybrid Intelligence:** Automatically tries to connect to a local `Ollama` server for high-quality responses. If `Ollama` is not found, it seamlessly falls back to using the built-in `TinyLlama` GGUF model.
    *   Generates human-friendly responses based on system data, RAG context, and user queries.
    *   Generates proactive status updates and critical alerts.

---

## 3. Dynamic Configuration & RAG (`custom_system/` & `rag/`)

### 📄 `custom_system/excel_parser.py`
*   **Purpose:** To read and interpret the `.xlsx` machine specification files.
*   **Functionality:**
    *   Uses the `pandas` library to open and read Excel files.
    *   Extracts sensor names, thresholds, rules, and other metadata.
    *   Saves the parsed configuration to `active_config.json`.

### 📄 `custom_system/config_manager.py`
*   **Purpose:** A singleton to provide the rest of the application with the current machine configuration.
*   **Functionality:**
    *   Loads `active_config.json` into memory.
    *   Provides methods for other modules (like `fusion_engine`) to get the correct, dynamic thresholds for sensors.

### 📄 `rag/embedding_store.py` & `rag/ingestion.py`
*   **Purpose:** The Retrieval-Augmented Generation (RAG) pipeline.
*   **Functionality:**
    *   `ingestion.py` takes the data from the Excel file and converts it into text chunks.
    *   `embedding_store.py` uses `sentence-transformers` to turn those chunks into vector embeddings and stores them in a `FAISS` index (`faiss_index.bin`). This allows for fast semantic searching.

### 📄 `rag/retriever.py`
*   **Purpose:** To query the RAG system.
*   **Functionality:**
    *   Provides a simple function that the `LLMEngine` can call to get relevant context from the FAISS index based on a user's query or the current system state.

---

## 4. Core Logic & Simulation (`logic/` & `simulator/`)

### 📄 `logic/system_core.py`
*   **Purpose:** The heart of the monitoring system.
*   **Functionality:**
    *   Orchestrates all background data processing threads.
    *   Aggregates data from the `MachineSimulator`, `FusionEngine`, and `ReasoningEngine`.
    *   Provides a `get_snapshot()` method for the `ConversationManager` and `API Server` to get the latest complete state of the system.

### 📄 `logic/fusion_engine.py`
*   **Purpose:** To fuse raw sensor data into a single, actionable risk score.
*   **Functionality:**
    *   Takes raw data (temperature, vibration) and assesses the risk level for each.
    *   Dynamically pulls its thresholds from the `ConfigManager`.
    *   Combines individual risks into a single, aggregated risk score.

### 📄 `logic/reasoning_engine.py`
*   **Purpose:** To make high-level decisions based on the fused data.
*   **Functionality:**
    *   Takes the fused data and risk score.
    *   Determines the overall system status (`NORMAL`, `CAUTION`, `DANGER`).
    *   Provides a recommended action (e.g., `MONITOR`, `SHUTDOWN`).

### 📄 `simulator/machine_simulator.py`
*   **Purpose:** To generate realistic, simulated machine data for testing.
*   **Functionality:**
    *   Runs in a thread and simulates fluctuating temperature and vibration data.
    *   Can be triggered to create "warning" or "critical" event scenarios.

---

## 5. Web Interface & API (`api/` & `web_ui/`)

### 📄 `api/server.py`
*   **Purpose:** A `FastAPI` server that acts as the bridge between the backend and the frontend UI.
*   **Functionality:**
    *   `/state`: Provides real-time JSON data of the entire system state.
    *   `/video_feed`: Streams the camera feed to the dashboard.
    *   `/upload_excel`: The endpoint that receives the `.xlsx` file from the UI and triggers the reconfiguration pipeline.

### 📄 `web_ui/` folder
*   **Purpose:** Contains all the frontend files (HTML, CSS, JavaScript).
*   **`robot.html`:** The main AI Core interface with the reactive robot face.
*   **`index.html`:** The Command Center dashboard with the vision feed and telemetry.
*   **`upload.html`:** The portal for uploading new machine configurations.
*   **`app.js`:** The core JavaScript that fetches data from the `/state` endpoint every 500ms and updates all the visual components in the UI.
*   **`style.css`:** Contains all the styling for the beautiful, industrial aesthetic.
