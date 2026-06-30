/* ═══════════════════════════════════════════════════════════════
   RoadGuard AI – Dashboard Charts JavaScript
   ═══════════════════════════════════════════════════════════════ */

"use strict";

// Chart.js global defaults
Chart.defaults.color = '#78909c';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.pointStyleWidth = 10;
Chart.defaults.plugins.legend.labels.padding = 16;

let trendChart, conditionChart, damageChart, severityChart;

// ── Load all dashboard data ────────────────────────────────────────────────────
async function loadDashboard() {
  try {
    const res  = await fetch('/dashboard/api/stats');
    const data = await res.json();
    renderStats(data);
    renderTrendChart(data);
    renderConditionChart(data);
    renderDamageChart(data);
    renderSeverityChart(data);
    renderRecentTable(data.recent || []);
  } catch (e) {
    console.error('Dashboard load error:', e);
  }
}

// ── Stats cards ───────────────────────────────────────────────────────────────
function renderStats(data) {
  const map = {
    statTotal:         data.total_detections,
    statToday:         data.today_detections,
    statCritical:      data.critical_count,
    statQualityScore:  null,
  };
  Object.entries(map).forEach(([id, val]) => {
    const el = document.getElementById(id);
    if (!el) return;
    if (id === 'statQualityScore') {
      const score = data.road_quality_score ?? 100.0;
      el.textContent = score.toFixed(1) + '%';
      
      const gradeEl = document.getElementById('statQualityGrade');
      if (gradeEl) {
        gradeEl.textContent = 'Grade ' + (data.road_quality_grade || 'A');
        gradeEl.style.display = 'inline-block';
        
        const colors = { A: '#66bb6a', B: '#29b6f6', C: '#ffca28', D: '#ffa726', F: '#ef5350' };
        const color = colors[data.road_quality_grade] || '#66bb6a';
        gradeEl.style.borderColor = color + '44';
        gradeEl.style.color = color;
        gradeEl.style.background = color + '15';
      }
    } else {
      animateCounter(el, val || 0);
    }
  });
}

// ── Trend line chart ──────────────────────────────────────────────────────────
function renderTrendChart(data) {
  const ctx = document.getElementById('trendChart');
  if (!ctx) return;
  if (trendChart) trendChart.destroy();

  const grad = ctx.getContext('2d').createLinearGradient(0, 0, 0, 200);
  grad.addColorStop(0, 'rgba(33,150,243,.3)');
  grad.addColorStop(1, 'rgba(33,150,243,.0)');

  trendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels:   data.trend_labels || [],
      datasets: [{
        label:            'Detections',
        data:             data.trend_data || [],
        borderColor:      '#2196f3',
        backgroundColor:  grad,
        borderWidth:      2.5,
        pointBackgroundColor: '#2196f3',
        pointBorderColor:     '#0d1b2a',
        pointBorderWidth:     2,
        pointRadius:          5,
        pointHoverRadius:     7,
        tension:          0.4,
        fill:             true,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: true,
      plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false, backgroundColor: 'rgba(13,27,42,.95)', borderColor: 'rgba(33,150,243,.3)', borderWidth: 1, padding: 12, titleFont: { weight: 700 } } },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,.04)', drawBorder: false }, ticks: { color: '#546e7a' } },
        y: { grid: { color: 'rgba(255,255,255,.04)', drawBorder: false }, ticks: { color: '#546e7a', stepSize: 1, precision: 0 }, beginAtZero: true },
      },
      interaction: { mode: 'nearest', axis: 'x', intersect: false },
    },
  });
}

// ── Road condition doughnut ────────────────────────────────────────────────────
function renderConditionChart(data) {
  const ctx = document.getElementById('conditionChart');
  if (!ctx) return;
  if (conditionChart) conditionChart.destroy();

  const labels = ['Good','Moderate','Poor','Critical'];
  const counts = labels.map(l => data.condition_counts[l] || 0);
  const colors = ['#28a745','#ffc107','#fd7e14','#dc3545'];

  conditionChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data:             counts,
        backgroundColor:  colors.map(c => c + '99'),
        borderColor:      colors,
        borderWidth:      2,
        hoverOffset:      6,
      }],
    },
    options: {
      cutout: '68%', responsive: true, maintainAspectRatio: true,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#78909c', font: { size: 12 } } },
        tooltip: { backgroundColor: 'rgba(13,27,42,.95)', borderColor: 'rgba(33,150,243,.3)', borderWidth: 1, padding: 10 },
      },
    },
  });

  // Custom legend
  const legend = document.getElementById('conditionLegend');
  if (legend) {
    legend.innerHTML = labels.map((l, i) => `
      <div style="display:flex;align-items:center;gap:6px;font-size:12px;color:#78909c;">
        <div style="width:10px;height:10px;border-radius:50%;background:${colors[i]};flex-shrink:0;"></div>
        ${l}: <strong style="color:${colors[i]};">${counts[i]}</strong>
      </div>`).join('');
  }
}

