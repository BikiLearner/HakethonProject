const AppState = {
  configured: false,
  data: {
    machine: "Autonomous CNC Center",
    temperature: 64.5,
    risk: "Nominal",
    vibration: "0.12 mm/s"
  }
};

const MEMORY = {
  status: "System is operating within safe limits",
  risk: "Current risk level is medium due to elevated temperature",
  health: "Machine health is stable",
  helmet: "Critical alert. A safety issue has been detected in the restricted zone"
};

const IDLE_CHATTER = [
  "All systems operational. Monitoring machine health.",
  "Scanning for safety breaches. Current status is normal.",
  "Data throughput is stable. Proactive core is active.",
  "Machine telemetry is within expected range.",
  "Hydraulic press temperature is steady.",
  "No immediate risks detected in the vicinity."
];

const DEMO_LOGS = [
  "Parsing machine specs...",
  "Building models...",
  "Calibrating thresholds...",
  "Deploying system..."
];

const $ = (selector, scope = document) => scope.querySelector(selector);
const $$ = (selector, scope = document) => Array.from(scope.querySelectorAll(selector));

document.addEventListener("DOMContentLoaded", () => {
  syncState();
  updateSystemPill();
  wireGlobalClicks();

  const page = document.body.dataset.page;
  if (page === "robot") initRobot();
  if (page === "dashboard") initDashboard();
  if (page === "upload") initUpload();
  if (page === "remote") initRemote();
});

function syncState() {
  AppState.configured = localStorage.getItem("configured") === "true";
}

function updateSystemPill() {
  const pill = $("#systemPill");
  if (!pill) return;

  pill.textContent = AppState.configured ? "Configured" : "Not Configured";
  pill.classList.toggle("offline", !AppState.configured);
}

function wireGlobalClicks() {
  document.addEventListener("click", (event) => {
    if (event.target.closest("button, a")) playTone("click");
  });
}

function playTone(type) {
  const audio = type === "alert" ? $("#alertSound") : $("#clickSound");
  if (audio) {
    audio.currentTime = 0;
    audio.play().catch(() => {});
  }

  const AudioContext = window.AudioContext || window.webkitAudioContext;
  if (!AudioContext) return;

  const context = new AudioContext();
  const oscillator = context.createOscillator();
  const gain = context.createGain();
  oscillator.type = type === "alert" ? "sawtooth" : "sine";
  oscillator.frequency.value = type === "alert" ? 880 : 420;
  gain.gain.setValueAtTime(type === "alert" ? 0.08 : 0.035, context.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.001, context.currentTime + 0.18);
  oscillator.connect(gain);
  gain.connect(context.destination);
  oscillator.start();
  oscillator.stop(context.currentTime + 0.2);
}

