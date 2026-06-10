import os
import sys
import time
import logging
import traceback

# Fix for torchvision circular import bug in Python 3.14+
try:
    import torchvision
    import torchvision.transforms
except ImportError:
    pass

from logic.system_core import SystemCore
from api.server import run_server
from robot.conversation_manager import ConversationManager

# --- EXHAUSTIVE LOGGING CONFIGURATION ---
# This logs to BOTH the console and a specialized trace file
trace_logger = logging.getLogger("SentinelX.Trace")
trace_logger.setLevel(logging.DEBUG)

log_format = logging.Formatter('%(asctime)s.%(msecs)03d | %(name)-15s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S')

# Console Handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_format)
trace_logger.addHandler(console_handler)

# File Handler (Comprehensive Trace)
file_handler = logging.FileHandler("sentinelx_trace.log", mode='w')
file_handler.setFormatter(log_format)
trace_logger.addHandler(file_handler)

# Redirect root loggers to our trace format
logging.getLogger("SentinelX").addHandler(file_handler)
logging.getLogger("uvicorn").addHandler(file_handler)

def main():
    try:
        trace_logger.info("=== SentinelX TRACE START ===")
        trace_logger.info(f"OS: {sys.platform} | Python: {sys.version}")
        
        # 1. Initialize Core
        trace_logger.info("[INIT] Initializing SystemCore...")
        core = SystemCore()
        
        # 2. Start Logic Threads
        trace_logger.info("[INIT] Starting background processing threads...")
        core.start()

        # 3. Start Conversation Manager
        trace_logger.info("[INIT] Initializing Conversation Manager...")
        converse = ConversationManager(core)
        converse.start()

        # 4. Run API Server (Blocks main thread)
        trace_logger.info("[INIT] Launching FastAPI Server on http://localhost:8000")
        run_server(core, host="0.0.0.0", port=8000)

    except KeyboardInterrupt:
        trace_logger.info("=== System shutdown requested by user ===")
    except Exception as e:
        trace_logger.critical(f"!!! FATAL CRASH !!! Error: {e}")
        trace_logger.error(traceback.format_exc())
    finally:
        trace_logger.info("=== SentinelX TRACE END ===")
        time.sleep(2)

if __name__ == "__main__":
    main()
