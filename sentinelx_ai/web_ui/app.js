const API_BASE = window.location.protocol + "//" + window.location.host;

let lastStatus = "";
let isListening = false;
let recognition;
let speechQueue = [];
let isSpeaking = false;

// Utility to send logs to python terminal
function serverLog(message, level="INFO") {
    fetch(`${API_BASE}/log`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ level: level, message: message })
    }).catch(e => console.error("Failed to send log to server", e));
    
    if (level === "ERROR") console.error(message);
    else if (level === "WARN") console.warn(message);
    else console.log(message);
}

// Initialize Speech Recognition once
function initRecognition() {
    serverLog("[STT_DEBUG] initRecognition() called.", "INFO");
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        serverLog("[STT_DEBUG] Speech Recognition API NOT SUPPORTED in this browser.", "ERROR");
        return null;
    }

    const rec = new SpeechRecognition();
    rec.continuous = false;
    rec.interimResults = false;
    rec.lang = 'en-US';

    rec.onstart = (e) => {
        serverLog("[STT_DEBUG] EVENT: onstart. Microphone is active.");
        isListening = true;
        const btn = document.getElementById('btn-listen');
        const ind = document.getElementById('listening-indicator');
        if (btn) btn.classList.add('active');
        if (ind) {
            ind.classList.remove('hidden');
            ind.innerText = "Listening... (Speak now)";
        }
    };

    rec.onaudiostart = (e) => serverLog("[STT_DEBUG] EVENT: onaudiostart. Browser has started capturing audio.");
    rec.onsoundstart = (e) => serverLog("[STT_DEBUG] EVENT: onsoundstart. Browser has detected some sound.");
    rec.onspeechstart = (e) => serverLog("[STT_DEBUG] EVENT: onspeechstart. Browser has detected actual speech.");

    rec.onresult = (event) => {
        serverLog("[STT_DEBUG] EVENT: onresult.");
        const transcript = event.results[0][0].transcript;
        serverLog(`[STT_DEBUG] Final Transcript Heard: '${transcript}'`);
        const input = document.getElementById('chat-input');
        if (input) input.value = transcript;
        sendChatMessage(transcript);
    };

    rec.onspeechend = (e) => serverLog("[STT_DEBUG] EVENT: onspeechend. Speech has stopped.");
    rec.onsoundend = (e) => serverLog("[STT_DEBUG] EVENT: onsoundend. Sound has stopped.");
    rec.onaudioend = (e) => serverLog("[STT_DEBUG] EVENT: onaudioend. Audio capturing ended.");

    rec.onnomatch = (e) => serverLog("[STT_DEBUG] EVENT: onnomatch. Speech detected but not recognized.", "WARN");

    rec.onerror = (event) => {
        serverLog(`[STT_DEBUG] EVENT: onerror. Error Code: '${event.error}'. Message: '${event.message}'`, "ERROR");
        if (event.error === 'not-allowed') {
            alert("Microphone access is blocked! Please check browser permissions.");
        } else if (event.error === 'network') {
            alert("⚠️ VOICE RECOGNITION BLOCKED BY BROWSER ⚠️\n\nGoogle Chrome requires an active internet connection AND an 'HTTPS' secure connection to use voice-to-text. Because SentinelX is running locally on 'HTTP', Chrome is blocking the audio transfer.\n\nWORKAROUNDS:\n1. Type your questions in the chat box instead.\n2. In Chrome, go to chrome://flags/#unsafely-treat-insecure-origin-as-secure, enable it, and add 'http://localhost:8000'.");
        }
    };

    rec.onend = (e) => {
        serverLog("[STT_DEBUG] EVENT: onend. Voice recognition fully ENDED.");
        isListening = false;
        const btn = document.getElementById('btn-listen');
        const ind = document.getElementById('listening-indicator');
        if (btn) btn.classList.remove('active');
        if (ind) ind.classList.add('hidden');
    };

    return rec;
}

recognition = initRecognition();

