/* ═══════════════════════════════════════════════════════════════════════
   ProTrack — Dashboard Application Logic
   ═══════════════════════════════════════════════════════════════════════ */

// ── Socket.IO Connection ──────────────────────────────────────────────
const socket = io();
let isConnected = false;

socket.on('connect', () => {
    isConnected = true;
    console.log('✅ Connected to ProTrack server');
    updateConnectionStatus(true);
});

socket.on('disconnect', () => {
    isConnected = false;
    console.log('❌ Disconnected from ProTrack server');
    updateConnectionStatus(false);
});

// ── Initialize Charts ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Create charts
    createHourlyChart('hourly-chart');
    createDistributionChart('distribution-chart');
    createTrendChart('trend-chart');

    // Add SVG gradient for gauge (needs to be in DOM)
    injectGaugeGradient();

    // Start clock
    updateClock();
    setInterval(updateClock, 1000);

    // Initial data fetch
    fetchTodayData();
    fetchTrendData(7);
    fetchIntervals();

    // Periodic refresh (every 30s to stay in sync)
    setInterval(() => {
        fetchTodayData();
        fetchIntervals();
    }, 30000);

    // Trend button handlers
    document.querySelectorAll('.trend-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.trend-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            fetchTrendData(parseInt(e.target.dataset.days, 10));
        });
    });
});

// ── Real-Time Event Handlers ──────────────────────────────────────────
socket.on('interval_update', (data) => {
    console.log('📊 Interval update:', data);

    if (data.status) {
        updateStatusCards(data.status);
    }
    if (data.interval) {
        prependTimelineItem(data.interval);
    }

    // Refresh charts with latest data
    fetchTodayData();
    fetchIntervals();
});

socket.on('status_update', (data) => {
    updateStatusCards(data);
});

// ── API Fetchers ──────────────────────────────────────────────────────
async function fetchTodayData() {
    try {
        const res = await fetch('/api/today');
        const data = await res.json();

        updateStatusCards(data);

        if (data.hourly_breakdown) {
            updateHourlyChart(data.hourly_breakdown);
        }
    } catch (e) {
        console.error('Error fetching today data:', e);
    }
}

async function fetchTrendData(days) {
    try {
        const end = new Date().toISOString().slice(0, 10);
        const start = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);

        const res = await fetch(`/api/daily?start=${start}&end=${end}`);
        const data = await res.json();

        if (data.summaries) {
            updateTrendChart(data.summaries);
        }
    } catch (e) {
        console.error('Error fetching trend data:', e);
    }
}

async function fetchIntervals() {
    try {
        const today = new Date().toISOString().slice(0, 10);
        const res = await fetch(`/api/intervals?date=${today}&limit=50`);
        const data = await res.json();

        if (data.intervals) {
            updateTimeline(data.intervals);
            updateDistributionChart(data.intervals);
        }
    } catch (e) {
        console.error('Error fetching intervals:', e);
    }
}

// ── UI Updaters ───────────────────────────────────────────────────────

function updateStatusCards(status) {
    // Current State
    const badge = document.getElementById('state-badge');
    if (badge && status.current_state) {
        const state = status.current_state;
        badge.className = `state-badge ${state}`;
        badge.textContent = formatState(state);
    }

    // VDI Status
    const vdiEl = document.getElementById('vdi-status');
    if (vdiEl) {
        vdiEl.textContent = `VDI: ${status.vdi_active ? '✅ Active' : '⚪ Inactive'}`;
    }

    // Productive Hours
    const prodEl = document.getElementById('productive-hours');
    if (prodEl && status.productive_hours) {
        prodEl.textContent = status.productive_hours;
    }

    // Total Tracked
    const totalEl = document.getElementById('total-tracked');
    if (totalEl && status.total_seconds !== undefined) {
        const hrs = Math.floor(status.total_seconds / 3600);
        const mins = Math.floor((status.total_seconds % 3600) / 60);
        totalEl.textContent = `Total: ${hrs}h ${mins.toString().padStart(2, '0')}m tracked`;
    }

    // Efficiency
    const effEl = document.getElementById('efficiency-pct');
    if (effEl && status.efficiency !== undefined) {
        effEl.textContent = `${Math.round(status.efficiency)}%`;
    }

    // Gauge ring
    updateGauge(status.efficiency || 0);

    // Rolling Score
    const rollEl = document.getElementById('rolling-score');
    if (rollEl && status.rolling_score !== undefined) {
        rollEl.textContent = `Rolling: ${status.rolling_score.toFixed(2)}`;
    }

    // Focus Streak
    const streakEl = document.getElementById('current-streak');
    if (streakEl && status.current_streak !== undefined) {
        streakEl.textContent = status.current_streak;
    }

    const maxEl = document.getElementById('max-streak');
    if (maxEl && status.max_streak !== undefined) {
        maxEl.textContent = `Best today: ${status.max_streak}`;
    }

    const intEl = document.getElementById('interruptions');
    if (intEl && status.interruptions !== undefined) {
        intEl.textContent = `Interruptions: ${status.interruptions}`;
    }
}

