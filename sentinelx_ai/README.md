# 🤖 SentinelX AI : Industrial Overhaul V4

**SentinelX AI** is an advanced, multi-modal industrial safety platform. It represents a paradigm shift from reactive monitoring to **proactive risk mitigation** by fusing real-time physics simulations with high-speed AI inference.

---

## 🚀 Quick Start (Copy & Run)

### 1. Environment Setup
We recommend using Python 3.10+ (Fully stabilized for Python 3.14).
```bash
# Clone the repository
git clone https://github.com/your-repo/sentinelx_ai.git
cd sentinelx_ai

# Install high-performance dependencies
pip install -r requirements.txt
```

### 2. Launch the Platform
```bash
# Start the asynchronous server and dashboard
python -m streamlit run main.py
```

---

## 🏗️ Technical Architecture: The "Threaded Core"

SentinelX AI uses a **Decoupled Asynchronous Architecture**. This design pattern is critical for industrial applications where a UI hang could mask a critical safety alert.

### 📁 Exhaustive File Breakdown

#### **1. `main.py` | The Application Orchestrator**
- **Lazy Loading Logic:** On Python 3.14, heavy binary loads (Torch/OpenCV) can crash the Streamlit handshake. `main.py` solves this by starting the UI first and loading AI models in the background.
- **State Serialization:** Efficiently bridges the gap between the stateless Streamlit UI and the stateful threaded backend using `@st.cache_resource`.

#### **2. `logic/system_core.py` | Multi-Threaded Engine**
The heart of the system. It orchestrates three high-frequency parallel threads:
- **Telemetry Thread (10Hz):** Executes the physics engine equations.
- **Vision Thread (10 FPS):** Manages the camera buffer and YOLOv8 inference.
- **Reasoning Thread (2Hz):** Runs the ML Anomaly Detection and Bayesian Fusion.
- **Safety Interlocks:** Uses `threading.Lock()` to prevent race conditions during sensor data fusion.

#### **3. `simulator/machine_simulator.py` | Physics-Coupled Digital Twin**
This is not a random number generator. It is a **Digital Twin** that follows physical laws:
- **Thermal Dynamics:** Uses **Newton's Law of Cooling**: `dT/dt = k(T_env - T) + Q_heat`.
- **Kinetic Coupling:** Vibration is calculated as a quadratic function of RPM, further amplified by the `Wear Level`.
- **Interactive Load:** The `Machine Load Factor` (0.0 - 1.0) directly scales the `Q_heat` constant, allowing you to see the real-time thermal lag of a heavy motor.

#### **4. `logic/reasoning_engine.py` | ML Anomaly Detection**
- **Algorithm:** **Isolation Forest**. This unsupervised ML model identifies "outliers" in high-dimensional telemetry space.
- **Adaptive Learning:** The engine constantly buffers normal operating data. If vibration spikes *relative to the current RPM and Temp*, the ML flags it even if it's below the "hard" safety limit.
- **Decision Logic:** Merges ML scores with 7 predefined industrial safety interlocks.

#### **5. `logic/fusion_engine.py` | Bayesian Data Fusion**
- **Probabilistic Risk:** Calculates risk using a weighted approach:
    - **Thermal (35%)** + **Mechanical (25%)** + **Trend (25%)** + **Kinetic (15%)**.
- **Contextual Awareness:** Person detection doesn't just add to the score—it acts as a **Non-Linear Multiplier**. A failing machine is 10x more dangerous when a human is in the impact zone.

#### **6. `vision/vision_detector.py` | Advanced Computer Vision**
- **Inference Engine:** YOLOv8-Nano optimized for CPU/Edge-GPU execution.
- **Polygon Geofencing:** Implements `cv2.pointPolygonTest`. You can define custom hazardous zones where any intrusion triggers an immediate `DANGER` state.
- **PPE Heuristic:** A custom secondary classifier. It crops the detected person's head and uses **HSV Color Histograms** to identify Safety Helmets (detecting specific frequencies of Yellow, Orange, and White).

#### **7. `ui/dashboard.py` | Industrial Command Center**
- **Telemetry Scopes:** Real-time Pandas-backed charts with a 50-point rolling window.
- **Diagnostic Panel:** Provides deep-dive JSON snapshots of the "Machine Internal State" (Wear level, load factor, thermal trend).

---

## 🧠 Intelligence Deep-Dive

### **The "Safe-Mode" Connection**
If your hardware fails or the webcam is disconnected, the system activates **Safe-Mode**. 
- It generates a "VISION OFFLINE" placeholder.
- It switches the Reasoning Engine to "Sensor-Only" mode.
- **Result:** The server never crashes, ensuring continuous monitoring of machine metrics even if the "eyes" go dark.

### **PPE Detection Methodology**
1. **Detect Person:** YOLOv8 finds the bounding box.
2. **Isolate Head:** The system crops the top 25% of the box.
3. **HSV Filtering:** It applies a mask to find "Industrial Safety Colors".
4. **Frequency Threshold:** If >15% of the head area matches PPE colors, the worker is cleared.

---

## 🔧 Operational Thresholds

| Metric | Normal | Warning | Critical |
| :--- | :--- | :--- | :--- |
| **Temperature** | < 75°C | 75°C - 89°C | > 90°C |
| **Vibration** | < 1.0 | 1.0 - 2.9 | > 3.0 |
| **PPE Compliance**| Helmets Worn | N/A | Missing in Zone |
| **ML Anomaly** | < 40% | 40% - 70% | > 70% |

---

## 🛠️ Troubleshooting & FAQ

**Q: The terminal says "Camera index out of range"?**
- **A:** We've implemented a dynamic prober. Use the **"Refresh Device List"** button in the Control Center. It will automatically find your external webcam (usually Index 1 or 2).

**Q: The video is lagging?**
- **A:** We have intentionally capped the Vision engine at 10 FPS. This ensures the **ML Reasoning** and **Physics Simulation** have enough CPU cycles to remain accurate. In industrial safety, a 100ms delay is acceptable, but a system crash is not.

**Q: How do I reset the "Wear Level"?**
- **A:** Clicking **"RESET SYSTEM"** in the dashboard clears all permanent degradation and resets the Digital Twin to a "Brand New" state.

---

**Version:** 4.1.0 (Exhaustive Edition)  
**Status:** ✅ Production-Grade Stability  
**Engine:** Multi-Threaded Asynchronous V4  
**Frameworks:** Streamlit, YOLOv8, scikit-learn, OpenCV  

*Designed for the future of AI-integrated industrial safety.*
