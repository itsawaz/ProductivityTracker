/* ═══════════════════════════════════════════════════════════════════════
   ProTrack — Chart.js Configurations
   ═══════════════════════════════════════════════════════════════════════ */

// ── Color Palette ─────────────────────────────────────────────────────
const CHART_COLORS = {
    idle: { main: '#6b7280', bg: 'rgba(107, 114, 128, 0.5)' },
    passive: { main: '#f59e0b', bg: 'rgba(245, 158, 11, 0.5)' },
    active: { main: '#10b981', bg: 'rgba(16, 185, 129, 0.5)' },
    high_focus: { main: '#3b82f6', bg: 'rgba(59, 130, 246, 0.5)' },
    accent: '#8b5cf6',
    grid: 'rgba(255, 255, 255, 0.05)',
    text: '#94a3b8',
    textMuted: '#64748b',
};

// ── Chart.js Global Defaults ──────────────────────────────────────────
Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
Chart.defaults.color = CHART_COLORS.text;
Chart.defaults.responsive = true;
Chart.defaults.maintainAspectRatio = false;
Chart.defaults.animation = { duration: 600, easing: 'easeOutQuart' };

// ── Hourly Productivity Bar Chart ─────────────────────────────────────
let hourlyChart = null;

function createHourlyChart(canvasId) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    hourlyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`),
            datasets: [{
                label: 'Productivity',
                data: new Array(24).fill(0),
                backgroundColor: new Array(24).fill(CHART_COLORS.idle.bg),
                borderColor: new Array(24).fill(CHART_COLORS.idle.main),
                borderWidth: 1.5, borderRadius: 6, borderSkipped: false,
            }],
        },
        options: {
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(10, 14, 26, 0.95)',
                    borderColor: 'rgba(255, 255, 255, 0.1)', borderWidth: 1,
                    titleFont: { weight: '600' }, padding: 12, cornerRadius: 8,
                    displayColors: false,
                    callbacks: {
                        title: (items) => items[0].label,
                        label: (item) => `Productivity: ${(item.raw * 100).toFixed(0)}%`,
                    },
                },
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 10 }, maxRotation: 0,
                        callback: function(val, index) { return index % 3 === 0 ? this.getLabelForValue(val) : ''; }
                    },
                },
                y: {
                    beginAtZero: true, max: 1,
                    grid: { color: CHART_COLORS.grid },
                    ticks: { font: { size: 10 }, callback: (val) => `${(val * 100).toFixed(0)}%`, stepSize: 0.25 },
                },
            },
        },
    });
    return hourlyChart;
}

function updateHourlyChart(hourlyData) {
    if (!hourlyChart) return;
    const data = new Array(24).fill(0);
    const bgColors = new Array(24).fill(CHART_COLORS.idle.bg);
    const borderColors = new Array(24).fill(CHART_COLORS.idle.main);
    for (const [hour, info] of Object.entries(hourlyData)) {
        const h = parseInt(hour, 10);
        const weight = info.avg_weight || 0;
        data[h] = weight;
        if (weight >= 0.8) { bgColors[h] = CHART_COLORS.high_focus.bg; borderColors[h] = CHART_COLORS.high_focus.main; }
        else if (weight >= 0.5) { bgColors[h] = CHART_COLORS.active.bg; borderColors[h] = CHART_COLORS.active.main; }
        else if (weight > 0) { bgColors[h] = CHART_COLORS.passive.bg; borderColors[h] = CHART_COLORS.passive.main; }
    }
    hourlyChart.data.datasets[0].data = data;
    hourlyChart.data.datasets[0].backgroundColor = bgColors;
    hourlyChart.data.datasets[0].borderColor = borderColors;
    hourlyChart.update('none');
}

// ── Activity Distribution Doughnut Chart ──────────────────────────────
let distributionChart = null;

function createDistributionChart(canvasId) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    distributionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Idle', 'Passive', 'Active', 'High Focus'],
            datasets: [{
                data: [1, 0, 0, 0],
                backgroundColor: [CHART_COLORS.idle.bg, CHART_COLORS.passive.bg, CHART_COLORS.active.bg, CHART_COLORS.high_focus.bg],
                borderColor: [CHART_COLORS.idle.main, CHART_COLORS.passive.main, CHART_COLORS.active.main, CHART_COLORS.high_focus.main],
                borderWidth: 2, hoverOffset: 8,
            }],
        },
        options: {
            cutout: '68%',
            plugins: {
                legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, pointStyle: 'rectRounded', font: { size: 11, weight: '500' } } },
                tooltip: {
                    backgroundColor: 'rgba(10, 14, 26, 0.95)', borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1, padding: 12, cornerRadius: 8,
                    callbacks: {
                        label: (item) => {
                            const total = item.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = total > 0 ? ((item.raw / total) * 100).toFixed(1) : 0;
                            return ` ${item.label}: ${pct}%`;
                        },
                    },
                },
            },
        },
        plugins: [{
            id: 'centerText',
            beforeDraw: (chart) => {
                const { ctx, width, height } = chart;
                const dataset = chart.data.datasets[0].data;
                const total = dataset.reduce((a, b) => a + b, 0);
                const productive = dataset[1] + dataset[2] + dataset[3];
                const pct = total > 0 ? ((productive / total) * 100).toFixed(0) : '0';
                ctx.save();
                ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
                ctx.font = "700 1.8rem 'Inter', sans-serif"; ctx.fillStyle = '#f1f5f9';
                ctx.fillText(`${pct}%`, width / 2, height / 2 - 8);
                ctx.font = "400 0.7rem 'Inter', sans-serif"; ctx.fillStyle = '#94a3b8';
                ctx.fillText('Productive', width / 2, height / 2 + 16);
                ctx.restore();
            },
        }],
    });
    return distributionChart;
}

function updateDistributionChart(intervals) {
    if (!distributionChart) return;
    const counts = { idle: 0, passive: 0, active: 0, high_focus: 0 };
    for (const iv of intervals) {
        const state = iv.activity_state || 'idle';
        if (counts[state] !== undefined) counts[state]++;
    }
    distributionChart.data.datasets[0].data = [counts.idle, counts.passive, counts.active, counts.high_focus];
    distributionChart.update();
}

// ── Productivity Trend Line Chart ─────────────────────────────────────
let trendChart = null;

function createTrendChart(canvasId) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, 260);
    gradient.addColorStop(0, 'rgba(59, 130, 246, 0.25)');
    gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)');
    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Efficiency', data: [],
                borderColor: CHART_COLORS.high_focus.main, backgroundColor: gradient,
                borderWidth: 2.5, fill: true, tension: 0.4, pointRadius: 4,
                pointBackgroundColor: CHART_COLORS.high_focus.main, pointBorderColor: '#0a0e1a',
                pointBorderWidth: 2, pointHoverRadius: 6,
            }, {
                label: 'Productive Hours', data: [],
                borderColor: CHART_COLORS.active.main, borderWidth: 2, borderDash: [5, 5],
                fill: false, tension: 0.4, pointRadius: 3,
                pointBackgroundColor: CHART_COLORS.active.main, pointBorderColor: '#0a0e1a',
                pointBorderWidth: 2, yAxisID: 'y1',
            }],
        },
        options: {
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, pointStyle: 'circle', font: { size: 11, weight: '500' } } },
                tooltip: { backgroundColor: 'rgba(10, 14, 26, 0.95)', borderColor: 'rgba(255, 255, 255, 0.1)', borderWidth: 1, padding: 12, cornerRadius: 8 },
            },
            scales: {
                x: { grid: { display: false }, ticks: { font: { size: 10 } } },
                y: { beginAtZero: true, max: 100, grid: { color: CHART_COLORS.grid },
                    ticks: { font: { size: 10 }, callback: (val) => `${val}%` },
                    title: { display: true, text: 'Efficiency %', font: { size: 10 }, color: CHART_COLORS.textMuted },
                },
                y1: { position: 'right', beginAtZero: true, grid: { display: false },
                    ticks: { font: { size: 10 }, callback: (val) => `${val}h` },
                    title: { display: true, text: 'Hours', font: { size: 10 }, color: CHART_COLORS.textMuted },
                },
            },
        },
    });
    return trendChart;
}

function updateTrendChart(summaries) {
    if (!trendChart) return;
    const labels = summaries.map(s => {
        const d = new Date(s.date);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });
    trendChart.data.labels = labels;
    trendChart.data.datasets[0].data = summaries.map(s => s.efficiency || 0);
    trendChart.data.datasets[1].data = summaries.map(s => parseFloat(((s.productive_seconds || 0) / 3600).toFixed(2)));
    trendChart.update();
}

// ═══════════════════════════════════════════════════════════════════════
// NEW: VDI Comparison Chart
// ═══════════════════════════════════════════════════════════════════════
let vdiComparisonChart = null;

function createVdiComparisonChart(canvasId) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    vdiComparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`),
            datasets: [{
                label: 'VDI Active',
                data: new Array(24).fill(0),
                backgroundColor: 'rgba(59, 130, 246, 0.5)',
                borderColor: '#3b82f6',
                borderWidth: 1, borderRadius: 4, borderSkipped: false,
            }, {
                label: 'Non-VDI',
                data: new Array(24).fill(0),
                backgroundColor: 'rgba(148, 163, 184, 0.2)',
                borderColor: 'rgba(148, 163, 184, 0.4)',
                borderWidth: 1, borderRadius: 4, borderSkipped: false,
            }],
        },
        options: {
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(10, 14, 26, 0.95)',
                    borderColor: 'rgba(255, 255, 255, 0.1)', borderWidth: 1,
                    padding: 12, cornerRadius: 8,
                    callbacks: {
                        label: (item) => {
                            const mins = Math.round(item.raw / 60);
                            return ` ${item.dataset.label}: ${mins}m`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    stacked: true, grid: { display: false },
                    ticks: { font: { size: 10 }, maxRotation: 0,
                        callback: function(val, index) { return index % 3 === 0 ? this.getLabelForValue(val) : ''; }
                    },
                },
                y: {
                    stacked: true, beginAtZero: true,
                    grid: { color: CHART_COLORS.grid },
                    ticks: { font: { size: 10 }, callback: (val) => `${Math.round(val / 60)}m` },
                },
            },
        },
    });
    return vdiComparisonChart;
}

