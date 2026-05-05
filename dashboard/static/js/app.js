/* ═══════════════════════════════════════════════════════════════════════
   ProTrack — Dashboard Application Logic (Gen Z Edition)
   ═══════════════════════════════════════════════════════════════════════ */

// ── Constants ─────────────────────────────────────────────────────────
const DAILY_GOAL_HOURS = 5;
const DAILY_GOAL_SECONDS = DAILY_GOAL_HOURS * 3600;

// ── Socket.IO Connection ──────────────────────────────────────────────
const socket = io({
    transports: ['polling'],
});
let isConnected = false;
let lastKnownTotalSeconds = 0;
let lastKnownProductiveSeconds = 0;
let lastStatusTimestamp = 0;
let lastKnownVdiActive = false;
let lastKnownState = 'idle';

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

// ── Initialize ────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    createHourlyChart('hourly-chart');
    createDistributionChart('distribution-chart');
    createTrendChart('trend-chart');
    createVdiComparisonChart('vdi-comparison-chart');
    createInputHeatmap('input-heatmap');

    injectGaugeGradient();
    updateGreeting();
    updateClock();
    setInterval(updateClock, 1000);
    setInterval(tickLiveTimer, 1000);

    fetchTodayData();
    fetchTrendData(7);
    fetchIntervals();
    fetchInsights();

    setInterval(() => {
        fetchTodayData();
        fetchIntervals();
        fetchInsights();
    }, 30000);

    // Update greeting every minute
    setInterval(updateGreeting, 60000);

    document.querySelectorAll('.trend-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.trend-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            fetchTrendData(parseInt(e.target.dataset.days, 10));
        });
    });
});

// ── Real-Time Events ──────────────────────────────────────────────────
socket.on('interval_update', (data) => {
    if (data.status) updateStatusCards(data.status);
    if (data.interval) prependTimelineItem(data.interval);
    fetchTodayData();
    fetchIntervals();
    fetchInsights();
});

socket.on('status_update', (data) => {
    updateStatusCards(data);
});

// ── Greeting & Motivation ─────────────────────────────────────────────
function updateGreeting() {
    const hour = new Date().getHours();
    let greeting, emoji;
    if (hour < 6) { greeting = 'Night owl mode'; emoji = '🦉'; }
    else if (hour < 12) { greeting = 'Good morning'; emoji = '☀️'; }
    else if (hour < 17) { greeting = 'Good afternoon'; emoji = '🚀'; }
    else if (hour < 21) { greeting = 'Good evening'; emoji = '🌆'; }
    else { greeting = 'Burning midnight oil'; emoji = '🌙'; }

    const el = document.getElementById('hero-greeting');
    const wave = document.getElementById('hero-wave');
    if (el) el.textContent = `${greeting}!`;
    if (wave) wave.textContent = emoji;
}

function getGoalMessage(pct) {
    if (pct >= 100) return "YOU DID IT! 5 hours smashed! 🏆🎉";
    if (pct >= 80) return "Almost there — push through! 💎";
    if (pct >= 60) return "Over halfway! You're cooking 🔥";
    if (pct >= 40) return "Great momentum — keep it locked in 💪";
    if (pct >= 20) return "Building up steam — let's gooo 🚂";
    if (pct > 0) return "You've started — that's the hardest part ✨";
    return "Let's crush your 5-hour goal today 🔥";
}

// ── Data Fetchers ─────────────────────────────────────────────────────
async function fetchTodayData() {
    try {
        const res = await fetch('/api/today');
        const data = await res.json();

        updateStatusCards(data);
        if (data.hourly_breakdown) {
            updateHourlyChart(data.hourly_breakdown);
            updateDistributionChart(data.hourly_breakdown);
        }
    } catch (e) {
        console.error('Error fetching today data:', e);
    }
}

async function fetchTrendData(days) {
    try {
        const end = new Date().toISOString().split('T')[0];
        const start = new Date(Date.now() - days * 86400000).toISOString().split('T')[0];
        const res = await fetch(`/api/daily?start=${start}&end=${end}`);
        const data = await res.json();
        if (data.summaries) updateTrendChart(data.summaries);
    } catch (e) {
        console.error('Error fetching trend data:', e);
    }
}

async function fetchIntervals() {
    try {
        const today = new Date().toISOString().split('T')[0];
        const res = await fetch(`/api/intervals?date=${today}&limit=50`);
        const data = await res.json();
        if (data.intervals) updateTimeline(data.intervals);
    } catch (e) {
        console.error('Error fetching intervals:', e);
    }
}

