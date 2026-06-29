/* ═══════════════════════════════════════════════════════════════
   RoadGuard AI – Live Camera Detection JavaScript (FIXED)
   ═══════════════════════════════════════════════════════════════ */

"use strict";

let mediaStream    = null;
let autoDetectLoop = null;
let autoDetect     = false;
let totalDetect    = 0;
let frameCount     = 0;
let detectInterval = 1500;
let lat = null, lon = null;
let confHistory    = [];
let lastSpokenTime = 0;
let fpsInterval    = null;

const video  = document.getElementById('videoFeed');
const canvas = document.getElementById('overlayCanvas');
const ctx    = canvas ? canvas.getContext('2d') : null;

// ── Geolocation (passive watch + IP fallback) ──────────────────────────────────
if (navigator.geolocation) {
  navigator.geolocation.getCurrentPosition(
    (pos) => { lat = pos.coords.latitude; lon = pos.coords.longitude; },
    async () => {
      try {
        const res = await fetch('https://ipapi.co/json/');
        const ipData = await res.json();
        if (ipData.latitude && ipData.longitude) {
          lat = ipData.latitude;
          lon = ipData.longitude;
        }
      } catch (e) {}
    },
    { enableHighAccuracy: true }
  );
  navigator.geolocation.watchPosition(
    (pos) => { lat = pos.coords.latitude; lon = pos.coords.longitude; },
    () => {},
    { enableHighAccuracy: true }
  );
} else {
  fetch('https://ipapi.co/json/')
    .then(r => r.json())
    .then(ipData => {
      if (ipData.latitude && ipData.longitude) {
        lat = ipData.latitude;
        lon = ipData.longitude;
      }
    })
    .catch(() => {});
}

// ── Start Camera ──────────────────────────────────────────────────────────────
async function startCamera(deviceId = null) {
  try {
    const select = document.getElementById('cameraSelect');
    const constraints = {
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 }
      },
      audio: false
    };

    if (deviceId) {
      constraints.video.deviceId = { exact: deviceId };
    } else if (select && select.value) {
      constraints.video.deviceId = { exact: select.value };
    } else {
      constraints.video.facingMode = 'environment';
    }

    mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
    video.srcObject = mediaStream;
    await video.play();

    video.addEventListener('loadedmetadata', syncCanvas);

    hideEl('cameraIdle');
    showEl('liveDot');
    hideEl('startBtn');
    showEl('stopBtn');
    showEl('captureBtn');
    showEl('autoDetectBtn');

    startFPSCounter();
    showToast('Camera started', 'success', 2000);

    // Refresh devices list so we get human-readable labels now that permission is granted
    await refreshCameraList();

    // Select the currently active device in dropdown
    if (select && mediaStream) {
      const activeTrack = mediaStream.getVideoTracks()[0];
      if (activeTrack) {
        const settings = activeTrack.getSettings();
        if (settings && settings.deviceId) {
          select.value = settings.deviceId;
        }
      }
    }
  } catch (err) {
    const msgs = {
      NotAllowedError:  'Camera permission denied. Allow camera access in browser settings.',
      NotFoundError:    'No camera device found.',
      NotReadableError: 'Camera is in use by another application.',
    };
    showToast('Camera error: ' + (msgs[err.name] || err.message), 'danger');
  }
}

// ── Stop Camera ───────────────────────────────────────────────────────────────
function stopCamera() {
  if (autoDetect) toggleAutoDetect();
  if (mediaStream) { mediaStream.getTracks().forEach(t => t.stop()); mediaStream = null; }
  if (fpsInterval) { clearInterval(fpsInterval); fpsInterval = null; }
  video.srcObject = null;
  if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);

  showEl('cameraIdle');
  hideEl('liveDot');
  showEl('startBtn');
  hideEl('stopBtn');
  hideEl('captureBtn');
  hideEl('autoDetectBtn');
  setEl('fpsBadge', '— FPS');
  showToast('Camera stopped', 'info', 2000);
}