function initRobot() {
  const face = $("#robotFace");
  const response = $("#robotResponse");
  const context = $("#robotContext");
  const mode = $("#commandMode");
  const stateText = $("#robotStateText");
  const micButton = $("#micButton");
  const recognition = "SpeechRecognition" in window ? new SpeechRecognition() : ("webkitSpeechRecognition" in window ? new webkitSpeechRecognition() : null);
  const openedFromFile = window.location.protocol === "file:";
  let isListening = false;
  let capturedSpeech = "";
  let silenceTimer = null;
  let micAnswerPending = false;
  let autoListenEnabled = false;
  let audioModeActive = false;
  let micStream = null;
  let audioContext = null;
  let analyser = null;
  let vadFrame = null;
  let voiceStarted = false;
  let silenceStartedAt = 0;
  let demoIntentIndex = 0;
  let lastRemoteCommandId = "";
  let idleChatterTimer = null;
  const remoteChannel = "BroadcastChannel" in window ? new BroadcastChannel("sentinelx_remote") : null;

  function startIdleChatter() {
    stopIdleChatter();
    idleChatterTimer = window.setInterval(() => {
      if (!isListening && !window.speechSynthesis.speaking) {
        const message = randomItem(IDLE_CHATTER);
        response.textContent = message;
        speak(message);
      }
    }, 15000);
  }

  function stopIdleChatter() {
    if (idleChatterTimer) {
      window.clearInterval(idleChatterTimer);
      idleChatterTimer = null;
    }
  }

  startIdleChatter();

  context.textContent = AppState.configured
    ? "Autonomous CNC Center profile loaded. Safety monitoring and multi-axis telemetry are synchronized with my neural core."
    : "Initializing SentinelX core. Monitoring system health and safety protocols.";
  mode.textContent = AppState.configured ? "Machine-aware core" : "Autonomous core";

  if (!AppState.configured) {
    const configMsg = "System is currently unconfigured. Please navigate to the Configure page and upload your machine workbook to activate my monitoring core.";
    response.textContent = configMsg;
    window.setTimeout(() => speak(configMsg), 1200);
  } else {
    response.textContent = "System online. Standing by for telemetry and voice signals.";
  }

  if (recognition) {
    recognition.lang = "en-US";
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      isListening = true;
      micAnswerPending = true;
      capturedSpeech = "";
      clearTimeout(silenceTimer);
      window.speechSynthesis.cancel();
      micButton.classList.add("listening");
      setMicLabel("Auto Listening");
      response.textContent = "Listening automatically... speak now";
      setRobotState("thinking", "Auto listening active");
    };

    recognition.onresult = (event) => {
      let finalText = "";
      let interimText = "";

      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const text = event.results[index][0].transcript;
        if (event.results[index].isFinal) {
          finalText += text;
        } else {
          interimText += text;
        }
      }

      if (finalText.trim()) {
        capturedSpeech = `${capturedSpeech} ${finalText}`.trim();
      }

      const visibleSpeech = `${capturedSpeech} ${interimText}`.trim();
      response.textContent = visibleSpeech ? `Listening: "${visibleSpeech}"` : "Listening... speak now";

      clearTimeout(silenceTimer);
      silenceTimer = window.setTimeout(() => {
        if (isListening) recognition.stop();
      }, 1300);
    };

    recognition.onerror = (event) => {
      isListening = false;
      micAnswerPending = false;
      clearTimeout(silenceTimer);
      micButton.classList.remove("listening");
      setMicLabel("Start Listening");

      if (event.error === "no-speech") {
        response.textContent = "Switching to direct microphone mode. Speak naturally, then pause.";
        setRobotState("thinking", "Direct mic mode active");
        startAudioLevelListening();
        return;
      }

      if (event.error === "not-allowed" || event.error === "service-not-allowed") {
        autoListenEnabled = false;
        response.textContent = "Microphone permission is blocked. Allow mic access, then click Start Listening.";
        setRobotState("warning", "Mic permission required");
        return;
      }

      response.textContent = "Speech recognition paused. Using direct microphone mode instead.";
      setRobotState("thinking", "Direct mic mode active");
      startAudioLevelListening();
    };

    recognition.onend = () => {
      isListening = false;
      clearTimeout(silenceTimer);
      micButton.classList.remove("listening");
      setMicLabel("Start Listening");

      if (!capturedSpeech.trim()) {
        micAnswerPending = false;
        response.textContent = "Listening... waiting for your voice.";
        setRobotState("thinking", "Waiting for voice");
        restartListening(700);
        return;
      }

      response.textContent = `Heard: "${capturedSpeech}"`;
      window.setTimeout(() => {
        handleTranscript(capturedSpeech);
        restartListening(1600);
      }, 450);
    };

  }

  micButton.addEventListener("click", () => {
    window.speechSynthesis.cancel();
    stopIdleChatter();
    response.textContent = "Proactive monitoring paused. Standing by for manual query.";
    setRobotState("idle", "Idle monitoring active");
    window.setTimeout(startIdleChatter, 10000);
  });

  $$(".memory-grid button").forEach((button) => {
    button.addEventListener("click", () => {
      stopIdleChatter();
      answerQuery(button.dataset.query);
      window.setTimeout(startIdleChatter, 10000);
    });
  });

  window.addEventListener("storage", (event) => {
    if (event.key === "sentinelx_remote_command" && event.newValue) {
      handleRemoteCommand(event.newValue);
    }
  });

  if (remoteChannel) {
    remoteChannel.addEventListener("message", (event) => {
      handleRemoteCommand(event.data);
    });
  }

  window.setInterval(() => {
    const command = localStorage.getItem("sentinelx_remote_command");
    if (command) handleRemoteCommand(command);
  }, 350);

  function answerQuery(query) {
    micAnswerPending = false;
    const message = buildResponse(query);
    response.textContent = message;
    speak(message);

    if (query === "helmet") {
      setRobotState("critical", "Safety breach detected");
      playTone("alert");
    } else if (query === "risk") {
      setRobotState("warning", "Risk advisory active");
    } else {
      setRobotState("idle", "System normal");
    }
  }

  function handleTranscript(transcript) {
    const query = detectIntent(transcript);
    const heardPrefix = transcript ? `Heard: "${transcript}". ` : "";

    if (!query) {
      response.textContent = `${heardPrefix}I am currently monitoring status, risk, health, and safety.`;
      setRobotState("warning", "Signal not recognized");
      micAnswerPending = false;
      return;
    }

    answerQuery(query);
  }

  function useFallbackListening() {
    response.textContent = "Processing system request...";
    setRobotState("thinking", "Analyzing core telemetry");

    window.setTimeout(() => {
      const query = randomItem(Object.keys(MEMORY));
      response.textContent = `Autonomous query: ${query}`;
      answerQuery(query);
    }, 900);
  }

  function buildResponse(query) {
    if (!AppState.configured) {
      return `${MEMORY[query]}. Monitoring local environment.`;
    }

    if (query === "helmet") {
      return `${MEMORY.helmet} near ${AppState.data.machine}. Safety confidence is 92 percent.`;
    }

    return `${MEMORY[query]} for ${AppState.data.machine}. Temperature is ${AppState.data.temperature} degrees Celsius, vibration is ${AppState.data.vibration}, and safety camera monitoring is active.`;
  }

  function setRobotState(state, text) {
    face.classList.remove("idle", "thinking", "warning", "critical");
    face.classList.add(state);
    stateText.textContent = text;
  }

  function setMicLabel(text) {
    const label = micButton.querySelector("span:last-child");
    if (label) label.textContent = text;
  }

  function handleRemoteCommand(rawCommand) {
    let command;
    try {
      command = typeof rawCommand === "string" ? JSON.parse(rawCommand) : rawCommand;
    } catch (error) {
      return;
    }

    if (!command.id || command.id === lastRemoteCommandId) return;
    lastRemoteCommandId = command.id;

    // Map intents to demo questions for visual feedback
    const intentToQuestion = {
      status: "What is the current status?",
      risk: "Are there any safety risks?",
      health: "Machine performance report",
      helmet: "Analyze current safety issues"
    };

    if (command.type === "speak") {
      autoListenEnabled = false;
      stopRemoteListening();
      stopIdleChatter();
      
      const question = intentToQuestion[command.intent] || "Core signal received";
      response.textContent = `Processing query: "${question}"`;
      setRobotState("thinking", "Analyzing core telemetry");
      
      window.setTimeout(() => {
        answerQuery(command.intent || "status");
        window.setTimeout(startIdleChatter, 10000);
      }, 800);
      return;
    }

    if (command.type === "listen") {
      autoListenEnabled = false;
      stopRemoteListening();
      stopIdleChatter();
      window.speechSynthesis.cancel();
      face.classList.remove("speaking");
      micButton.classList.add("listening");
      setMicLabel("Listening...");
      response.textContent = "Listening for voice command...";
      setRobotState("thinking", "Voice signal active");
      return;
    }

    if (command.type === "end") {
      stopRemoteListening();
      const question = intentToQuestion[command.intent] || "Signal received";
      
      // Step 1: Show what was "heard"
      response.textContent = `Heard: "${question}"`;
      setRobotState("thinking", "Processing voice signal");
      
      window.setTimeout(() => {
        // Step 2: Show "Thinking/Analyzing"
        response.textContent = "Analyzing telemetry and generating response...";
        
        window.setTimeout(() => {
          // Step 3: Answer
          answerQuery(command.intent || "status");
          startIdleChatter();
        }, 1200);
      }, 1000);
    }
  }

  function stopRemoteListening() {
    clearTimeout(silenceTimer);
    micButton.classList.remove("listening");
    setMicLabel("Activate Mic");

    if (isListening && recognition) {
      try {
        recognition.stop();
      } catch (error) {}
    }

    if (audioModeActive) {
      stopAudioLevelListening(false);
    }

    isListening = false;
    micAnswerPending = false;
  }

  function startListening() {
    if (!recognition || isListening || audioModeActive || !autoListenEnabled) return;

    try {
      window.speechSynthesis.cancel();
      recognition.start();
    } catch (error) {
      restartListening(900);
    }
  }

  function restartListening(delay) {
    if (!autoListenEnabled) return;
    window.setTimeout(() => {
      if (!isListening && !audioModeActive && !micAnswerPending) startListening();
    }, delay);
  }

  async function startAudioLevelListening() {
    if (audioModeActive || openedFromFile || !autoListenEnabled) return;

    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !AudioContext) {
        response.textContent = "Mic access is unavailable in this browser. Use Chrome or Edge on localhost.";
        setRobotState("warning", "Mic unavailable");
        return;
      }

      micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioContext = new AudioContext();
      analyser = audioContext.createAnalyser();
      analyser.fftSize = 1024;

      const source = audioContext.createMediaStreamSource(micStream);
      source.connect(analyser);

      audioModeActive = true;
      isListening = true;
      micAnswerPending = true;
      voiceStarted = false;
      silenceStartedAt = 0;
      window.speechSynthesis.cancel();
      micButton.classList.add("listening");
      setMicLabel("Auto Listening");
      response.textContent = "Listening automatically... speak now";
      setRobotState("thinking", "Direct mic listening");
      monitorAudioLevel();
    } catch (error) {
      autoListenEnabled = false;
      audioModeActive = false;
      isListening = false;
      micAnswerPending = false;
      response.textContent = "Microphone permission is blocked. Allow mic access, then click Start Listening.";
      setRobotState("warning", "Mic permission required");
    }
  }

  function monitorAudioLevel() {
    if (!audioModeActive || !analyser) return;

    const data = new Uint8Array(analyser.fftSize);
    analyser.getByteTimeDomainData(data);
    let sum = 0;

    data.forEach((value) => {
      const centered = (value - 128) / 128;
      sum += centered * centered;
    });

    const volume = Math.sqrt(sum / data.length);
    const bars = buildVolumeBars(volume);

    if (volume > 0.035) {
      voiceStarted = true;
      silenceStartedAt = 0;
      response.textContent = `Mic input detected ${bars}`;
      setRobotState("thinking", "Voice input detected");
    } else if (voiceStarted) {
      if (!silenceStartedAt) silenceStartedAt = Date.now();
      response.textContent = `Processing voice input ${bars}`;

      if (Date.now() - silenceStartedAt > 1200) {
        stopAudioLevelListening(true);
        return;
      }
    } else {
      response.textContent = `Listening automatically ${bars}`;
    }

    vadFrame = window.requestAnimationFrame(monitorAudioLevel);
  }

  function stopAudioLevelListening(shouldAnswer) {
    audioModeActive = false;
    isListening = false;
    window.cancelAnimationFrame(vadFrame);
    micButton.classList.remove("listening");
    setMicLabel("Start Listening");

    if (micStream) {
      micStream.getTracks().forEach((track) => track.stop());
      micStream = null;
    }

    if (audioContext) {
      audioContext.close().catch(() => {});
      audioContext = null;
    }

    analyser = null;

    if (!shouldAnswer) {
      micAnswerPending = false;
      response.textContent = "Automatic listening paused. Click Start Listening to resume.";
      setRobotState("idle", "Listening paused");
      return;
    }

    const query = nextDemoIntent();
    response.textContent = `Voice input received. Demo intent: ${query}.`;
    window.setTimeout(() => {
      answerQuery(query);
      if (autoListenEnabled) window.setTimeout(() => startAudioLevelListening(), 1600);
    }, 450);
  }

  function nextDemoIntent() {
    const intents = AppState.configured
      ? ["status", "risk", "helmet", "health"]
      : ["status", "risk", "health", "helmet"];
    const intent = intents[demoIntentIndex % intents.length];
    demoIntentIndex += 1;
    return intent;
  }

  function buildVolumeBars(volume) {
    const count = Math.max(1, Math.min(8, Math.round(volume * 90)));
    return `[${"|".repeat(count)}${".".repeat(8 - count)}]`;
  }
}