async function updateState() {
    try {
        const response = await fetch(`${API_BASE}/state`);
        const data = await response.json();
        if (data.error) return;

        // Trace log every 5 seconds to avoid spam, but useful for debugging
        if (Math.random() < 0.2) {
            console.log(`[TRACE STATE] Temp: ${data.machine_state?.temperature.toFixed(1)}, Status: ${data.status}`);
        }

        document.getElementById('risk-value').innerText = `${(data.risk_score * 100).toFixed(0)}%`;
        document.getElementById('temp-value').innerText = `${data.machine_state ? data.machine_state.temperature.toFixed(1) : 0}°C`;

        const badge = document.getElementById('status-badge');
        badge.innerText = `SYSTEM ${data.status === 'SAFE' ? 'NOMINAL' : data.status}`;
        
        if (data.status !== lastStatus) {
            console.log(`[TRACE EVENT] Status changed from ${lastStatus} to ${data.status}`);
            handleStatusChange(data.status, data.risk_score);
            lastStatus = data.status;
        }
    } catch (error) {
        console.error("Update failed:", error);
    }
}

function handleStatusChange(status, risk) {
    const eyeLeft = document.getElementById('eye-left');
    const eyeRight = document.getElementById('eye-right');
    const glow = document.getElementById('glow');
    const badge = document.getElementById('status-badge');
    const mouth = document.getElementById('mouth');

    let color = "#00ffcc";
    let glowColor = "rgba(0, 255, 204, 0.15)";
    let badgeClass = "badge green";

    if (status === "DANGER" || risk > 0.7) {
        color = "#ff3e3e";
        glowColor = "rgba(255, 62, 62, 0.25)";
        badgeClass = "badge red";
    } else if (status === "CAUTION" || risk > 0.4) {
        color = "#ffdf00";
        glowColor = "rgba(255, 223, 0, 0.2)";
        badgeClass = "badge yellow";
    }

    eyeLeft.style.backgroundColor = color;
    eyeLeft.style.boxShadow = `0 0 30px ${color}`;
    eyeRight.style.backgroundColor = color;
    eyeRight.style.boxShadow = `0 0 30px ${color}`;
    glow.style.background = `radial-gradient(circle, ${glowColor} 0%, transparent 70%)`;
    badge.className = badgeClass;
    mouth.style.backgroundColor = color;
    mouth.style.boxShadow = `0 0 10px ${color}`;

    fetchSpeech();
}

async function fetchSpeech() {
    try {
        console.log("[TRACE TRIGGER] Calling /speak endpoint");
        const response = await fetch(`${API_BASE}/speak`);
        const data = await response.json();
        if (data.text) {
            console.log(`[TRACE RESPONSE] Speak: '${data.text}'`);
            
            // PRIORITY OVERRIDE: If a new system state comes in, we MUST stop 
            // whatever old alert is currently playing/queued, as it is now stale.
            speechQueue = []; 
            if (isSpeaking && 'speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                isSpeaking = false;
            }
            
            queueSpeech(data.text);
        }
    } catch (e) { console.error("Speech trigger failed"); }
}

async function sendChatMessage(message) {
    if (!message.trim()) return;
    
    // START THINKING ANIMATION
    console.log("[TRACE ANIMATION] Starting thinking animation");
    document.body.classList.add('robot-thinking');
    
    // Show bubble immediately
    const bubble = document.getElementById('speech-bubble');
    bubble.innerText = "Thinking...";
    bubble.style.opacity = 1;
    
    try {
        console.log(`[TRACE TRIGGER] Calling /chat endpoint with message: '${message}'`);
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });
        const data = await response.json();
        
        // STOP THINKING ANIMATION
        console.log("[TRACE ANIMATION] Stopping thinking animation");
        document.body.classList.remove('robot-thinking');
        
        if (data.text) {
            console.log(`[TRACE RESPONSE] Chat: '${data.text}'`);
            // Clear queue for immediate response to user input
            speechQueue = []; 
            isSpeaking = false;
            window.speechSynthesis.cancel();
            queueSpeech(data.text);
        }
    } catch (e) {
        console.error(`[TRACE ERROR] Chat error: ${e}`);
        document.body.classList.remove('robot-thinking');
        queueSpeech("My neural link is unstable.");
    }
}