// ── Sync canvas overlay to video size ─────────────────────────────────────────
function syncCanvas() {
  if (!canvas) return;
  canvas.width  = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.style.width  = video.offsetWidth  + 'px';
  canvas.style.height = video.offsetHeight + 'px';
}

// ── Capture single frame ──────────────────────────────────────────────────────
async function captureFrame() {
  if (!mediaStream) { showToast('Camera not started', 'warning'); return; }
  const blob = await captureVideoFrame();
  await sendFrame(blob, true);
}

function captureVideoFrame() {
  return new Promise(resolve => {
    const off = document.createElement('canvas');
    off.width  = video.videoWidth  || 640;
    off.height = video.videoHeight || 480;
    off.getContext('2d').drawImage(video, 0, 0);
    off.toBlob(resolve, 'image/jpeg', 0.80);
  });
}

// ── Auto-detect toggle ────────────────────────────────────────────────────────
function toggleAutoDetect() {
  autoDetect = !autoDetect;
  const btn = document.getElementById('autoDetectBtn');
  if (autoDetect) {
    btn.innerHTML  = '<i class="fas fa-rotate fa-spin me-2"></i>Auto Detect: ON';
    btn.style.cssText = 'background:rgba(40,167,69,.25);border-color:rgba(40,167,69,.5);color:#66bb6a;';
    autoDetectLoop = setInterval(async () => {
      if (!mediaStream) return;
      const blob = await captureVideoFrame();
      await sendFrame(blob, false);
    }, detectInterval);
  } else {
    stopAutoDetect();
    btn.innerHTML  = '<i class="fas fa-rotate me-2"></i>Auto Detect: OFF';
    btn.style.cssText = '';
  }
}

function stopAutoDetect() {
  if (autoDetectLoop) { clearInterval(autoDetectLoop); autoDetectLoop = null; }
  autoDetect = false;
}

function updateInterval(val) {
  detectInterval = parseInt(val);
  document.getElementById('intervalLabel').textContent = (val / 1000).toFixed(1) + 's';
  if (autoDetect) {
    stopAutoDetect();
    autoDetect = true;
    autoDetectLoop = setInterval(async () => {
      if (!mediaStream) return;
      const blob = await captureVideoFrame();
      await sendFrame(blob, false);
    }, detectInterval);
  }
}

// ── Send frame to API ─────────────────────────────────────────────────────────
async function sendFrame(blob, forceSave = false) {
  return new Promise(resolve => {
    const reader = new FileReader();
    reader.onloadend = async () => {
      frameCount++;
      try {
        const payload = { frame: reader.result };
        if (lat !== null) payload.latitude  = lat;
        if (lon !== null) payload.longitude = lon;
        if (forceSave)     payload.force_save = true;

        const res = await fetch('/detect/api/frame', {
          method:  'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
          body:    JSON.stringify(payload),
        });
        if (!res.ok) { resolve(); return; }
        const data = await res.json();
        if (data.success) {
          renderLiveResult(data);
          if (data.saved_to_db) {
            showToast(forceSave ? 'Photo captured and saved to history!' : 'Road damage detected! Saved to history.', 'success', 3000);
          } else if (forceSave) {
            showToast('Photo captured!', 'info', 2000);
          }
        }
      } catch (e) {
        console.error('[Camera] Frame send error:', e);
      }
      resolve();
    };
    reader.readAsDataURL(blob);
  });
}