function detectIntent(transcript) {
  const text = transcript.toLowerCase();

  const intentMap = [
    {
      intent: "helmet",
      words: ["helmet", "hard hat", "worker", "person", "safety", "camera", "detected", "detection"]
    },
    {
      intent: "risk",
      words: ["risk", "danger", "unsafe", "warning", "temperature", "temp", "heat", "hot"]
    },
    {
      intent: "health",
      words: ["health", "machine health", "condition", "stable", "maintenance", "status of machine"]
    },
    {
      intent: "status",
      words: ["status", "system", "state", "update", "report", "operating", "overview"]
    }
  ];

  const match = intentMap.find((entry) => entry.words.some((word) => text.includes(word)));
  return match ? match.intent : null;
}

function initRemote() {
  const log = $("#remoteLog");
  const select = $("#remoteIntent");
  const origin = $("#remoteOrigin");
  const remoteChannel = "BroadcastChannel" in window ? new BroadcastChannel("sentinelx_remote") : null;

  if (origin) {
    origin.textContent = `Control origin: ${window.location.origin}. Robot must be opened from the same origin.`;
  }

  $$(".remote-panel button").forEach((button) => {
    button.addEventListener("click", () => {
      const type = button.dataset.remoteCommand;
      const intent = type === "end"
        ? select.value
        : button.dataset.intent || select.value;

      sendRemoteCommand(type, intent);
      log.textContent = formatRemoteLog(type, intent);
    });
  });

  function sendRemoteCommand(type, intent) {
    const command = {
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      type,
      intent
    };

    if (remoteChannel) {
      remoteChannel.postMessage(command);
    }

    localStorage.removeItem("sentinelx_remote_command");
    localStorage.setItem("sentinelx_remote_command", JSON.stringify(command));
  }

  function formatRemoteLog(type, intent) {
    if (type === "listen") return "Robot set to Listening mode.";
    if (type === "end") return `Robot will end listening and answer: ${intent}.`;
    return `Robot speaking: ${intent}.`;
  }
}