function queueSpeech(text) {
    speechQueue.push(text);
    processSpeechQueue();
}

function processSpeechQueue() {
    if (isSpeaking || speechQueue.length === 0) return;
    
    if ('speechSynthesis' in window) {
        isSpeaking = true;
        const text = speechQueue.shift();
        const msg = new SpeechSynthesisUtterance(text);
        
        // Find best female voice
        const voices = window.speechSynthesis.getVoices();
        const preferredVoice = voices.find(v => 
            v.name.includes('Google UK English Female') || 
            v.name.includes('Google US English') || 
            v.name.includes('Zira') || 
            v.name.includes('Samantha') || 
            (v.name.includes('Female') && v.lang.startsWith('en'))
        ) || voices[0];
        
        if (preferredVoice) msg.voice = preferredVoice;
        
        msg.rate = 1.0;
        msg.pitch = 1.1;
        
        const mouth = document.getElementById('mouth');
        const bubble = document.getElementById('speech-bubble');
        
        msg.onstart = () => {
            console.log("[TRACE TTS] Speaking: ", text);
            if (bubble) {
                bubble.innerText = text;
                bubble.style.opacity = 1;
            }
            if (mouth) mouth.classList.add('speaking');
        };
        
        msg.onend = () => {
            console.log("[TRACE TTS] Finished speaking.");
            isSpeaking = false;
            if (mouth) mouth.classList.remove('speaking');
            if (bubble && speechQueue.length === 0) {
                setTimeout(() => {
                    if (!isSpeaking) bubble.style.opacity = 0.5;
                }, 2000);
            }
            // Process next message in queue
            processSpeechQueue();
        };
        
        msg.onerror = (e) => {
            console.error("[TRACE TTS] Error:", e);
            isSpeaking = false;
            if (mouth) mouth.classList.remove('speaking');
            processSpeechQueue();
        };
        
        window.speechSynthesis.speak(msg);
    } else {
        console.warn("Speech Synthesis not supported in this browser.");
        // Fallback: just show text
        const text = speechQueue.shift();
        const bubble = document.getElementById('speech-bubble');
        if (bubble) {
            bubble.innerText = text;
            bubble.style.opacity = 1;
            setTimeout(() => bubble.style.opacity = 0.5, 4000);
        }
        isSpeaking = false;
        processSpeechQueue();
    }
}

// Ensure voices are loaded
if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = () => {
        window.speechSynthesis.getVoices();
    };
}

function toggleListening() {
    if (!recognition) {
        alert("Use Chrome/Edge for voice input. Check microphone permissions.");
        return;
    }
    if (isListening) {
        console.log("[TRACE STT] Manually stopping recognition");
        recognition.stop();
    } else {
        try { 
            console.log("[TRACE STT] Manually starting recognition");
            recognition.start(); 
        } catch (e) { 
            console.error(`[TRACE STT] Start error: ${e}`);
            // Force reset state
            isListening = false;
            document.getElementById('btn-listen').classList.remove('active');
            document.getElementById('listening-indicator').classList.add('hidden');
        }
    }
}

function stopListening() {
    isListening = false;
    document.getElementById('btn-listen').classList.remove('active');
    document.getElementById('listening-indicator').classList.add('hidden');
}

document.getElementById('btn-send').addEventListener('click', () => {
    const input = document.getElementById('chat-input');
    sendChatMessage(input.value);
    input.value = "";
});

document.getElementById('chat-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendChatMessage(e.target.value);
        e.target.value = "";
    }
});

document.getElementById('btn-listen').addEventListener('click', toggleListening);

document.addEventListener('mousemove', (e) => {
    const eyes = document.querySelectorAll('.eye');
    eyes.forEach(eye => {
        const pupil = eye.querySelector('.pupil');
        const x = (e.clientX / window.innerWidth) * 15 - 7.5;
        const y = (e.clientY / window.innerHeight) * 15 - 7.5;
        pupil.style.transform = `translate(${x}px, ${y}px)`;
    });
});

function openDashboard() {
    window.location.href = "dashboard.html";
}

setInterval(updateState, 1500); // Slightly slower to prevent API spam
updateState();
