const API_BASE = window.location.protocol + "//" + window.location.host;

let lastStatus = "";
let isListening = false;
let isSpeaking = false;
let speechQueue = [];

// Native Speech Recognition Setup
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = false;

    recognition.onstart = () => {
        isListening = true;
        document.getElementById('btn-listen').classList.add('active');
        document.getElementById('listening-indicator').classList.remove('hidden');
        document.getElementById('listening-indicator').innerText = "Listening... (Speak now)";
        serverLog("[TRACE STT] Native recognition started.");
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        serverLog(`[TRACE STT] Recognized: '${transcript}'`);
        document.getElementById('chat-input').value = transcript;
        sendChatMessage(transcript);
    };

    recognition.onerror = (e) => {
        serverLog(`[TRACE STT] Recognition error: ${e.error}`, "ERROR");
    };

    recognition.onend = () => {
        isListening = false;
        document.getElementById('btn-listen').classList.remove('active');
        document.getElementById('listening-indicator').classList.add('hidden');
        serverLog("[TRACE STT] Native recognition ended.");
    };
}

// Utility to send logs to python terminal
function serverLog(message, level="INFO") {
    fetch(`${API_BASE}/log`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ level: level, message: message })
    }).catch(e => console.error("Failed to send log to server", e));
    console.log(message);
}

// ----------------------------------------------------
// STATE SYNC
// ----------------------------------------------------
async function updateState() {
    try {
        const response = await fetch(`${API_BASE}/state`);
        const data = await response.json();
        if (data.error) return;

        document.getElementById('risk-value').innerText = `${(data.risk_score * 100).toFixed(0)}%`;
        document.getElementById('temp-value').innerText = `${data.machine_state ? data.machine_state.temperature.toFixed(1) : 0}°C`;

        const badge = document.getElementById('status-badge');
        badge.innerText = `SYSTEM ${data.status === 'SAFE' ? 'NOMINAL' : data.status}`;
        
        if (data.status !== lastStatus) {
            serverLog(`[TRACE EVENT] Status changed from ${lastStatus} to ${data.status}`);
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

    triggerSystemSpeech();
}

// ----------------------------------------------------
// BROWSER NATIVE TTS
// ----------------------------------------------------
async function triggerSystemSpeech() {
    try {
        serverLog("[TRACE TRIGGER] Calling /speak endpoint");
        const response = await fetch(`${API_BASE}/speak`);
        const data = await response.json();
        if (data.text) {
            serverLog(`[TRACE RESPONSE] Speak: '${data.text}'`);
            
            // PRIORITY OVERRIDE
            speechQueue = []; 
            if (isSpeaking) {
                window.speechSynthesis.cancel();
                isSpeaking = false;
            }
            
            queueSpeech(data.text);
        }
    } catch (e) { console.error("Speech trigger failed", e); }
}

async function sendChatMessage(message) {
    if (!message.trim()) return;
    
    serverLog("[TRACE ANIMATION] Starting thinking animation");
    document.body.classList.add('robot-thinking');
    
    const bubble = document.getElementById('speech-bubble');
    bubble.innerText = "Thinking...";
    bubble.style.opacity = 1;
    
    try {
        serverLog(`[TRACE TRIGGER] Calling /chat endpoint with message: '${message}'`);
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });
        const data = await response.json();
        
        document.body.classList.remove('robot-thinking');
        
        if (data.text) {
            serverLog(`[TRACE RESPONSE] Chat: '${data.text}'`);
            speechQueue = []; 
            if (isSpeaking) {
                window.speechSynthesis.cancel();
            }
            isSpeaking = false;
            queueSpeech(data.text);
        }
    } catch (e) {
        document.body.classList.remove('robot-thinking');
        queueSpeech("My neural link is unstable.");
    }
}

function queueSpeech(text) {
    speechQueue.push(text);
    processSpeechQueue();
}

async function processSpeechQueue() {
    if (isSpeaking || speechQueue.length === 0) return;
    isSpeaking = true;
    const text = speechQueue.shift();
    
    serverLog(`[TRACE TTS] Native speaking: '${text}'`);
    const bubble = document.getElementById('speech-bubble');
    const mouth = document.getElementById('mouth');
    
    if (bubble) {
        bubble.innerText = text;
        bubble.style.opacity = 1;
    }
    if (mouth) mouth.classList.add('speaking');

    const utterance = new SpeechSynthesisUtterance(text);
    
    // Attempt to pick a good voice
    const voices = window.speechSynthesis.getVoices();
    const femaleVoice = voices.find(v => v.name.includes('Female') || v.name.includes('Google UK English Female') || v.name.includes('Microsoft Zira'));
    if (femaleVoice) utterance.voice = femaleVoice;
    
    utterance.onend = () => {
        finishSpeech(mouth, bubble);
    };
    
    utterance.onerror = (e) => {
        serverLog(`[TRACE TTS] Native Error: ${e.error}`, "ERROR");
        finishSpeech(mouth, bubble);
    };

    window.speechSynthesis.speak(utterance);
}

function finishSpeech(mouth, bubble) {
    serverLog("[TRACE TTS] Finished speaking.");
    isSpeaking = false;
    if (mouth) mouth.classList.remove('speaking');
    if (bubble && speechQueue.length === 0) {
        setTimeout(() => {
            if (!isSpeaking) bubble.style.opacity = 0.5;
        }, 2000);
    }
    processSpeechQueue();
}

// ----------------------------------------------------
// BROWSER NATIVE STT
// ----------------------------------------------------
async function toggleListening() {
    if (!recognition) {
        alert("Speech Recognition not supported in this browser.");
        return;
    }
    if (isListening) {
        recognition.stop();
    } else {
        recognition.start();
    }
}


// ----------------------------------------------------
// UI BINDINGS
// ----------------------------------------------------
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

setInterval(updateState, 1500); 
updateState();
