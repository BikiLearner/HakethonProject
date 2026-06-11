const API_BASE = window.location.protocol + "//" + window.location.host;

let lastStatus = "";
let lastThinking = false;
let isSpeaking = false;
let lastSpeech = "";
let lastSpeaking = false;
let speakingTimeout = null;
let audioCtx = new (window.AudioContext || window.webkitAudioContext)();
let mouthAnimating = false;
const robotHead = document.getElementById("robot-head");

// ----------------------------------------------------
// STATE SYNC & REACTIVITY
// ----------------------------------------------------
async function updateState() {
  try {
    const response = await fetch(`${API_BASE}/state`);
    const data = await response.json();
    if (data.error) return;

    // 1. Header & Context Updates
    const machineEl = document.getElementById("active-machine");
    if (machineEl) machineEl.innerText = data.machine_name || "GENERIC UNIT";

    const statusEl = document.getElementById("system-status-text");
    if (statusEl) statusEl.innerText = data.status || "IDLE";

    const clockEl = document.getElementById("clock");
    if (clockEl)
      clockEl.innerText = new Date().toLocaleTimeString("en-GB", {
        hour12: false,
      });
    // 🔥 SPEAKING ANIMATION CONTROL
    if (data.ai_speaking) {
      robotHead.classList.add("speaking");
    } else {
      robotHead.classList.remove("speaking");
    }

    // 2. Robot Face Reactivity
    if (
      data.status !== lastStatus ||
      data.is_thinking !== lastThinking ||
      data.is_speaking !== lastSpeaking
    ) {
      updateRobotBehavior(
        data.status,
        data.risk_score,
        data.is_thinking,
        data.ai_speaking, // 🔥 THIS
      );
      if (data.status !== lastStatus) {
        let logType = "info";
        if (data.status === "DANGER") logType = "crit";
        else if (data.status === "CAUTION") logType = "warn";
        addLog(`Operational State changed to ${data.status}`, logType);
      }

      lastStatus = data.status;
      lastThinking = data.is_thinking;
      lastSpeaking = data.ai_speaking; // ✅ FIXED
    }
    // 3. Dynamic Dashboard
    if (document.getElementById("dynamic-metrics")) {
      renderDashboard(data);
    }

    // 4. Speech Updates
    const speechText = document.getElementById("speech-text");
    if (speechText && data.ai_response) {
      if (speechText.innerText !== data.ai_response) {
        speechText.innerText = data.ai_response;
        playAndAnimate();
      }
    }
  } catch (e) {
    console.error("Link Failure:", e);
  }
}

// ----------------------------------------------------
// ROBOT BEHAVIOR ENGINE
// ----------------------------------------------------
function updateRobotBehavior(status, risk, isThinking, isSpeaking) {
  const head = document.getElementById("robot-head");
  if (!head) return;

  head.classList.remove("danger", "caution", "thinking");

  if (isThinking) head.classList.add("thinking");

  if (status === "DANGER" || risk > 0.75) {
    head.classList.add("danger");
    express("SQUINT");
  } else if (status === "CAUTION" || risk > 0.4) {
    head.classList.add("caution");
    express("ALERT");
  } else {
    express("NORMAL");
  }

  // 🔥 REAL SYNC
  if (!isSpeaking) {
    stopMouthAnimation();
  }
}

async function playAndAnimate() {
  const audio = new Audio("/speak_audio");

  const bars = document.querySelectorAll(".spec-bar");
  const head = document.getElementById("robot-head");

  const src = audioCtx.createMediaElementSource(audio);
  const analyser = audioCtx.createAnalyser();

  src.connect(analyser);
  analyser.connect(audioCtx.destination);

  analyser.fftSize = 64;
  const dataArray = new Uint8Array(analyser.frequencyBinCount);

  function animate() {
    analyser.getByteFrequencyData(dataArray);

    bars.forEach((bar, i) => {
      let v = dataArray[i] / 255;
      bar.style.height = `${5 + v * 40}px`;
    });

    head.classList.add("speaking");

    if (!audio.paused) {
      requestAnimationFrame(animate);
    }
  }

  audio.onplay = () => {
    audioCtx.resume(); // 🔥 IMPORTANT FIX
    animate();
  };

  audio.onended = () => {
    head.classList.remove("speaking");
    bars.forEach((b) => (b.style.height = "6px"));
  };

  audio.play();
}

function animateMouth(text) {
  const bars = document.querySelectorAll(".spec-bar");
  const head = document.getElementById("robot-head");

  head.classList.add("speaking");

  let duration = Math.max(1500, text.length * 60);
  let start = Date.now();

  function animate() {
    let elapsed = Date.now() - start;

    bars.forEach((bar) => {
      let randomHeight = 5 + Math.random() * 35;
      bar.style.height = `${randomHeight}px`;
    });

    if (elapsed < duration) {
      requestAnimationFrame(animate);
    } else {
      // reset
      bars.forEach((bar) => (bar.style.height = "6px"));
      head.classList.remove("speaking");
    }
  }

  animate();
}

