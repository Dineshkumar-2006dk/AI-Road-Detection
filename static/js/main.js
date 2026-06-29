/* ═══════════════════════════════════════════════════════════════
   RoadGuard AI – Global JavaScript Utilities
   ═══════════════════════════════════════════════════════════════ */

"use strict";

// ── CSRF Token helper ─────────────────────────────────────────────────────────
function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta) return meta.getAttribute('content');
  // Try cookie
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? match[1] : '';
}

// ── Toast notifications ───────────────────────────────────────────────────────
function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const icons = {
    success: 'fa-circle-check',
    danger:  'fa-circle-xmark',
    warning: 'fa-triangle-exclamation',
    info:    'fa-circle-info',
  };
  const colors = {
    success: '#28a745',
    danger:  '#dc3545',
    warning: '#ffc107',
    info:    '#2196f3',
  };

  const id   = `toast_${Date.now()}`;
  const icon = icons[type] || icons.info;
  const color= colors[type] || colors.info;

  const toastEl = document.createElement('div');
  toastEl.id        = id;
  toastEl.className = 'rg-toast toast show d-flex align-items-center gap-3 mb-2';
  toastEl.style.cssText = `border-left:3px solid ${color};padding:12px 16px;animation:fadeInUp .3s ease both;`;
  toastEl.innerHTML = `
    <i class="fas ${icon}" style="color:${color};font-size:16px;flex-shrink:0;"></i>
    <span style="flex:1;font-size:14px;">${message}</span>
    <button onclick="document.getElementById('${id}').remove()"
            style="background:none;border:none;color:#546e7a;cursor:pointer;font-size:14px;">
      <i class="fas fa-times"></i>
    </button>
  `;
  container.appendChild(toastEl);
  setTimeout(() => { if (document.getElementById(id)) document.getElementById(id).remove(); }, duration);
}

// ── Sidebar toggle ────────────────────────────────────────────────────────────
const sidebarToggle  = document.getElementById('sidebarToggle');
const sidebar        = document.getElementById('sidebar');
const mainContent    = document.getElementById('main-content');

if (sidebarToggle && sidebar) {
  sidebarToggle.addEventListener('click', () => {
    if (window.innerWidth <= 992) {
      sidebar.classList.toggle('open');
    } else {
      document.body.classList.toggle('sidebar-collapsed');
    }
  });
  // Close sidebar on mobile when clicking outside
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 992 && sidebar.classList.contains('open')
        && !sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
      sidebar.classList.remove('open');
    }
  });
}

// ── Theme toggle ──────────────────────────────────────────────────────────────
const themeToggleBtn = document.getElementById('themeToggle');
const themeIcon      = document.getElementById('themeIcon');

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('rg_theme', theme);
  if (themeIcon) {
    themeIcon.className = theme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
  }
}

// Load saved theme
applyTheme(localStorage.getItem('rg_theme') || 'dark');

if (themeToggleBtn) {
  themeToggleBtn.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    applyTheme(current === 'dark' ? 'light' : 'dark');
  });
}

// ── Voice toggle ──────────────────────────────────────────────────────────────
let voiceEnabled = localStorage.getItem('rg_voice') !== 'false';
const voiceToggleBtn = document.getElementById('voiceToggle');
const voiceIcon      = document.getElementById('voiceIcon');

function updateVoiceIcon() {
  if (!voiceIcon) return;
  voiceIcon.className = voiceEnabled ? 'fas fa-volume-high' : 'fas fa-volume-xmark';
  voiceToggleBtn.style.color = voiceEnabled ? '' : 'rgba(255,255,255,.3)';
}
updateVoiceIcon();

if (voiceToggleBtn) {
  voiceToggleBtn.addEventListener('click', () => {
    voiceEnabled = !voiceEnabled;
    localStorage.setItem('rg_voice', voiceEnabled);
    updateVoiceIcon();
    showToast(`Voice alerts ${voiceEnabled ? 'enabled' : 'disabled'}`, voiceEnabled ? 'success' : 'info', 2000);
  });
}

// ── Counter animation ─────────────────────────────────────────────────────────
function animateCounter(el, target, duration = 1200, suffix = '') {
  const start = parseInt(el.textContent) || 0;
  const diff  = target - start;
  if (diff === 0) { el.textContent = target + suffix; return; }
  const startTime = performance.now();
  function update(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + diff * ease) + suffix;
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

// ── Number formatter ──────────────────────────────────────────────────────────
function formatNumber(n) {
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
  return n.toString();
}

// ── Auto-dismiss alerts ───────────────────────────────────────────────────────
document.querySelectorAll('.rg-alert').forEach(alert => {
  setTimeout(() => {
    alert.style.opacity = '0';
    alert.style.transition = 'opacity .5s';
    setTimeout(() => alert.remove(), 500);
  }, 5000);
});

// ── Highlight active nav ──────────────────────────────────────────────────────
(function() {
  const path = window.location.pathname;
  document.querySelectorAll('.sidebar-nav .nav-link').forEach(link => {
    if (link.getAttribute('href') === path) {
      link.classList.add('active');
    }
  });
})();

// ── Global API helper ─────────────────────────────────────────────────────────
async function apiPost(url, formData) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCsrfToken() },
    body: formData,
  });
  return response.json();
}

async function apiPostJSON(url, data) {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    body: JSON.stringify(data),
  });
  return response.json();
}

// ── Road condition colors ─────────────────────────────────────────────────────
const CONDITION_COLORS = {
  Good:     { bg: 'rgba(40,167,69,.15)',  border: 'rgba(40,167,69,.4)',  text: '#66bb6a' },
  Moderate: { bg: 'rgba(255,193,7,.15)',  border: 'rgba(255,193,7,.4)',  text: '#ffc107' },
  Poor:     { bg: 'rgba(253,126,20,.15)', border: 'rgba(253,126,20,.4)', text: '#fd7e14' },
  Critical: { bg: 'rgba(220,53,69,.15)',  border: 'rgba(220,53,69,.4)',  text: '#ef5350' },
};

const SEVERITY_COLORS = {
  Low:      '#28a745',
  Medium:   '#ffc107',
  High:     '#fd7e14',
  Critical: '#dc3545',
};

const DAMAGE_COLORS_JS = [
  '#2196f3','#f44336','#ff9800','#4caf50','#9c27b0',
  '#00bcd4','#ff5722','#8bc34a','#e91e63','#03a9f4',
  '#ffc107','#607d8b',
];

// ── Print helper ──────────────────────────────────────────────────────────────
function printReport() {
  window.print();
}

console.log('%c🛡️ RoadGuard AI %c– Road Quality Monitor',
  'color:#42a5f5;font-size:16px;font-weight:900;',
  'color:#78909c;font-size:13px;');