function initDashboard() {
  if (!AppState.configured) {
    renderUnconfiguredDashboard();
    return;
  }

  $("#dashboardTitle").textContent = "Autonomous CNC Monitoring";
  $("#dashboardSubtitle").textContent = "SentinelX CNC profile active. Multi-axis telemetry and safety monitoring are online.";
  $("#machineValue").textContent = AppState.data.machine;
  $("#riskValue").textContent = AppState.data.risk;
  $("#vibrationValue").textContent = AppState.data.vibration;
  
  // Populate Extracted Configuration Cards
  if ($("#coreValue")) {
    $("#coreValue").textContent = "SEC-HUB-04";
    $("#coreValue").nextElementSibling.textContent = "Production Bay Registry";
    
    $("#safetyValue").textContent = "Full-Auto";
    $("#safetyValue").nextElementSibling.textContent = "AI-Drive Active";
    
    $("#modelValue").textContent = "Activated";
    $("#modelValue").nextElementSibling.textContent = "Neural Bridge Stable";
    
    $("#syncValue").textContent = "ISO-10218-1";
    $("#syncValue").nextElementSibling.textContent = "Compliance Verified";
  }

  $("#chartStatus").textContent = "Live simulated telemetry";
  $("#cameraStatus").textContent = "Online";
  $("#detectionMeta").innerHTML = "<span>Confidence: <strong>--</strong></span><span>Object: <strong>--</strong></span>";

  $$(".disabled").forEach((element) => element.classList.remove("disabled"));
  $(".metric-card:nth-child(3)").classList.add("risk");

  const configBtn = $("#configButton");
  if (configBtn) configBtn.style.display = "none";

  const liveFeed = $("#liveFeed");
  if (liveFeed) {
    liveFeed.src = "http://localhost:8000/video_feed";
    liveFeed.style.display = "block";
    liveFeed.onerror = () => {
      liveFeed.style.display = "none";
      console.warn("Backend video feed not available. Running in simulation mode.");
    };
  }

  animateTemperature(0, AppState.data.temperature, $("#tempValue"));
  startLiveTelemetrySimulation();
  activateCameraDetection();
}