// ── Render live result ────────────────────────────────────────────────────────
function renderLiveResult(data) {
  totalDetect += data.detection_count || 0;
  setEl('lsTotalDetect', totalDetect);
  setEl('lsFrameCount',  frameCount);

  const conf = data.avg_confidence || 0;  // already 0–100
  confHistory.push(conf);
  if (confHistory.length > 10) confHistory.shift();
  const avgConf = confHistory.reduce((a, b) => a + b, 0) / confHistory.length;
  setEl('lsAvgConf', avgConf.toFixed(1) + '%');

  // Confidence meter
  const meter = document.getElementById('confMeter');
  if (meter) meter.style.width = conf + '%';
  setEl('confMeterVal', conf.toFixed(1) + '%');

  // Road condition
  const cond   = data.road_condition || '—';
  const COLORS  = typeof CONDITION_COLORS !== 'undefined' ? CONDITION_COLORS : {};
  const col    = (COLORS[cond] || {}).text || '#78909c';
  const condEl = document.getElementById('liveCondition');
  if (condEl) {
    condEl.style.borderColor = col + '44';
    const txt = condEl.querySelector('.live-condition-text');
    if (txt) { txt.textContent = cond; txt.style.color = col; }
  }

  // Overlay badge
  const overlay = document.getElementById('condOverlay');
  if (overlay) {
    overlay.classList.remove('d-none');
    overlay.textContent      = `${cond} • ${conf.toFixed(0)}%`;
    overlay.style.color      = col;
    overlay.style.borderColor= col + '40';
  }

  // Live result image
  if (data.result_image_url) {
    const wrap = document.getElementById('liveResultWrap');
    const img  = document.getElementById('liveResultImg');
    if (wrap) wrap.classList.add('d-none');
    if (img)  { img.classList.remove('d-none'); img.src = data.result_image_url + '?t=' + Date.now(); }
  }

  // Log entry
  if (data.detection_count > 0) {
    addToLog(data);
    // Voice throttled to once per 5 s
    if (typeof voiceEnabled !== 'undefined' && voiceEnabled
        && (cond === 'Critical' || cond === 'Poor')
        && Date.now() - lastSpokenTime > 5000) {
      lastSpokenTime = Date.now();
      const dmg = (data.damage_types || [])[0] || 'critical';
      playLiveVoice(dmg, cond);
    }
  }
}

function addToLog(data) {
  const log  = document.getElementById('detectionLog');
  if (!log) return;
  const cond = data.road_condition || '—';
  const COLORS = typeof CONDITION_COLORS !== 'undefined' ? CONDITION_COLORS : {};
  const col  = (COLORS[cond] || {}).text || '#78909c';
  const dmgs = (data.damage_types || []).map(d => d.replace(/_/g,' ')).join(', ') || '—';
  const time = new Date().toLocaleTimeString();

  const placeholder = log.querySelector('p');
  if (placeholder) placeholder.remove();

  const entry = document.createElement('div');
  entry.style.cssText = 'display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:12px;';
  entry.innerHTML = `
    <span style="color:${col};font-weight:600;">${cond}</span>
    <span style="color:#78909c;flex:1;margin:0 8px;overflow:hidden;text-overflow:ellipsis;">${dmgs}</span>
    <span style="color:#455a64;white-space:nowrap;">${time}</span>`;
  log.insertBefore(entry, log.firstChild);
  if (log.children.length > 50) log.removeChild(log.lastChild);
}

function clearLog() {
  const log = document.getElementById('detectionLog');
  if (log) log.innerHTML = '<p style="color:#455a64;font-size:13px;text-align:center;padding:20px 0;">No detections yet</p>';
  totalDetect = 0; frameCount = 0; confHistory = [];
  setEl('lsTotalDetect', '0');
  setEl('lsFrameCount',  '0');
  setEl('lsAvgConf',     '—');
}

// ── FPS Counter ───────────────────────────────────────────────────────────────
function startFPSCounter() {
  let frames = 0;
  fpsInterval = setInterval(() => {
    setEl('fpsBadge', frames + ' FPS');
    frames = 0;
  }, 1000);
  function count() {
    if (!mediaStream) return;
    frames++;
    requestAnimationFrame(count);
  }
  requestAnimationFrame(count);
}

