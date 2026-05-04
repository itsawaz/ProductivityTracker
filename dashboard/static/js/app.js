/* ═══════════════════════════════════════════════════════════════════════
   ProTrack — Dashboard Application Logic
   ═══════════════════════════════════════════════════════════════════════ */

// ── Socket.IO Connection (prefer WebSocket) ──────────────────────────
const socket = io({
    transports: ['websocket', 'polling'],
    upgrade: true,
});
let isConnected = false;
let lastKnownTotalSeconds = 0;
let lastStatusTimestamp = 0;
let lastKnownVdiActive = false;

socket.on('connect', () => {
    isConnected = true;
    console.log('✅ Connected to ProTrack server via', socket.io.engine.transport.name);
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
    createVdiComparisonChart('vdi-comparison-chart');
    createInputHeatmap('input-heatmap');

    // Add SVG gradient for gauge
    injectGaugeGradient();

    // Start clock + live timer
    updateClock();
    setInterval(updateClock, 1000);
    setInterval(tickLiveTimer, 1000);

    // Initial data fetch
    fetchTodayData();
    fetchTrendData(7);
    fetchIntervals();
    fetchInsights();

    // Periodic heavy refresh (charts + intervals every 30s)
    setInterval(() => {
        fetchTodayData();
        fetchIntervals();
        fetchInsights();
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
    if (data.status) updateStatusCards(data.status);
    if (data.interval) prependTimelineItem(data.interval);
    fetchTodayData();
    fetchIntervals();
    fetchInsights();
});

socket.on('status_update', (data) => {
    // Live status pushed every 5 seconds from the server
    updateStatusCards(data);
});

// ── API Fetchers ──────────────────────────────────────────────────────
async function fetchTodayData() {
    try {
        const res = await fetch('/api/today');
        const data = await res.json();
        updateStatusCards(data);
        if (data.hourly_breakdown) updateHourlyChart(data.hourly_breakdown);
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
        if (data.summaries) updateTrendChart(data.summaries);
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

async function fetchInsights() {
    try {
        const today = new Date().toISOString().slice(0, 10);
        const res = await fetch(`/api/insights/${today}`);
        const data = await res.json();
        if (data.error) return;
        updateInsightCards(data);
        if (data.vdi_stats && data.vdi_stats.hourly_vdi) {
            updateVdiComparisonChart(data.vdi_stats.hourly_vdi);
        }
        if (data.input_totals && data.input_totals.hourly_input) {
            updateInputHeatmap(data.input_totals.hourly_input);
        }
    } catch (e) {
        console.error('Error fetching insights:', e);
    }
}

// ── UI Updaters ───────────────────────────────────────────────────────

function updateStatusCards(status) {
    // Track the last known total for the live timer
    if (status.total_seconds !== undefined) {
        lastKnownTotalSeconds = status.total_seconds;
        lastStatusTimestamp = Date.now();
    }
    if (status.vdi_active !== undefined) {
        lastKnownVdiActive = status.vdi_active;
    }

    // Current State
    const badge = document.getElementById('state-badge');
    if (badge && status.current_state) {
        badge.className = `state-badge ${status.current_state}`;
        badge.textContent = formatState(status.current_state);
    }

    // VDI Status
    const vdiEl = document.getElementById('vdi-status');
    if (vdiEl) vdiEl.textContent = `VDI: ${status.vdi_active ? '✅ Active' : '⚪ Inactive'}`;

    // Productive Hours
    const prodEl = document.getElementById('productive-hours');
    if (prodEl && status.productive_hours) prodEl.textContent = status.productive_hours;

    // Total Tracked
    const totalEl = document.getElementById('total-tracked');
    if (totalEl && status.total_seconds !== undefined) {
        const hrs = Math.floor(status.total_seconds / 3600);
        const mins = Math.floor((status.total_seconds % 3600) / 60);
        totalEl.textContent = `Total: ${hrs}h ${mins.toString().padStart(2, '0')}m tracked`;
    }

    // Efficiency
    const effEl = document.getElementById('efficiency-pct');
    if (effEl && status.efficiency !== undefined) effEl.textContent = `${Math.round(status.efficiency)}%`;
    updateGauge(status.efficiency || 0);

    // Rolling Score
    const rollEl = document.getElementById('rolling-score');
    if (rollEl && status.rolling_score !== undefined) rollEl.textContent = `Rolling: ${status.rolling_score.toFixed(2)}`;

    // Focus Streak
    const streakEl = document.getElementById('current-streak');
    if (streakEl && status.current_streak !== undefined) streakEl.textContent = status.current_streak;

    const maxEl = document.getElementById('max-streak');
    if (maxEl && status.max_streak !== undefined) maxEl.textContent = `Best today: ${status.max_streak}`;

    const intEl = document.getElementById('interruptions');
    if (intEl && status.interruptions !== undefined) intEl.textContent = `Interruptions: ${status.interruptions}`;

    // Also update the total-time insight card from real-time status
    if (status.total_seconds !== undefined) {
        const ttEl = document.getElementById('insight-total-time-val');
        if (ttEl) ttEl.textContent = formatDuration(status.total_seconds);
    }
    if (status.vdi_percentage !== undefined) {
        const vpEl = document.getElementById('insight-vdi-pct');
        const vpFill = document.getElementById('vdi-progress-fill');
        if (vpEl) vpEl.textContent = `${Math.round(status.vdi_percentage)}%`;
        if (vpFill) vpFill.style.width = `${Math.min(status.vdi_percentage, 100)}%`;
    }
    if (status.idle_seconds !== undefined && status.total_seconds) {
        const idlePct = status.total_seconds > 0 ? (status.idle_seconds / status.total_seconds * 100) : 0;
        const ipEl = document.getElementById('insight-idle-pct');
        const ipFill = document.getElementById('idle-progress-fill');
        if (ipEl) ipEl.textContent = `${Math.round(idlePct)}%`;
        if (ipFill) ipFill.style.width = `${Math.min(idlePct, 100)}%`;
        const iSub = document.getElementById('insight-idle-sub');
        if (iSub) iSub.textContent = `${formatDurationShort(status.idle_seconds)} idle of ${formatDurationShort(status.total_seconds)} total`;
    }
}

function updateInsightCards(data) {
    // Total Time Worked
    if (data.totals) {
        const ttEl = document.getElementById('insight-total-time-val');
        if (ttEl) ttEl.textContent = formatDuration(data.totals.total_seconds);
        const ttSub = document.getElementById('insight-total-time-sub');
        if (ttSub) {
            const prodHrs = formatDurationShort(data.totals.productive_seconds);
            ttSub.textContent = `${prodHrs} productive`;
        }
    }

    // VDI Focus Ratio
    if (data.vdi_stats) {
        const vs = data.vdi_stats;
        const vpEl = document.getElementById('insight-vdi-pct');
        const vpFill = document.getElementById('vdi-progress-fill');
        if (vpEl) vpEl.textContent = `${Math.round(vs.vdi_percentage)}%`;
        if (vpFill) vpFill.style.width = `${Math.min(vs.vdi_percentage, 100)}%`;
        const vSub = document.getElementById('insight-vdi-sub');
        if (vSub) vSub.textContent = `${formatDurationShort(vs.vdi_seconds)} VDI · ${formatDurationShort(vs.total_seconds)} total`;
    }

    // Peak Hour
    if (data.peak_hour !== null && data.peak_hour !== undefined) {
        const phEl = document.getElementById('insight-peak-val');
        const h = parseInt(data.peak_hour, 10);
        if (phEl) phEl.textContent = `${h.toString().padStart(2, '0')}:00 – ${(h + 1).toString().padStart(2, '0')}:00`;
        const phSub = document.getElementById('insight-peak-sub');
        if (phSub) phSub.textContent = `Score: ${(data.peak_weight * 100).toFixed(0)}% productivity`;
    } else {
        const phEl = document.getElementById('insight-peak-val');
        if (phEl) phEl.textContent = '—';
    }

    // Deep Work Sessions
    if (data.deep_work) {
        const dw = data.deep_work;
        const dwEl = document.getElementById('insight-deep-val');
        if (dwEl) dwEl.textContent = `${dw.session_count} session${dw.session_count !== 1 ? 's' : ''}`;
        const dwSub = document.getElementById('insight-deep-sub');
        if (dwSub) {
            if (dw.session_count > 0) {
                dwSub.textContent = `${dw.total_duration_minutes}m total · ${dw.longest_session_minutes}m longest`;
            } else {
                dwSub.textContent = 'No sustained focus blocks yet';
            }
        }
    }

    // Idle Time
    if (data.totals) {
        const t = data.totals;
        const idlePct = t.total_seconds > 0 ? (t.idle_seconds / t.total_seconds * 100) : 0;
        const ipEl = document.getElementById('insight-idle-pct');
        const ipFill = document.getElementById('idle-progress-fill');
        if (ipEl) ipEl.textContent = `${Math.round(idlePct)}%`;
        if (ipFill) ipFill.style.width = `${Math.min(idlePct, 100)}%`;
        const iSub = document.getElementById('insight-idle-sub');
        if (iSub) iSub.textContent = `${formatDurationShort(t.idle_seconds)} idle of ${formatDurationShort(t.total_seconds)} total`;
    }

    // Input Stats
    if (data.input_totals) {
        const inp = data.input_totals;
        setAnimatedValue('input-keys', inp.total_keys);
        setAnimatedValue('input-clicks', inp.total_clicks);
        setAnimatedValue('input-scrolls', inp.total_scrolls);
        setAnimatedValue('input-moves', inp.total_mouse_moves);
    }
}

function updateGauge(efficiency) {
    const gaugeFill = document.getElementById('gauge-fill');
    if (!gaugeFill) return;
    const circumference = 2 * Math.PI * 40;
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
            </div>`;
        if (count) count.textContent = '0 intervals';
        return;
    }
    body.innerHTML = intervals.map(iv => createTimelineHTML(iv)).join('');
    if (count) count.textContent = `${intervals.length} intervals`;
}

function prependTimelineItem(interval) {
    const body = document.getElementById('timeline-body');
    if (!body) return;
    const empty = body.querySelector('.timeline-empty');
    if (empty) body.innerHTML = '';
    body.insertAdjacentHTML('afterbegin', createTimelineHTML(interval));
    while (body.children.length > 50) body.removeChild(body.lastChild);
    const count = document.getElementById('timeline-count');
    if (count) count.textContent = `${body.children.length} intervals`;
}

function createTimelineHTML(iv) {
    const state = iv.activity_state || 'idle';
    const time = iv.timestamp ? new Date(iv.timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    }) : '--:--:--';
    const weight = (iv.adjusted_weight || 0);
    const pct = Math.round(weight * 100);
    const productive = (iv.productive_seconds || 0).toFixed(0);
    const vdiIcon = iv.vdi_active ? '🟢' : '⚪';
    const totalEvents = iv.total_events || 0;

    return `
        <div class="timeline-item">
            <div class="timeline-dot ${state}"></div>
            <span class="timeline-time">${time}</span>
            <span class="timeline-state ${state}">${formatState(state)}</span>
            <div class="timeline-events">
                <span title="VDI Status">${vdiIcon}</span>
                <span title="Keystrokes">⌨️${iv.key_count || 0}</span>
                <span title="Clicks">🖱️${iv.mouse_click_count || 0}</span>
                <span title="Scrolls">↕️${iv.scroll_count || 0}</span>
                <span title="Total Events">Σ${totalEvents}</span>
            </div>
            <div class="timeline-bar-wrap">
                <div class="timeline-bar">
                    <div class="timeline-bar-fill ${state}" style="width: ${pct}%"></div>
                </div>
                <span class="timeline-bar-label">${pct}%</span>
            </div>
            <span class="timeline-productive">${productive}s</span>
        </div>`;
}

// ── Live Timer (ticks every 1 second) ─────────────────────────────────

function tickLiveTimer() {
    if (lastKnownTotalSeconds <= 0 || lastStatusTimestamp <= 0) return;

    // Only tick the timer when VDI is active
    if (!lastKnownVdiActive) {
        // Show paused state
        const totalEl = document.getElementById('total-tracked');
        if (totalEl) {
            const hrs = Math.floor(lastKnownTotalSeconds / 3600);
            const mins = Math.floor((lastKnownTotalSeconds % 3600) / 60);
            totalEl.textContent = `Total: ${hrs}h ${mins.toString().padStart(2, '0')}m (paused)`;
        }
        return;
    }

    // Calculate elapsed since last server status push
    const elapsed = Math.floor((Date.now() - lastStatusTimestamp) / 1000);
    const currentTotal = lastKnownTotalSeconds + elapsed;

    // Update "Total Time Worked" insight card
    const ttEl = document.getElementById('insight-total-time-val');
    if (ttEl) ttEl.textContent = formatDuration(currentTotal);

    // Update "Total: Xh Ym tracked" in stats card
    const totalEl = document.getElementById('total-tracked');
    if (totalEl) {
        const hrs = Math.floor(currentTotal / 3600);
        const mins = Math.floor((currentTotal % 3600) / 60);
        const secs = currentTotal % 60;
        totalEl.textContent = `Total: ${hrs}h ${mins.toString().padStart(2, '0')}m ${secs.toString().padStart(2, '0')}s`;
    }
}

// ── Helpers ───────────────────────────────────────────────────────────

function formatState(state) {
    const names = { 'idle': 'Idle', 'passive': 'Passive', 'active': 'Active', 'high_focus': 'High Focus' };
    return names[state] || state;
}

function formatDuration(seconds) {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${hrs}h ${mins.toString().padStart(2, '0')}m`;
}

function formatDurationShort(seconds) {
    if (seconds >= 3600) {
        const hrs = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        return `${hrs}h ${mins}m`;
    }
    return `${Math.floor(seconds / 60)}m`;
}

function setAnimatedValue(elementId, value) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const display = value > 9999 ? `${(value / 1000).toFixed(1)}k` : value.toLocaleString();
    el.textContent = display;
}

function updateClock() {
    const el = document.getElementById('header-datetime');
    if (!el) return;
    el.textContent = new Date().toLocaleString('en-US', {
        weekday: 'short', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
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
        if (text) { text.textContent = 'Tracking Active'; text.style.color = '#10b981'; }
    } else {
        status.style.borderColor = 'rgba(239, 68, 68, 0.2)';
        status.style.background = 'rgba(239, 68, 68, 0.1)';
        if (dot) dot.style.background = '#ef4444';
        if (text) { text.textContent = 'Disconnected'; text.style.color = '#ef4444'; }
    }
}

function injectGaugeGradient() {
    const svg = document.querySelector('.gauge-ring');
    if (!svg) return;
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
    gradient.setAttribute('id', 'gauge-gradient');
    gradient.setAttribute('x1', '0%'); gradient.setAttribute('y1', '0%');
    gradient.setAttribute('x2', '100%'); gradient.setAttribute('y2', '100%');
    const stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    stop1.setAttribute('offset', '0%'); stop1.setAttribute('stop-color', '#3b82f6');
    const stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    stop2.setAttribute('offset', '100%'); stop2.setAttribute('stop-color', '#8b5cf6');
    gradient.appendChild(stop1); gradient.appendChild(stop2);
    defs.appendChild(gradient);
    svg.insertBefore(defs, svg.firstChild);
}