function startLiveTelemetrySimulation() {
  const tempEl = $("#tempValue");
  const vibEl = $("#vibrationValue");
  const riskEl = $("#riskValue");
  const riskCard = $(".metric-card:nth-child(3)");
  const chartBars = $$("#fakeChart i");
  
  let currentTemp = AppState.data.temperature;

  window.setInterval(() => {
    // 1. Dynamic Temperature & Vibration
    const tempOffset = (Math.random() * 1.6 - 0.8);
    currentTemp = Math.min(75, Math.max(55, currentTemp + tempOffset));
    const currentVib = (0.10 + Math.random() * 0.05).toFixed(2);
    
    if (tempEl) tempEl.textContent = currentTemp.toFixed(1);
    if (vibEl) vibEl.textContent = `${currentVib} mm/s`;

    // 2. Dynamic Risk Logic
    let riskLevel = "Nominal";
    if (currentTemp > 70) {
      riskLevel = "Warning";
      riskCard.style.borderColor = "var(--yellow)";
      riskEl.style.color = "var(--yellow)";
    } else if (currentTemp > 73) {
      riskLevel = "Critical";
      riskCard.style.borderColor = "var(--red)";
      riskEl.style.color = "var(--red)";
    } else {
      riskCard.style.borderColor = "var(--line)";
      riskEl.style.color = "var(--blue)";
    }
    if (riskEl) riskEl.textContent = riskLevel;

    // 3. Dynamic Thermal Chart (Real-time shifting)
    if (chartBars.length > 0) {
      // Shift heights to the left
      for (let i = 0; i < chartBars.length - 1; i++) {
        chartBars[i].style.height = chartBars[i+1].style.height;
      }
      // Add new value at the end (scaled temperature)
      const chartHeight = Math.floor(((currentTemp - 55) / 20) * 100);
      chartBars[chartBars.length - 1].style.height = `${Math.max(15, Math.min(95, chartHeight))}%`;
      
      // Change chart color based on risk
      chartBars.forEach(bar => {
        bar.style.background = currentTemp > 73 ? "var(--red)" : (currentTemp > 70 ? "var(--yellow)" : "var(--blue)");
      });
    }
  }, 2000);
}