// ── Voice ─────────────────────────────────────────────────────────────────────
function playLiveVoice(dmg, cond) {
  if (!('speechSynthesis' in window)) return;
  const msgs_en = {
    pothole:  'Warning! Pothole detected ahead. Reduce speed.',
    crack:    'Road crack detected. Proceed with caution.',
    critical: 'Critical road damage. Slow down immediately.',
    poor:     'Poor road condition detected. Drive carefully.',
  };
  const msgs_ta = {
    pothole:  'எச்சரிக்கை! குழி கண்டுபிடிக்கப்பட்டது. வேகத்தை குறைக்கவும்.',
    crack:    'சாலை வெடிப்பு கண்டுபிடிக்கப்பட்டது. கவனமாக செல்லவும்.',
    critical: 'மிகவும் ஆபத்தான சாலை சேதம். உடனடியாக வேகத்தை குறைக்கவும்.',
    poor:     'மோசமான சாலை நிலை. மெதுவாக ஓட்டவும்.',
  };
  const lang = window.currentUserLanguage || 'en';
  const text = (lang === 'ta' ? msgs_ta[dmg] || msgs_ta[cond.toLowerCase()] : msgs_en[dmg] || msgs_en[cond.toLowerCase()])
            || (lang === 'ta' ? 'சாலை சேதம் கண்டறியப்பட்டது.' : 'Road damage detected.');

  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 1.0; u.pitch = 1; u.volume = 1;
  if (lang === 'ta') {
    u.lang = 'ta-IN';
    const voices = window.speechSynthesis.getVoices();
    const taVoice = voices.find(v => v.lang.startsWith('ta'));
    if (taVoice) u.voice = taVoice;
  } else {
    u.lang = 'en-US';
  }
  window.speechSynthesis.speak(u);
}

// ── Utilities ─────────────────────────────────────────────────────────────────
function setEl(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}
function showEl(id) { const el = document.getElementById(id); if (el) el.classList.remove('d-none'); }
function hideEl(id) { const el = document.getElementById(id); if (el) el.classList.add('d-none');    }

// ── Camera Device Enumeration & Selection ──────────────────────────────────────
async function initCameraSelection() {
  const select = document.getElementById('cameraSelect');
  if (!select) return;

  select.addEventListener('change', async () => {
    const deviceId = select.value;
    if (!deviceId) return;

    const wasRunning = (mediaStream !== null);
    if (wasRunning) {
      stopCamera();
      await startCamera(deviceId);
    }
  });

  // Try listing devices (might yield empty labels until permission is granted)
  await refreshCameraList();
}

async function refreshCameraList() {
  const select = document.getElementById('cameraSelect');
  if (!select) return;

  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    const videoDevices = devices.filter(d => d.kind === 'videoinput');

    const currentVal = select.value;
    select.innerHTML = '';

    if (videoDevices.length === 0) {
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = 'No cameras found';
      select.appendChild(opt);
      return;
    }

    videoDevices.forEach((device, index) => {
      const opt = document.createElement('option');
      opt.value = device.deviceId;

      let label = device.label || '';
      if (!label) {
        label = `Camera ${index + 1}`;
      }

      // Format custom user friendly labels
      const lowerLabel = label.toLowerCase();
      if (lowerLabel.includes('link to windows') || lowerLabel.includes('phone') || lowerLabel.includes('mobile')) {
        label = '📱 Phone Camera (' + label + ')';
      } else if (lowerLabel.includes('webcam') || lowerLabel.includes('integrated') || lowerLabel.includes('front') || lowerLabel.includes('back')) {
        label = '💻 Laptop Built-in Webcam (' + label + ')';
      } else {
        label = '📷 ' + label;
      }

      opt.textContent = label;
      select.appendChild(opt);
    });

    if (currentVal && Array.from(select.options).some(o => o.value === currentVal)) {
      select.value = currentVal;
    } else {
      // Try default selecting phone camera if present, else first
      const phoneIndex = videoDevices.findIndex(d => {
        const lbl = d.label.toLowerCase();
        return lbl.includes('link to windows') || lbl.includes('phone') || lbl.includes('mobile');
      });
      if (phoneIndex !== -1) {
        select.value = videoDevices[phoneIndex].deviceId;
      } else {
        select.value = videoDevices[0].deviceId;
      }
    }
  } catch (e) {
    console.error('Error listing cameras:', e);
  }
}

// Initialize camera select dropdown on load
document.addEventListener('DOMContentLoaded', () => {
  initCameraSelection();
});

window.addEventListener('beforeunload', () => { if (mediaStream) stopCamera(); });