function updateGauge(efficiency) {
    const gaugeFill = document.getElementById('gauge-fill');
    if (!gaugeFill) return;

    const circumference = 2 * Math.PI * 40; // r=40
    const pct = Math.min(efficiency, 100) / 100;
    const offset = circumference * (1 - pct);
    gaugeFill.style.strokeDasharray = circumference;
    gaugeFill.style.strokeDashoffset = offset;
}

function updateTimeline(intervals) {
    const body = document.getElementById('timeline-body');
    const count = document.getElementById('timeline-count');
    if (!body) return;

    if (intervals.length === 0) {
        body.innerHTML = `
            <div class="timeline-empty">
                <span class="empty-icon">📡</span>
                <p>Waiting for data...</p>
                <p class="empty-sub">Intervals will appear here every 30 seconds</p>
            </div>
        `;
        if (count) count.textContent = '0 intervals';
        return;
    }

    body.innerHTML = intervals.map(iv => createTimelineHTML(iv)).join('');
    if (count) count.textContent = `${intervals.length} intervals`;
}

function prependTimelineItem(interval) {
    const body = document.getElementById('timeline-body');
    if (!body) return;

    // Remove empty state if present
    const empty = body.querySelector('.timeline-empty');
    if (empty) body.innerHTML = '';

    const html = createTimelineHTML(interval);
    body.insertAdjacentHTML('afterbegin', html);

    // Keep max 50 items
    while (body.children.length > 50) {
        body.removeChild(body.lastChild);
    }

    const count = document.getElementById('timeline-count');
    if (count) count.textContent = `${body.children.length} intervals`;
}

function createTimelineHTML(iv) {
    const state = iv.activity_state || 'idle';
    const time = iv.timestamp ? new Date(iv.timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    }) : '--:--:--';

    const weight = (iv.adjusted_weight || 0).toFixed(2);
    const productive = (iv.productive_seconds || 0).toFixed(1);

    return `
        <div class="timeline-item">
            <div class="timeline-dot ${state}"></div>
            <span class="timeline-time">${time}</span>
            <span class="timeline-state ${state}">${formatState(state)}</span>
            <div class="timeline-events">
                <span>⌨️ ${iv.key_count || 0}</span>
                <span>🖱️ ${iv.mouse_click_count || 0}</span>
                <span>↕️ ${iv.scroll_count || 0}</span>
                <span>📏 ${iv.mouse_move_count || 0}</span>
            </div>
            <span class="timeline-weight">${weight}</span>
            <span class="timeline-productive">${productive}s</span>
        </div>
    `;
}

// ── Helpers ───────────────────────────────────────────────────────────

function formatState(state) {
    const names = {
        'idle': 'Idle',
        'passive': 'Passive',
        'active': 'Active',
        'high_focus': 'High Focus',
    };
    return names[state] || state;
}

function updateClock() {
    const el = document.getElementById('header-datetime');
    if (!el) return;
    const now = new Date();
    el.textContent = now.toLocaleString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false,
    });
}

function updateConnectionStatus(connected) {
    const status = document.getElementById('tracking-status');
    if (!status) return;
    const dot = status.querySelector('.status-dot');
    const text = status.querySelector('.status-text');

    if (connected) {
        status.style.borderColor = 'rgba(16, 185, 129, 0.2)';
        status.style.background = 'rgba(16, 185, 129, 0.1)';
        if (dot) dot.style.background = '#10b981';
        if (text) {
            text.textContent = 'Tracking Active';
            text.style.color = '#10b981';
        }
    } else {
        status.style.borderColor = 'rgba(239, 68, 68, 0.2)';
        status.style.background = 'rgba(239, 68, 68, 0.1)';
        if (dot) dot.style.background = '#ef4444';
        if (text) {
            text.textContent = 'Disconnected';
            text.style.color = '#ef4444';
        }
    }
}

function injectGaugeGradient() {
    // Add SVG gradient definition for the gauge circle
    const svg = document.querySelector('.gauge-ring');
    if (!svg) return;

    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
    gradient.setAttribute('id', 'gauge-gradient');
    gradient.setAttribute('x1', '0%');
    gradient.setAttribute('y1', '0%');
    gradient.setAttribute('x2', '100%');
    gradient.setAttribute('y2', '100%');

    const stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    stop1.setAttribute('offset', '0%');
    stop1.setAttribute('stop-color', '#3b82f6');

    const stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    stop2.setAttribute('offset', '100%');
    stop2.setAttribute('stop-color', '#8b5cf6');

    gradient.appendChild(stop1);
    gradient.appendChild(stop2);
    defs.appendChild(gradient);
    svg.insertBefore(defs, svg.firstChild);
}