function updateVdiComparisonChart(hourlyVdi) {
    if (!vdiComparisonChart) return;
    const vdiData = new Array(24).fill(0);
    const nonVdiData = new Array(24).fill(0);
    for (const [hour, info] of Object.entries(hourlyVdi)) {
        const h = parseInt(hour, 10);
        vdiData[h] = info.vdi_seconds || 0;
        nonVdiData[h] = info.non_vdi_seconds || 0;
    }
    vdiComparisonChart.data.datasets[0].data = vdiData;
    vdiComparisonChart.data.datasets[1].data = nonVdiData;
    vdiComparisonChart.update('none');
}

// ═══════════════════════════════════════════════════════════════════════
// NEW: Input Activity Heatmap (Canvas-based)
// ═══════════════════════════════════════════════════════════════════════
let heatmapCanvas = null;

function createInputHeatmap(canvasId) {
    heatmapCanvas = document.getElementById(canvasId);
}

function updateInputHeatmap(hourlyInput) {
    if (!heatmapCanvas) return;
    const ctx = heatmapCanvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = heatmapCanvas.parentElement.getBoundingClientRect();
    const W = rect.width;
    const H = rect.height;
    heatmapCanvas.width = W * dpr;
    heatmapCanvas.height = H * dpr;
    heatmapCanvas.style.width = W + 'px';
    heatmapCanvas.style.height = H + 'px';
    ctx.scale(dpr, dpr);

    const categories = ['Keys', 'Clicks', 'Scrolls', 'Moves'];
    const catKeys = ['keys', 'clicks', 'scrolls', 'mouse_moves'];

    // Build data matrix and find max
    const matrix = [];
    let maxVal = 1;
    for (let c = 0; c < 4; c++) {
        matrix[c] = [];
        for (let h = 0; h < 24; h++) {
            const hourKey = h.toString().padStart(2, '0');
            const val = (hourlyInput[hourKey] && hourlyInput[hourKey][catKeys[c]]) || 0;
            matrix[c][h] = val;
            if (val > maxVal) maxVal = val;
        }
    }

    const labelW = 60;
    const bottomH = 28;
    const cellW = (W - labelW - 16) / 24;
    const cellH = (H - bottomH - 20) / 4;
    const gap = 2;

    ctx.clearRect(0, 0, W, H);

    // Draw category labels
    ctx.font = "500 11px 'Inter', sans-serif";
    ctx.fillStyle = '#94a3b8';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    for (let c = 0; c < 4; c++) {
        ctx.fillText(categories[c], labelW - 8, 16 + c * cellH + cellH / 2);
    }

    // Draw hour labels
    ctx.font = "400 9px 'Inter', sans-serif";
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    for (let h = 0; h < 24; h++) {
        if (h % 3 === 0) {
            ctx.fillStyle = '#64748b';
            ctx.fillText(`${h.toString().padStart(2, '0')}`, labelW + h * cellW + cellW / 2, H - bottomH + 8);
        }
    }

    // Draw cells
    for (let c = 0; c < 4; c++) {
        for (let h = 0; h < 24; h++) {
            const val = matrix[c][h];
            const intensity = val / maxVal;
            const x = labelW + h * cellW + gap / 2;
            const y = 16 + c * cellH + gap / 2;
            const w = cellW - gap;
            const ht = cellH - gap;

            // Color interpolation: dark → blue → purple
            const r = Math.round(59 + (139 - 59) * intensity);
            const g = Math.round(130 + (92 - 130) * intensity);
            const b = Math.round(246 + (246 - 246) * intensity);
            const alpha = 0.08 + intensity * 0.7;

            ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha})`;
            ctx.beginPath();
            ctx.roundRect(x, y, w, ht, 3);
            ctx.fill();

            // Show value in cell if large enough
            if (val > 0 && cellW > 20 && cellH > 20) {
                ctx.font = "600 9px 'Inter', sans-serif";
                ctx.fillStyle = intensity > 0.5 ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.4)';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(val > 999 ? `${(val/1000).toFixed(0)}k` : val, x + w / 2, y + ht / 2);
            }
        }
    }
}
