"""
SentinelX AI - Stable Entry Point (V4)
Lazy loading to preventprocess-level crashes on Python 3.14
"""
import streamlit as st
import time
import sys
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SentinelX")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logic.system_core import SystemCore
from ui.dashboard import Dashboard

@st.cache_resource
def get_system_core():
    """Create core once. Don't load models here."""
    return SystemCore()

def init_ui_state():
    """Initialize UI-specific state variables with safe defaults"""
    if "trigger_warning" not in st.session_state:
        st.session_state.trigger_warning = False
    if "trigger_critical" not in st.session_state:
        st.session_state.trigger_critical = False
    if "machine_load" not in st.session_state:
        st.session_state.machine_load = 0.5
    if "camera_id" not in st.session_state:
        st.session_state.camera_id = 0
    if "available_cameras" not in st.session_state:
        st.session_state.available_cameras = [0, 1, 2]

def main():
    try:
        # 1. UI Setup
        init_ui_state()
        if "dashboard" not in st.session_state:
            st.session_state.dashboard = Dashboard()
        
        # 2. Get Core
        core = get_system_core()

        # 3. Start Threads (Safe/Lazy)
        if not core.state.is_running:
            with st.spinner("🔧 Calibrating Industrial Systems..."):
                core.start()
                time.sleep(1)
                st.rerun()

        # 4. Sync UI -> Core
        core.set_triggers(st.session_state.trigger_warning, st.session_state.trigger_critical)
        core.set_load(st.session_state.machine_load)
        
        # 5. Get Data
        snapshot = core.get_snapshot()
        
        # 5. Handle initial loading state
        if snapshot["machine_state"] is None:
            st.info("📡 Connecting to machine telemetry...")
            time.sleep(1)
            st.rerun()
            return

        # 6. Render
        st.session_state.dashboard.render_dashboard(
            machine_state=snapshot["machine_state"],
            detection_result=snapshot["detection_result"],
            fusion_result=snapshot["fusion_result"],
            decision=snapshot["decision"],
            fusion_history=snapshot["fusion_history"],
            last_frame=snapshot["last_frame"],
            core=core
        )

        # 7. Refresh
        time.sleep(1)
        st.rerun()

    except Exception as e:
        st.error(f"### 🛑 System Halted: {e}")
        if st.button("Restart Engine"):
            st.cache_resource.clear()
            st.rerun()

if __name__ == "__main__":
    main()
