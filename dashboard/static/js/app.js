// SVG Progress Ring calculations
const circle = document.getElementById('gauge-circle');
const radius = circle.r.baseVal.value;
const circumference = radius * 2 * Math.PI;

circle.style.strokeDasharray = `${circumference} ${circumference}`;
circle.style.strokeDashoffset = circumference;

function setProgress(percent) {
    const offset = circumference - (percent / 100 * circumference);
    circle.style.strokeDashoffset = offset;
    
    // Change gauge color based on percentage
    if (percent < 50) {
        circle.style.stroke = '#10B981'; // Green
    } else if (percent >= 50 && percent < 80) {
        circle.style.stroke = '#F59E0B'; // Yellow/Orange
    } else {
        circle.style.stroke = '#EF4444'; // Red
    }
}

// Request permission for push notifications
if (typeof Notification !== 'undefined') {
    if (Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

// Time display
function updateTime() {
    const timeEl = document.getElementById('live-time');
    const now = new Date();
    timeEl.textContent = now.toLocaleString();
}
setInterval(updateTime, 1000);
updateTime();

// Chart.js initialization
const ctx = document.getElementById('liveTrendChart').getContext('2d');
const maxDataPoints = 15;
const chartData = {
    labels: [],
    datasets: [
        {
            label: 'Fill Level (%)',
            data: [],
            borderColor: '#3B82F6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            borderWidth: 2,
            tension: 0.3,
            fill: true
        },
        {
            label: 'Gas Level (%)',
            data: [],
            borderColor: '#F59E0B',
            backgroundColor: 'transparent',
            borderWidth: 1.5,
            tension: 0.3
        }
    ]
};

const liveChart = new Chart(ctx, {
    type: 'line',
    data: chartData,
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                min: 0,
                max: 100,
                grid: { color: 'rgba(255, 255, 255, 0.05)' },
                ticks: { color: '#94A3B8' }
            },
            x: {
                grid: { color: 'rgba(255, 255, 255, 0.05)' },
                ticks: { color: '#94A3B8', maxRotation: 45, minRotation: 45 }
            }
        },
        plugins: {
            legend: {
                labels: { color: '#F8FAFC' }
            }
        }
    }
});

let wasAlertActive = false;

// Poll backend API
async function fetchTelemetry() {
    try {
        const response = await fetch('/api/data');
        if (!response.ok) throw new Error('API offline');
        
        const data = await response.json();
        
        // Update connections state
        document.getElementById('connection-status').className = 'status-indicator online';
        document.getElementById('connection-status').textContent = 'Online';

        // 1. Update Gauge & UI Labels
        const fill = data.fill_percentage;
        document.getElementById('level-value').textContent = `${fill}%`;
        setProgress(fill);

        // Update badge class
        const statusBadge = document.getElementById('status-badge');
        statusBadge.textContent = data.status.toUpperCase();
        statusBadge.className = 'badge';
        if (data.status === 'Empty') statusBadge.classList.add('empty');
        else if (data.status === 'Half Full') statusBadge.classList.add('half');
        else statusBadge.classList.add('full');

        // Update details
        document.getElementById('distance-value').textContent = `${data.distance} cm`;
        document.getElementById('gas-value').textContent = `${data.gas_level}%`;
        document.getElementById('temp-value').textContent = `${data.temp} °C`;
        document.getElementById('humidity-value').textContent = `${data.humidity} %`;

        // Odor descriptive mapping
        const gasIndicator = document.getElementById('gas-indicator');
        if (data.gas_level < 30) {
            gasIndicator.textContent = 'Low / Odorless';
            gasIndicator.style.color = '#10B981';
        } else if (data.gas_level >= 30 && data.gas_level < 60) {
            gasIndicator.textContent = 'Moderate Odor';
            gasIndicator.style.color = '#F59E0B';
        } else {
            gasIndicator.textContent = 'High Odor (Hazardous)';
            gasIndicator.style.color = '#EF4444';
        }

        // 2. Alert Box styling
        const notifBox = document.getElementById('notification-box');
        const alertText = document.getElementById('alert-text');
        
        if (data.alert_triggered) {
            notifBox.className = 'system-alerts-box';
            alertText.textContent = `🚨 Alert: Bin Node-1 is ${fill}% full! Dispatching garbage truck soon.`;
            
            // System Notification popup on transition
            if (!wasAlertActive && typeof Notification !== 'undefined' && Notification.permission === 'granted') {
                new Notification('⚠️ Smart Waste Alert', {
                    body: `Bin Node-1 is nearly full (${fill}%). Collection scheduled!`,
                    icon: 'https://cdn-icons-png.flaticon.com/512/1160/1160358.png'
                });
            }
            wasAlertActive = true;
        } else {
            notifBox.className = 'system-alerts-box normal';
            alertText.textContent = 'Monitoring active. Bin level is within safe limits.';
            wasAlertActive = false;
        }

        // 3. Update Chart
        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        
        // Add new data points
        chartData.labels.push(timestamp);
        chartData.datasets[0].data.push(fill);
        chartData.datasets[1].data.push(data.gas_level);

        // Shift old data points if exceeding limits
        if (chartData.labels.length > maxDataPoints) {
            chartData.labels.shift();
            chartData.datasets[0].data.shift();
            chartData.datasets[1].data.shift();
        }

        liveChart.update();

    } catch (error) {
        console.error('Telemetry fetch error:', error);
        document.getElementById('connection-status').className = 'status-indicator offline';
        document.getElementById('connection-status').textContent = 'Disconnected';
    }
}

// Set Simulation Mode
async function setSimMode(mode) {
    try {
        const response = await fetch('/api/set-mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: mode })
        });
        if (response.ok) {
            // Update button styles
            const buttons = document.querySelectorAll('.btn-grid .btn');
            buttons.forEach(btn => btn.classList.remove('active'));
            
            // Add active to the clicked mode button
            const modeBtnMap = {
                'empty': '.btn-empty',
                'half-full': '.btn-half',
                'nearly-full': '.btn-nearly',
                'full': '.btn-full',
                'dynamic': '#btn-dynamic'
            };
            document.querySelector(modeBtnMap[mode]).classList.add('active');
            
            // Clear chart to start fresh trend if manual mode changed
            if (mode !== 'dynamic') {
                chartData.labels = [];
                chartData.datasets[0].data = [];
                chartData.datasets[1].data = [];
                liveChart.update();
            }
        }
    } catch (error) {
        console.error('Error changing simulation mode:', error);
    }
}

// Start polling loop
setInterval(fetchTelemetry, 2500);
fetchTelemetry();