// ── Damage horizontal bar chart ───────────────────────────────────────────────
function renderDamageChart(data) {
  const ctx = document.getElementById('damageChart');
  if (!ctx) return;
  if (damageChart) damageChart.destroy();

  const damages = (data.top_damages || []).slice(0, 8);
  const labels  = damages.map(d => d.name.replace(/_/g,' ').replace(/\b\w/g, c => c.toUpperCase()));
  const counts  = damages.map(d => d.count);
  const colors  = DAMAGE_COLORS_JS.slice(0, labels.length);

  damageChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Detections',
        data:  counts,
        backgroundColor: colors.map(c => c + '88'),
        borderColor:     colors,
        borderWidth:     1.5,
        borderRadius:    6,
        borderSkipped:   false,
      }],
    },
    options: {
      indexAxis: 'y', responsive: true, maintainAspectRatio: true,
      plugins: { legend: { display: false }, tooltip: { backgroundColor: 'rgba(13,27,42,.95)', borderColor: 'rgba(33,150,243,.3)', borderWidth: 1, padding: 10 } },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,.04)', drawBorder: false }, ticks: { color: '#546e7a', precision: 0 }, beginAtZero: true },
        y: { grid: { display: false }, ticks: { color: '#90a4ae', font: { size: 11 } } },
      },
    },
  });
}

// ── Severity doughnut ─────────────────────────────────────────────────────────
function renderSeverityChart(data) {
  const ctx = document.getElementById('severityChart');
  if (!ctx) return;
  if (severityChart) severityChart.destroy();

  const labels = ['Low','Medium','High','Critical'];
  const counts = labels.map(l => data.severity_counts[l] || 0);
  const colors = ['#28a745','#ffc107','#fd7e14','#dc3545'];

  severityChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data:            counts,
        backgroundColor: colors.map(c => c + '88'),
        borderColor:     colors,
        borderWidth:     2,
        hoverOffset:     6,
      }],
    },
    options: {
      cutout: '68%', responsive: true, maintainAspectRatio: true,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#78909c', font: { size: 12 } } },
        tooltip: { backgroundColor: 'rgba(13,27,42,.95)', borderColor: 'rgba(33,150,243,.3)', borderWidth: 1, padding: 10 },
      },
    },
  });

  const legend = document.getElementById('severityLegend');
  if (legend) {
    legend.innerHTML = labels.map((l, i) => `
      <div style="display:flex;align-items:center;gap:6px;font-size:12px;color:#78909c;">
        <div style="width:10px;height:10px;border-radius:50%;background:${colors[i]};"></div>
        ${l}: <strong style="color:${colors[i]};">${counts[i]}</strong>
      </div>`).join('');
  }
}

// ── Recent Detections table ───────────────────────────────────────────────────
function renderRecentTable(items) {
  const tbody = document.getElementById('recentTable');
  if (!tbody) return;
  if (items.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4" style="color:#455a64;">No detections yet. <a href="/detect/image" style="color:#42a5f5;">Analyze your first road image</a></td></tr>';
    return;
  }
  const condColors = { Good:'#28a745', Moderate:'#ffc107', Poor:'#fd7e14', Critical:'#dc3545' };
  tbody.innerHTML = items.map(d => {
    const cc = condColors[d.road_condition] || '#78909c';
    const sc = condColors[d.severity] || '#78909c';
    const dmg = (d.damage_types || []).slice(0,2).map(t =>
      `<span class="dmg-tag">${t.replace(/_/g,' ')}</span>`).join('');
    return `<tr>
      <td style="color:#455a64;">#${d.id}</td>
      <td style="color:#78909c;font-size:12px;white-space:nowrap;">${d.timestamp}</td>
      <td><span class="cond-chip" style="background:${cc}22;color:${cc};border:1px solid ${cc}44;">${d.road_condition||'—'}</span></td>
      <td><span class="cond-chip" style="background:${sc}22;color:${sc};border:1px solid ${sc}44;">${d.severity||'—'}</span></td>
      <td>${dmg || '<span style="color:#455a64;font-size:12px;">None</span>'}</td>
      <td><span style="color:#42a5f5;font-weight:700;">${d.avg_confidence}%</span></td>
    </tr>`;
  }).join('');
}

// Load on DOM ready
document.addEventListener('DOMContentLoaded', loadDashboard);
// Auto-refresh every 30s
setInterval(loadDashboard, 30000);