function renderUnconfiguredDashboard() {
  $("#dashboardTitle").textContent = "No system configured";
  $("#dashboardSubtitle").textContent = "Upload a machine configuration file to activate SentinelX industrial monitoring.";
  $("#cameraStatus").textContent = "Offline";
}

function animateTemperature(start, end, target) {
  let current = start;
  const timer = window.setInterval(() => {
    current += 2;
    target.textContent = current >= end ? end : current;
    if (current >= end) window.clearInterval(timer);
  }, 38);
}

function activateCameraDetection() {
  const panel = $("#cameraPanel");
  const frame = $("#videoFrame");
  const meta = $("#detectionMeta");

  window.setTimeout(() => {
    panel.classList.add("detected");
    // frame.classList.add("alerting"); // Removed red border alert
    $("#cameraStatus").textContent = "Safety breach";
    meta.innerHTML = "<span>Confidence: <strong>92%</strong></span><span>Object: <strong>Person</strong></span>";
    playTone("alert");
  }, 4000);
}

function initUpload() {
  const dropZone = $("#dropZone");
  const fileInput = $("#fileInput");
  const loadingPanel = $("#loadingPanel");

  if (!dropZone || !fileInput) return;

  dropZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropZone.classList.add("dragging");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragging");
  });

  dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropZone.classList.remove("dragging");
    const files = event.dataTransfer.files;
    if (files.length > 0) startUpload(files[0]);
  });

  dropZone.addEventListener("click", () => fileInput.click());
  
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) startUpload(fileInput.files[0]);
  });

  if (AppState.configured && $(".preview-table")) {
    $(".preview-table").style.display = "block";
  }

  loadingPanel.style.opacity = "0.72";
}

