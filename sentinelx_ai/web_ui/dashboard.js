const API_BASE = "http://localhost:8000";
let chart;

async function initChart() {
    const ctx = document.getElementById('telemetryChart').getContext('2d');
    if (!ctx) return;
    
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'Temperature', data: [], borderColor: '#ef4444', tension: 0.1, borderWidth: 2, pointRadius: 0, fill: false },
                { label: 'Vibration x10', data: [], borderColor: '#00ffcc', tension: 0.1, borderWidth: 2, pointRadius: 0, fill: false },
                { label: 'Risk %', data: [], borderColor: '#f59e0b', tension: 0.1, borderWidth: 2, pointRadius: 0, fill: false }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 0 },
            scales: {
                y: { beginAtZero: true, grid: { color: '#242431' }, ticks: { color: '#94a3b8' } },
                x: { grid: { display: false }, ticks: { color: '#94a3b8', maxRotation: 0, autoSkip: true, maxTicksLimit: 10 } }
            },
            plugins: { legend: { labels: { color: '#94a3b8', font: { size: 10 } } } }
        }
    });
}

async function updateDashboard() {
    try {
        const response = await fetch(`${API_BASE}/state`);
        const data = await response.json();

        // Update Status
        const statusText = document.getElementById('status-text');
        const alertBox = document.getElementById('alert-box');

        if (statusText) statusText.innerText = data.status;
        if (document.getElementById('issue-text')) document.getElementById('issue-text').innerText = data.issue;
        if (document.getElementById('action-text')) document.getElementById('action-text').innerText = data.recommendation;
        if (document.getElementById('reason-text')) document.getElementById('reason-text').innerText = data.reason;

        // Colors
        let color = "#00ffcc";
        let alertClass = "alert-box info";

        if (data.status === "DANGER") {
            color = "#ef4444";
            alertClass = "alert-box danger";
        } else if (data.status === "CAUTION") {
            color = "#f59e0b";
            alertClass = "alert-box warning";
        }

        if (statusText) statusText.style.color = color;
        if (alertBox) alertBox.className = alertClass;

        // Mini Robot Styling
        const miniEyeLeft = document.getElementById('mini-eye-left');
        const miniEyeRight = document.getElementById('mini-eye-right');
        const miniMouth = document.getElementById('mini-mouth');
        const miniRobot = document.getElementById('mini-robot');
        const miniBubble = document.getElementById('mini-speech-bubble');

        if (miniEyeLeft) {
            miniEyeLeft.style.backgroundColor = color;
            miniEyeLeft.style.boxShadow = `0 0 5px ${color}`;
            miniEyeRight.style.backgroundColor = color;
            miniEyeRight.style.boxShadow = `0 0 5px ${color}`;
            miniMouth.style.backgroundColor = color;
            miniRobot.style.boxShadow = `0 0 10px ${color}`;
            
            // Show bubble randomly or on danger
            if (data.status === "DANGER" || Math.random() < 0.1) {
                miniBubble.innerText = data.issue || data.status;
                miniBubble.style.opacity = 1;
                miniMouth.classList.add('speaking');
                setTimeout(() => {
                    miniBubble.style.opacity = 0;
                    miniMouth.classList.remove('speaking');
                }, 3000);
            }
        }

        // Update Metrics
        if (data.machine_state) {
            if (document.getElementById('m-temp')) document.getElementById('m-temp').innerText = `${data.machine_state.temperature.toFixed(1)}°C`;
            if (document.getElementById('m-vib')) document.getElementById('m-vib').innerText = data.machine_state.vibration.toFixed(2);
            if (document.getElementById('m-rpm')) document.getElementById('m-rpm').innerText = data.machine_state.rpm.toFixed(0);
        }
        if (document.getElementById('m-anomaly')) document.getElementById('m-anomaly').innerText = `${(data.anomaly_score * 100).toFixed(1)}%`;
        if (document.getElementById('m-wear')) document.getElementById('m-wear').innerText = `${(data.wear_level * 100).toFixed(4)}%`;

        // Update Chart
        if (chart) {
            const historyRes = await fetch(`${API_BASE}/history`);
            const history = await historyRes.json();
            
            if (history && history.length > 0) {
                chart.data.labels = history.map(h => {
                    const d = new Date(h.timestamp * 1000);
                    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                });
                chart.data.datasets[0].data = history.map(h => h.temperature);
                chart.data.datasets[1].data = history.map(h => h.vibration * 10);
                chart.data.datasets[2].data = history.map(h => h.risk_score * 100);
                chart.update('none');
            }
        }

    } catch (e) {
        console.error("Dashboard update failed", e);
    }
}

async function trigger(type) {
    await fetch(`${API_BASE}/control/trigger?type=${type}`, { method: 'POST' });
}

const loadSlider = document.getElementById('load-slider');
if (loadSlider) {
    loadSlider.addEventListener('input', async (e) => {
        const val = e.target.value;
        const loadValDisp = document.getElementById('load-value');
        if (loadValDisp) loadValDisp.innerText = `${(val * 100).toFixed(0)}%`;
        await fetch(`${API_BASE}/control/load?value=${val}`, { method: 'POST' });
    });
}

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    setInterval(updateDashboard, 1000);
    updateDashboard();
});