async function fetchInsights() {
    try {
        const today = new Date().toISOString().split('T')[0];
        const res = await fetch(`/api/insights/${today}`);
        const data = await res.json();
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
    // Track for live timer
    if (status.total_seconds !== undefined) {
        lastKnownTotalSeconds = status.total_seconds;
        lastStatusTimestamp = Date.now();
    }
    if (status.productive_seconds !== undefined) {
        lastKnownProductiveSeconds = status.productive_seconds;
    }
    if (status.vdi_active !== undefined) {
        lastKnownVdiActive = status.vdi_active;
    }
    if (status.current_state) {
        lastKnownState = status.current_state;
    }

    // Current State
    const badge = document.getElementById('state-badge');
    if (badge && status.current_state) {
        badge.className = `state-badge ${status.current_state}`;
        badge.textContent = formatState(status.current_state);
    }

    // VDI Status
    const vdiEl = document.getElementById('qs-vdi-val');
    if (vdiEl) vdiEl.textContent = status.vdi_active ? '✅ Active' : '⚪ Off';

    // Efficiency
    const effEl = document.getElementById('qs-efficiency-val');
    if (effEl && status.efficiency !== undefined) effEl.textContent = `${Math.round(status.efficiency)}%`;

    // Streak
    const streakEl = document.getElementById('current-streak');
    if (streakEl && status.current_streak !== undefined) streakEl.textContent = status.current_streak;
    const heroStreak = document.getElementById('hero-streak-count');
    if (heroStreak && status.max_streak !== undefined) heroStreak.textContent = status.max_streak;

    // Interruptions
    const intEl = document.getElementById('interruptions');
    if (intEl && status.interruptions !== undefined) intEl.textContent = status.interruptions;

    // Total Tracked
    if (status.total_seconds !== undefined) {
        const totalEl = document.getElementById('total-tracked');
        if (totalEl) totalEl.textContent = formatDuration(status.total_seconds);
    }

    // Hidden elements (backward compat)
    const prodEl = document.getElementById('productive-hours');
    if (prodEl && status.productive_hours) prodEl.textContent = status.productive_hours;
    const vdiStatus = document.getElementById('vdi-status');
    if (vdiStatus) vdiStatus.textContent = status.vdi_active ? '✅ Active' : '⚪ Inactive';
    const effPct = document.getElementById('efficiency-pct');
    if (effPct && status.efficiency !== undefined) effPct.textContent = `${Math.round(status.efficiency)}%`;
    const rollEl = document.getElementById('rolling-score');
    if (rollEl && status.rolling_score !== undefined) rollEl.textContent = status.rolling_score.toFixed(2);
    const maxStreak = document.getElementById('max-streak');
    if (maxStreak && status.max_streak !== undefined) maxStreak.textContent = status.max_streak;

    // Update the 5-hour goal ring
    updateGoalRing(status.productive_seconds || lastKnownProductiveSeconds);
}

function updateGoalRing(productiveSeconds) {
    const pct = Math.min((productiveSeconds / DAILY_GOAL_SECONDS) * 100, 100);
    const circumference = 2 * Math.PI * 85; // r=85

    // Ring fill
    const ring = document.getElementById('goal-ring-fill');
    if (ring) {
        const offset = circumference - (pct / 100) * circumference;
        ring.style.strokeDashoffset = offset;
    }

    // Time display
    const timeEl = document.getElementById('goal-time');
    if (timeEl) timeEl.textContent = formatDuration(productiveSeconds);

    // Hidden element
    const ttEl = document.getElementById('insight-total-time-val');
    if (ttEl) ttEl.textContent = formatDuration(productiveSeconds);

    // Percentage badge
    const badge = document.getElementById('goal-pct-badge');
    if (badge) {
        badge.textContent = `${Math.round(pct)}%`;
        badge.className = 'goal-pct-badge';
        if (pct >= 100) badge.classList.add('done');
        else if (pct >= 60) badge.classList.add('hot');
    }

    // Motivational status
    const statusEl = document.getElementById('goal-status');
    if (statusEl) statusEl.textContent = getGoalMessage(pct);

    // Update motto
    const mottoEl = document.getElementById('hero-motto');
    if (mottoEl) {
        if (pct >= 100) mottoEl.textContent = "5-hour goal achieved! You're a legend 👑";
        else if (pct >= 60) mottoEl.textContent = "You're on fire — don't stop now 🔥";
        else mottoEl.textContent = getGoalMessage(pct);
    }
}

function updateInsightCards(data) {
    // VDI Focus Ratio
    if (data.vdi_stats) {
        const v = data.vdi_stats;
        const pct = v.vdi_percentage || 0;
        const fill = document.getElementById('vdi-progress-fill');
        const pctEl = document.getElementById('insight-vdi-pct');
        if (fill) fill.style.width = `${Math.min(pct, 100)}%`;
        if (pctEl) pctEl.textContent = `${Math.round(pct)}%`;
        const sub = document.getElementById('insight-vdi-sub');
        if (sub) sub.textContent = `${formatDurationShort(v.vdi_seconds)} VDI · ${formatDurationShort(v.total_seconds)} total`;
    }

    // Peak Hour
    if (data.peak_hour && data.peak_weight > 0) {
        const h = parseInt(data.peak_hour, 10);
        const phEl = document.getElementById('insight-peak-val');
        if (phEl) phEl.textContent = `${h.toString().padStart(2, '0')}:00 – ${(h + 1).toString().padStart(2, '0')}:00`;
        const phSub = document.getElementById('insight-peak-sub');
        if (phSub) phSub.textContent = `Score: ${(data.peak_weight * 100).toFixed(0)}% productivity`;
    } else {
        const phEl = document.getElementById('insight-peak-val');
        if (phEl) phEl.textContent = '—';
    }

    // Deep Work
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

// ── Connection Status ─────────────────────────────────────────────────
function updateConnectionStatus(connected) {
    const el = document.getElementById('tracking-status');
    if (!el) return;
    if (connected) {
        el.className = 'tracking-status';
        el.innerHTML = '<span class="status-dot"></span><span class="status-text">Tracking Active</span>';
    } else {
        el.className = 'tracking-status disconnected';
        el.innerHTML = '<span class="status-dot"></span><span class="status-text">Disconnected</span>';
    }
}

// ── Clock ─────────────────────────────────────────────────────────────
function updateClock() {
    const el = document.getElementById('header-datetime');
    if (el) {
        const now = new Date();
        el.textContent = now.toLocaleDateString('en-US', {
            weekday: 'short', month: 'short', day: 'numeric',
        }) + ' · ' + now.toLocaleTimeString('en-US', {
            hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
        });
    }
}

// ── Timeline ──────────────────────────────────────────────────────────
function updateTimeline(intervals) {
    const body = document.getElementById('timeline-body');
    const countEl = document.getElementById('timeline-count');
    if (!body) return;

    if (!intervals || intervals.length === 0) {
        body.innerHTML = '<div class="timeline-empty"><span class="empty-icon">📡</span><p>Waiting for data...</p><p class="empty-sub">Intervals appear every 30 seconds</p></div>';
        if (countEl) countEl.textContent = '0 intervals';
        return;
    }

    if (countEl) countEl.textContent = `${intervals.length} interval${intervals.length !== 1 ? 's' : ''}`;
    body.innerHTML = intervals.map(iv => createTimelineHTML(iv)).join('');
}

function prependTimelineItem(interval) {
    const body = document.getElementById('timeline-body');
    if (!body) return;
    const empty = body.querySelector('.timeline-empty');
    if (empty) empty.remove();
    body.insertAdjacentHTML('afterbegin', createTimelineHTML(interval));
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

// ── Live Timer ────────────────────────────────────────────────────────
function tickLiveTimer() {
    if (lastKnownTotalSeconds <= 0 || lastStatusTimestamp <= 0) return;

    if (!lastKnownVdiActive) {
        const totalEl = document.getElementById('total-tracked');
        if (totalEl) totalEl.textContent = formatDuration(lastKnownTotalSeconds) + ' ⏸️';
        return;
    }

    const elapsed = Math.floor((Date.now() - lastStatusTimestamp) / 1000);
    const currentTotal = lastKnownTotalSeconds + elapsed;

    // Only extrapolate productive time when actually in a productive state
    const isProductive = (lastKnownState === 'active' || lastKnownState === 'high_focus');
    const currentProductive = isProductive
        ? lastKnownProductiveSeconds + elapsed
        : lastKnownProductiveSeconds;

    const totalEl = document.getElementById('total-tracked');
    if (totalEl) {
        const hrs = Math.floor(currentTotal / 3600);
        const mins = Math.floor((currentTotal % 3600) / 60);
        const secs = currentTotal % 60;
        totalEl.textContent = `${hrs}h ${mins.toString().padStart(2, '0')}m ${secs.toString().padStart(2, '0')}s`;
    }

    // Live goal ring update
    updateGoalRing(currentProductive);
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

function setAnimatedValue(id, value) {
    const el = document.getElementById(id);
    if (!el) return;
    const current = parseInt(el.textContent, 10) || 0;
    if (current === value) return;
    el.textContent = value.toLocaleString();
}

function injectGaugeGradient() {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.id = 'gauge-gradient-svg';
    svg.innerHTML = '<defs><linearGradient id="gauge-grad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#ef4444"/><stop offset="50%" stop-color="#f59e0b"/><stop offset="100%" stop-color="#10b981"/></linearGradient></defs>';
    document.body.appendChild(svg);
}