function startMouthAnimation() {
  if (mouthAnimating) return;

  const bars = document.querySelectorAll(".spec-bar");
  const head = document.getElementById("robot-head");

  mouthAnimating = true;
  head.classList.add("speaking");

  function animate() {
    if (!mouthAnimating) return;

    bars.forEach((bar) => {
      bar.style.height = `${5 + Math.random() * 40}px`;
    });

    requestAnimationFrame(animate);
  }

  animate();
}

function stopMouthAnimation() {
  const bars = document.querySelectorAll(".spec-bar");
  const head = document.getElementById("robot-head");

  mouthAnimating = false;
  head.classList.remove("speaking");

  bars.forEach((bar) => (bar.style.height = "6px"));
}

function express(mood) {
  const dots = document.querySelectorAll(".led-dot");
  dots.forEach((dot) => {
    if (mood === "SQUINT") {
      dot.style.height = "10px";
      dot.style.marginTop = "15px";
    } else if (mood === "ALERT") {
      dot.style.height = "45px";
      dot.style.marginTop = "0px";
    } else {
      dot.style.height = "35px";
      dot.style.marginTop = "0px";
    }
  });
}

// 3D Head Tracking
document.addEventListener("mousemove", (e) => {
  const head = document.getElementById("robot-head");
  if (!head) return;

  const rect = head.getBoundingClientRect();
  const centerX = rect.left + rect.width / 2;
  const centerY = rect.top + rect.height / 2;

  const rotY = (e.clientX - centerX) / 25;
  const rotX = -(e.clientY - centerY) / 25;

  const limit = 15;
  const rY = Math.max(-limit, Math.min(limit, rotY));
  const rX = Math.max(-limit, Math.min(limit, rotX));

  head.style.transform = `rotateX(${rX}deg) rotateY(${rY}deg)`;

  const eyes = document.querySelectorAll(".led-grid");
  eyes.forEach((eye) => {
    eye.style.transform = `translateX(${rY * 0.5}px) translateY(${-rX * 0.5}px)`;
  });
});

// ----------------------------------------------------
// DASHBOARD ENGINE (MISSION CONTROL)
// ----------------------------------------------------
function renderDashboard(data) {
  const container = document.getElementById("dynamic-metrics");
  if (!container) return;

  const state = data.machine_state || {};
  let html = "";

  // 1. Dynamic Metric Panels
  if (state.temperature !== undefined) {
    html += createCommandPanel(
      "System Temperature",
      state.temperature.toFixed(1),
      "°C",
      data.status,
    );
  }
  if (state.vibration !== undefined) {
    html += createCommandPanel(
      "Structural Vibration",
      state.vibration.toFixed(2),
      "mm/s",
      data.status,
    );
  }

  // Add any custom sensors from config
  const sensors = data.machine_config?.sensors || {};
  Object.entries(sensors).forEach(([key, cfg]) => {
    if (key !== "temperature" && key !== "vibration") {
      html += createCommandPanel(key, state[key] || 0.0, cfg.unit, data.status);
    }
  });

  container.innerHTML = html;

  // 2. Risk Probability Visualization
  const riskFill = document.getElementById("risk-fill");
  if (riskFill) {
    const riskVal = (data.risk_score * 100).toFixed(0);
    riskFill.style.width = `${riskVal}%`;
    document.getElementById("risk-val-text").innerText =
      data.risk_score.toFixed(2);
    document.getElementById("risk-pct-text").innerText = `${riskVal}%`;

    if (data.risk_score > 0.7) riskFill.style.background = "var(--ind-red)";
    else if (data.risk_score > 0.4)
      riskFill.style.background = "var(--ind-yellow)";
    else riskFill.style.background = "var(--ind-blue)";
  }
}

function createCommandPanel(title, val, unit, status) {
  let mode = "";
  if (status === "DANGER") mode = "danger";
  else if (status === "CAUTION" || status === "WARNING") mode = "caution";

  return `
        <div class="metric-panel ${mode}">
            <div class="m-title">${title.toUpperCase()}</div>
            <div class="m-main">
                <span class="m-val">${val}</span>
                <span class="m-unit">${unit}</span>
            </div>
            <div style="font-size: 0.6rem; color: #333; margin-top: 5px; font-family: 'Share Tech Mono'">SENS_ACTIVE_OK</div>
        </div>
    `;
}

function addLog(msg, type = "info") {
  const container = document.getElementById("event-logs");
  if (!container) return;

  const entry = document.createElement("div");
  entry.className = `log-entry ${type}`;
  const ts = new Date().toLocaleTimeString("en-GB", { hour12: false });
  entry.innerHTML = `<span class="log-ts">[${ts}]</span> <span class="log-msg">${msg.toUpperCase()}</span>`;

  container.prepend(entry);
  if (container.children.length > 15) container.lastChild.remove();
}

// ----------------------------------------------------
// BOOTSTRAP
// ----------------------------------------------------
setInterval(updateState, 500); // 2x faster updates
updateState();
addLog("Mission Control Subsystem Online", "info");
