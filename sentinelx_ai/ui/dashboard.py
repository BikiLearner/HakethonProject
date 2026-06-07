"""
Dashboard Module - Industry-Grade Monitoring UI
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from utils.config import STATUS_COLORS, STATUS_EMOJI


class Dashboard:
    """Professional Streamlit dashboard for SentinelX AI"""
    
    def __init__(self):
        """Initialize dashboard"""
        self._setup_page()
    
    def _setup_page(self):
        """Configure Streamlit page"""
        st.set_page_config(
            page_title="SentinelX AI | Industrial Monitoring",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="collapsed",
        )
        
        # Dark theme styling with industrial accents
        st.markdown("""
        <style>
            .main {
                background-color: #0d1117;
            }
            .stMetric {
                background-color: #161b22;
                padding: 15px;
                border-radius: 10px;
                border-left: 5px solid #30363d;
                transition: transform 0.2s;
            }
            .stMetric:hover {
                transform: translateY(-2px);
                border-left-color: #58a6ff;
            }
        </style>
        """, unsafe_allow_html=True)
    
    def render_dashboard(self, machine_state, detection_result, fusion_result, 
                        decision, fusion_history, last_frame, core):
        """Main dashboard rendering"""
        # HEADER
        col1, col2 = st.columns([3, 1])
        with col1:
            st.title("🤖 SentinelX AI : Industrial Overhaul")
            st.caption("Event-Driven | Digital Twin | ML-Anomaly Detection")
        with col2:
            st.metric("System Uptime", datetime.now().strftime("%H:%M:%S"), "ACTIVE")
        
        st.markdown("---")
        
        # TOP ROW: STATUS & VIDEO
        col_stat, col_vid = st.columns([1, 2])
        
        with col_stat:
            self._render_status_indicator(decision)
            
            # PPE Status Indicator
            ppe_ok = getattr(detection_result, 'ppe_detected', False) if detection_result else False
            person_detected = getattr(detection_result, 'person_detected', False) if detection_result else False
            
            if person_detected:
                if ppe_ok:
                    st.success("👷 PPE Detected: OK")
                else:
                    st.error("⚠️ NO PPE DETECTED!")

            st.markdown("### 🚨 Safety Alerts")
            if decision:
                if decision.status == "DANGER":
                    st.error(f"**ISSUE:** {decision.predicted_issue}\n\n**ACTION:** {decision.recommended_action}")
                elif decision.status == "CAUTION":
                    st.warning(f"**ISSUE:** {decision.predicted_issue}\n\n**ACTION:** {decision.recommended_action}")
                else:
                    st.success(f"**STATUS:** {decision.recommended_action}")
                st.info(f"**REASON:** {decision.reason}")
            else:
                st.info("System is analyzing current state...")

        with col_vid:
            try:
                if last_frame is not None and last_frame.size > 0:
                    st.image(last_frame, channels="BGR", width="stretch", caption="Geofenced Safety Zone Monitoring")
                else:
                    st.warning("📷 Initializing Vision Engine...")
            except Exception as e:
                st.error(f"Media Error: {e}")
                st.warning("Ensure webcam is connected and not used by another app.")

        st.markdown("---")
        
        # MIDDLE ROW: CORE METRICS
        st.subheader("📊 Operational Telemetry")
        m1, m2, m3, m4, m5 = st.columns(5)
        
        snapshot = core.get_snapshot()
        
        with m1:
            st.metric("🌡️ Temp", f"{machine_state.temperature:.1f}°C", 
                     f"{machine_state.temperature - 60:.1f}", delta_color="inverse")
        with m2:
            st.metric("📢 Vibration", f"{machine_state.vibration:.2f}", 
                     f"{machine_state.vibration - 0.5:.2f}", delta_color="inverse")
        with m3:
            st.metric("⚙️ RPM", f"{machine_state.rpm:.0f}", 
                     f"{machine_state.rpm - 1500:.0f}")
        with m4:
            anomaly_score = getattr(decision, 'anomaly_score', 0.0)
            st.metric("🧠 ML Anomaly", f"{anomaly_score*100:.1f}%", 
                     "STABLE" if anomaly_score < 0.4 else "UNSTABLE", 
                     delta_color="inverse")
        with m5:
            wear = snapshot.get("wear_level", 0.0)
            st.metric("🛠️ Component Wear", f"{wear*100:.2f}%", 
                     f"+{wear*10:.4f}%")

        st.markdown("---")
        
        # BOTTOM ROW: CHARTS & CONTROLS
        col_chart, col_ctrl = st.columns([2, 1])
        
        with col_chart:
            self._render_charts(fusion_history)
            
        with col_ctrl:
            st.subheader("🎮 Control Center")
            
            # Camera Selection
            available_indices = st.session_state.available_cameras
            if not available_indices:
                st.error("No cameras detected!")
                if st.button("🔍 Rescan Cameras"):
                    st.session_state.available_cameras = core.probe_cameras()
                    st.rerun()
            else:
                cam_labels = {idx: f"Camera {idx}" for idx in available_indices}
                # Add friendly names for 0 and 1
                if 0 in cam_labels: cam_labels[0] = "Laptop / Default (0)"
                if 1 in cam_labels: cam_labels[1] = "External / USB (1)"
                
                selected_label = st.selectbox(
                    "Select Camera Input", 
                    list(cam_labels.values()), 
                    index=available_indices.index(st.session_state.camera_id) if st.session_state.camera_id in available_indices else 0
                )
                
                # Reverse mapping to get ID
                inv_labels = {v: k for k, v in cam_labels.items()}
                new_cam_id = inv_labels[selected_label]
                
                if new_cam_id != st.session_state.camera_id:
                    success = core.change_camera(new_cam_id)
                    if success:
                        st.session_state.camera_id = new_cam_id
                        st.success(f"Switched to {selected_label}")
                    else:
                        st.error(f"Failed to open {selected_label}")
            
            if st.button("🔍 Refresh Device List", width="stretch"):
                st.session_state.available_cameras = core.probe_cameras()
                st.rerun()

            # Machine Load Slider
            current_load = snapshot.get("load", 0.5)
            new_load = st.slider("Machine Load Factor", 0.0, 1.0, float(current_load))
            st.session_state.machine_load = new_load
            
            st.markdown("### Override Triggers")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🚨 TRIGGER CRITICAL", width="stretch", type="primary"):
                    st.session_state.trigger_critical = True
                    st.session_state.trigger_warning = False
            with c2:
                if st.button("⚠️ TRIGGER WARNING", width="stretch"):
                    st.session_state.trigger_warning = True
                    st.session_state.trigger_critical = False
            
            if st.button("🔄 RESET SYSTEM", width="stretch"):
                st.session_state.trigger_critical = False
                st.session_state.trigger_warning = False
                st.session_state.machine_load = 0.5
                core.simulator.reset()

        st.markdown("---")
        
        # TECHNICAL DETAILS
        with st.expander("🛠️ Advanced Diagnostics (Digital Twin State)"):
            st.json({
                "Engine": "Async-Event-Driven-V3-Threading",
                "ML_Model": "Isolation Forest (scikit-learn)",
                "Vision_Model": "YOLOv8-Nano (Geofenced)",
                "System_Snapshot": {
                    "Wear": f"{snapshot.get('wear_level'):.6f}",
                    "Load": f"{snapshot.get('load'):.2f}",
                    "Last_Sync": f"{snapshot.get('last_update'):.2f}"
                }
            })

    def _render_status_indicator(self, decision):
        """Render large status indicator"""
        if decision is None:
            status = "INITIALIZING"
            color, emoji, bg = "#808080", "⏳", "rgba(128, 128, 128, 0.1)"
            confidence = 0.0
        else:
            status = decision.status
            confidence = decision.confidence
            if status == "SAFE":
                color, emoji, bg = "#00ff00", "✅", "rgba(0, 255, 0, 0.1)"
            elif status == "CAUTION":
                color, emoji, bg = "#ffa500", "⚠️", "rgba(255, 165, 0, 0.1)"
            else:
                color, emoji, bg = "#ff0000", "🚨", "rgba(255, 0, 0, 0.1)"
        
        html = f"""
        <div style="background-color: {bg}; border: 2px solid {color}; border-radius: 10px; padding: 20px; text-align: center;">
            <h1 style="color: {color}; margin: 0;">{emoji} {status}</h1>
            <p style="margin: 5px 0;">Confidence: {confidence*100:.1f}%</p>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)

    def _render_charts(self, fusion_history):
        """Render telemetry charts"""
        if not fusion_history or len(fusion_history) < 2:
            st.info("Waiting for data stream...")
            return
            
        df = pd.DataFrame([
            {
                "Time": datetime.fromtimestamp(f.timestamp).strftime("%H:%M:%S"),
                "Temperature": f.temperature,
                "Vibration": f.vibration * 10,
                "Risk (%)": f.risk_score * 100,
            }
            for f in fusion_history[-50:]
        ])
        
        st.line_chart(df.set_index("Time"), width="stretch")