function startUpload(file) {
  const fill = $("#progressFill");
  const label = $("#progressLabel");
  const logList = $("#logList");
  const dropZone = $("#dropZone");
  const previewTable = $(".preview-table");
  const fileNameDisplay = previewTable ? previewTable.querySelector("small") : null;
  let progress = 0;
  let logIndex = 0;

  if (file && fileNameDisplay) {
    fileNameDisplay.textContent = file.name;
    DEMO_LOGS[0] = `Parsing ${file.name}...`;
  }

  dropZone.disabled = true;
  logList.innerHTML = "";

  const timer = window.setInterval(() => {
    progress = Math.min(progress + randomNumber(4, 9), 100);
    fill.style.width = `${progress}%`;
    label.textContent = `${progress}%`;

    if (progress >= (logIndex + 1) * 23 && logIndex < DEMO_LOGS.length) {
      appendLog(DEMO_LOGS[logIndex], logIndex === DEMO_LOGS.length - 1);
      logIndex += 1;
    }

    if (progress >= 100) {
      window.clearInterval(timer);
      localStorage.setItem("configured", "true");
      AppState.configured = true;
      if (previewTable) previewTable.style.display = "block";
      updateSystemPill();
      appendLog("Configuration complete. Redirecting...", true);
      window.setTimeout(() => {
        window.location.href = "dashboard.html";
      }, 900);
    }
  }, 170);

  function appendLog(text, active) {
    const item = document.createElement("li");
    item.textContent = text;
    if (active) item.classList.add("active");
    logList.appendChild(item);
  }
}

function speak(message) {
  if (!("speechSynthesis" in window)) return;
  const face = $("#robotFace");
  if (face) face.classList.remove("speaking");
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(message);
  utterance.rate = 0.92;
  utterance.pitch = 0.82;
  utterance.onstart = () => {
    if (face) face.classList.add("speaking");
  };
  utterance.onend = () => {
    if (face) face.classList.remove("speaking");
  };
  utterance.onerror = () => {
    if (face) face.classList.remove("speaking");
  };
  window.speechSynthesis.speak(utterance);
}

function randomItem(items) {
  return items[Math.floor(Math.random() * items.length)];
}

function randomNumber(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}
