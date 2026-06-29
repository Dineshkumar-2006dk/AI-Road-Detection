/* ═══════════════════════════════════════════════════════════════
   RoadGuard AI – Image Detection JavaScript (FIXED)
   ═══════════════════════════════════════════════════════════════ */

"use strict";

let selectedFile    = null;
let detectionResult = null;
let timerInterval   = null;
let timerStart      = null;

// ── Drop zone setup ───────────────────────────────────────────────────────────
const dropZone       = document.getElementById('dropZone');
const imageInput     = document.getElementById('imageInput');
const previewSection = document.getElementById('previewSection');
const detectBtn      = document.getElementById('detectBtn');

dropZone.addEventListener('click', () => imageInput.click());
imageInput.addEventListener('change', (e) => { if (e.target.files[0]) handleFile(e.target.files[0]); });

dropZone.addEventListener('dragover',  (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', ()  => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
  e.preventDefault(); dropZone.classList.remove('dragover');
  if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
});

function handleFile(file) {
  const allowed = ['image/jpeg','image/jpg','image/png','image/bmp'];
  if (!allowed.includes(file.type)) { showToast('Invalid file type. Use JPG, PNG or BMP.','danger'); return; }
  if (file.size > 32 * 1024 * 1024) { showToast('File too large (max 32 MB).','danger'); return; }

  selectedFile = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    document.getElementById('previewImg').src   = e.target.result;
    document.getElementById('originalImg').src  = e.target.result;
    const kb = (file.size / 1024).toFixed(1);
    document.getElementById('fileInfo').innerHTML =
      `<span><i class="fas fa-file me-1"></i>${file.name}</span>
       <span><i class="fas fa-weight me-1"></i>${kb} KB</span>
       <span><i class="fas fa-image me-1"></i>${file.type.split('/')[1].toUpperCase()}</span>`;
  };
  reader.readAsDataURL(file);
  dropZone.classList.add('d-none');
  previewSection.classList.remove('d-none');
  detectBtn.disabled = false;
  showPanel('idle');
}

function clearImage() {
  selectedFile = null; imageInput.value = '';
  dropZone.classList.remove('d-none');
  previewSection.classList.add('d-none');
  detectBtn.disabled = true;
  showPanel('idle'); clearTimer();
}

// ── Panel switcher ─────────────────────────────────────────────────────────────
function showPanel(name) {
  ['idle','loading','result'].forEach(p => {
    document.getElementById(p + 'Panel').classList.toggle('d-none', p !== name);
  });
}

// ── Detection Timer ────────────────────────────────────────────────────────────
function startTimer() {
  timerStart = performance.now();
  const el = document.getElementById('detectionTimer');
  timerInterval = setInterval(() => {
    el.textContent = ((performance.now() - timerStart)/1000).toFixed(3) + 's';
  }, 50);
}
function clearTimer() {
  if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
}

// ── GPS ────────────────────────────────────────────────────────────────────────
function getLocation() {
  const status = document.getElementById('locationStatus');
  if (!navigator.geolocation) {
    status.innerHTML = '<span style="color:#ef5350;"><i class="fas fa-times me-1"></i>Geolocation not supported in this browser</span>';
    return;
  }
  status.innerHTML = '<span style="color:#42a5f5;"><i class="fas fa-spinner fa-spin me-1"></i>Detecting GPS location...</span>';
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      document.getElementById('latInput').value = pos.coords.latitude.toFixed(6);
      document.getElementById('lonInput').value = pos.coords.longitude.toFixed(6);
      status.innerHTML = `<span style="color:#66bb6a;"><i class="fas fa-check me-1"></i>
        GPS captured: ${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}</span>`;
    },
    async (err) => {
      status.innerHTML = '<span style="color:#ffa726;"><i class="fas fa-spinner fa-spin me-1"></i>GPS failed. Fetching IP Geolocation...</span>';
      try {
        const res = await fetch('https://ipapi.co/json/');
        const ipData = await res.json();
        if (ipData.latitude && ipData.longitude) {
          document.getElementById('latInput').value = ipData.latitude.toFixed(6);
          document.getElementById('lonInput').value = ipData.longitude.toFixed(6);
          status.innerHTML = `<span style="color:#66bb6a;"><i class="fas fa-check me-1"></i>
            Location captured: ${ipData.city || 'Success'} (${ipData.latitude.toFixed(4)}, ${ipData.longitude.toFixed(4)})</span>`;
        } else {
          status.innerHTML = '<span style="color:#ef5350;"><i class="fas fa-times me-1"></i>Could not detect location. Please enter manually.</span>';
        }
      } catch (e) {
        status.innerHTML = '<span style="color:#ef5350;"><i class="fas fa-times me-1"></i>Could not detect location. Please enter manually.</span>';
      }
    },
    { timeout: 12000, enableHighAccuracy: true }
  );
}

async function searchLocation() {
  const query = document.getElementById('locationSearchInput').value.trim();
  if (!query) {
    showToast('Please enter a location to search.', 'warning');
    return;
  }
  const status = document.getElementById('locationStatus');
  status.innerHTML = '<span style="color:#42a5f5;"><i class="fas fa-spinner fa-spin me-1"></i>Searching location...</span>';
  
  try {
    const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1`, {
      headers: {
        'Accept-Language': 'en'
      }
    });
    const results = await res.json();
    if (results && results.length > 0) {
      const lat = parseFloat(results[0].lat);
      const lon = parseFloat(results[0].lon);
      document.getElementById('latInput').value = lat.toFixed(6);
      document.getElementById('lonInput').value = lon.toFixed(6);
      status.innerHTML = `<span style="color:#66bb6a;"><i class="fas fa-check me-1"></i>
        GPS set to: ${results[0].display_name}</span>`;
      showToast('Location coordinates updated!', 'success');
    } else {
      status.innerHTML = '<span style="color:#ef5350;"><i class="fas fa-times me-1"></i>Location not found</span>';
      showToast('No results found for that location.', 'danger');
    }
  } catch (error) {
    console.error('Error during geocoding:', error);
    status.innerHTML = '<span style="color:#ef5350;"><i class="fas fa-times me-1"></i>Geocoding failed</span>';
    showToast('Failed to connect to geocoding service.', 'danger');
  }
}


// ── Run Detection ──────────────────────────────────────────────────────────────
async function runDetection() {
  if (!selectedFile) { showToast('Please select an image first','warning'); return; }

  showPanel('loading');
  detectBtn.disabled = true;
  startTimer();

  const formData = new FormData();
  formData.append('image', selectedFile);

  const lat   = document.getElementById('latInput').value.trim();
  const lon   = document.getElementById('lonInput').value.trim();
  const email = document.getElementById('emailInput').value.trim();
  if (lat && lon) { formData.append('latitude', lat); formData.append('longitude', lon); }
  if (email)      formData.append('email', email);

  try {
    const response = await fetch('/detect/api/image', {
      method:  'POST',
      headers: { 'X-CSRFToken': getCsrfToken() },   // FormData sets Content-Type automatically
      body:    formData,
    });

    clearTimer();

    if (!response.ok) {
      let errMsg = `Server error ${response.status}`;
      try { const d = await response.json(); errMsg = d.error || errMsg; } catch(_) {}
      showToast(errMsg, 'danger');
      showPanel('idle'); detectBtn.disabled = false;
      return;
    }

    const data = await response.json();

    if (!data.success) {
      showToast(data.error || 'Detection failed', 'danger');
      showPanel('idle'); detectBtn.disabled = false;
      return;
    }

    detectionResult = data;
    renderResult(data);
    showPanel('result');

    // Voice alert via browser (guaranteed to work even if pyttsx3 fails)
    if (typeof voiceEnabled !== 'undefined' && voiceEnabled && data.road_condition) {
      playVoiceAlert(data.road_condition.toLowerCase());
    }

    // Email toast
    if (data.email) {
      if (data.email.sent)
        showToast('Email report sent successfully!', 'success');
      else if (data.email.message && !data.email.message.includes('not configured'))
        showToast('Email: ' + data.email.message, 'warning');
    }

    if (data.simulation_mode) {
      showToast('Simulation mode: Using OpenCV detection (no YOLOv8 model loaded)', 'info', 6000);
    }

  } catch (err) {
    clearTimer();
    showToast('Network error: ' + err.message, 'danger');
    showPanel('idle');
  }

  detectBtn.disabled = false;
}

// ── Render Result ──────────────────────────────────────────────────────────────
function renderResult(data) {
  // Condition banner
  const condCfg = (typeof CONDITION_COLORS !== 'undefined' ? CONDITION_COLORS : {})[data.road_condition]
               || { bg:'rgba(100,100,100,.15)', border:'rgba(100,100,100,.4)', text:'#90a4ae' };
  const banner = document.getElementById('conditionBanner');
  banner.style.background  = condCfg.bg;
  banner.style.borderColor = condCfg.border;
  const condVal = document.getElementById('conditionValue');
  condVal.textContent = data.road_condition || '—';
  condVal.style.color = condCfg.text;

  // Severity badge
  const sevColor = (typeof SEVERITY_COLORS !== 'undefined' ? SEVERITY_COLORS : {})[data.severity] || '#6c757d';
  const sevEl = document.getElementById('severityBadge');
  sevEl.textContent = data.severity || '—';
  sevEl.style.background  = sevColor + '22';
  sevEl.style.color       = sevColor;
  sevEl.style.border      = `1px solid ${sevColor}44`;

  // Result image
  document.getElementById('resultImg').src       = data.result_image_url;
  const dlBtn = document.getElementById('downloadBtn');
  dlBtn.href     = data.result_image_url;
  dlBtn.download = 'roadguard_result.jpg';

  const pdfBtn = document.getElementById('pdfReportBtn');
  if (pdfBtn) {
    if (data.detection_id) {
      pdfBtn.href = `/history/api/export/pdf/${data.detection_id}`;
      pdfBtn.style.display = 'inline-flex';
    } else {
      pdfBtn.style.display = 'none';
    }
  }

  // avg_confidence comes as 0–100 from backend (already multiplied by 100)
  const confPct = typeof data.avg_confidence === 'number' ? data.avg_confidence : 0;
  document.getElementById('mConf').textContent     = confPct.toFixed(1) + '%';
  document.getElementById('mCount').textContent    = data.detection_count ?? 0;
  document.getElementById('mTime').textContent     = (data.prediction_time ?? 0).toFixed(3) + 's';
  document.getElementById('mDmgCount').textContent = (data.damage_types || []).length;

  // Damage list
  const damageList = document.getElementById('damageList');
  const dmgTypes   = data.damage_types  || [];
  const dmgConfs   = data.confidences   || [];

  if (dmgTypes.length === 0) {
    damageList.innerHTML = `<span style="color:#546e7a;font-size:14px;">
      <i class="fas fa-check-circle me-2" style="color:#66bb6a;"></i>No significant road damage detected</span>`;
  } else {
    const combined = dmgTypes.map((t, i) => ({ type: t, conf: dmgConfs[i] ?? 0 }))
                             .sort((a, b) => b.conf - a.conf);
    const COLORS = typeof DAMAGE_COLORS_JS !== 'undefined' ? DAMAGE_COLORS_JS :
      ['#2196f3','#f44336','#ff9800','#4caf50','#9c27b0','#00bcd4','#ff5722','#8bc34a'];

    damageList.innerHTML = combined.map((d, i) => {
      const color = COLORS[i % COLORS.length];
      const label = d.type.replace(/_/g,' ').replace(/\b\w/g, c => c.toUpperCase());
      const pct   = (d.conf * 100).toFixed(1);  // confidences are 0–1
      return `<div class="damage-item">
        <span class="damage-name">${label}</span>
        <div class="damage-bar">
          <div class="damage-fill" id="dBar${i}"
               style="width:0%;background:${color};transition:width 1s ease;"></div>
        </div>
        <span class="damage-conf" style="color:${color};">${pct}%</span>
      </div>`;
    }).join('');

    // Animate bars after paint
    requestAnimationFrame(() => {
      combined.forEach((d, i) => {
        const bar = document.getElementById(`dBar${i}`);
        if (bar) setTimeout(() => bar.style.width = `${(d.conf * 100).toFixed(1)}%`, 80 * i);
      });
    });
  }

  // GPS section
  const gpsSection = document.getElementById('gpsSection');
  if (data.latitude && data.longitude) {
    gpsSection.classList.remove('d-none');
    document.getElementById('gpsBody').innerHTML = `
      <div style="display:flex;flex-direction:column;gap:8px;">
        <div><i class="fas fa-map-pin me-2" style="color:#42a5f5;"></i>
          <strong>${data.location_name || 'GPS Location'}</strong></div>
        <div style="color:#78909c;font-size:13px;">
          Lat: ${data.latitude.toFixed(6)} &nbsp;|&nbsp; Lon: ${data.longitude.toFixed(6)}</div>
        ${data.maps_link ? `<a href="${data.maps_link}" target="_blank"
          class="btn-result-action primary" style="align-self:flex-start;margin-top:4px;">
          <i class="fas fa-map-location-dot me-2"></i>Open in Google Maps</a>` : ''}
      </div>`;
  } else {
    gpsSection.classList.add('d-none');
  }

  // Simulation mode banner
  const simNote = document.getElementById('simModeNote');
  if (simNote) simNote.classList.toggle('d-none', !data.simulation_mode);

  // Message toast
  if (data.detection_count > 0) {
    showToast(`Detection complete: ${data.road_condition} road – ${data.detection_count} damage area(s)`,
              data.road_condition === 'Critical' ? 'danger' : 'info');
  } else {
    showToast('No road damage detected in this image.', 'success');
  }
}

// ── Voice (Web Speech API – always works in browser) ──────────────────────────
function playVoiceAlert(conditionOrClass) {
  if (!('speechSynthesis' in window)) return;
  const msgs_en = {
    critical: "Warning! Critical road damage detected. Reduce vehicle speed immediately.",
    poor:     "Poor road condition detected. Drive carefully.",
    moderate: "Moderate road damage detected. Proceed with caution.",
    good:     "Road condition is good. Safe to drive.",
    pothole:  "Warning! Pothole detected ahead. Reduce vehicle speed.",
    crack:    "Road crack detected. Proceed with caution.",
  };
  const msgs_ta = {
    critical: "எச்சரிக்கை! மிகவும் ஆபத்தான சாலை சேதம். வாகனத்தின் வேகத்தை உடனடியாக குறைக்கவும்.",
    poor:     "மோசமான சாலை நிலை. எச்சரிக்கையாக மெதுவாக ஓட்டவும்.",
    moderate: "மிதமான சாலை சேதம். கவனமாக செல்லவும்.",
    good:     "சாலை நிலை நன்றாக உள்ளது. பாதுகாப்பான பயணம்.",
    pothole:  "எச்சரிக்கை! குழி கண்டுபிடிக்கப்பட்டது. வேகத்தை குறைக்கவும்.",
    crack:    "சாலை வெடிப்பு கண்டுபிடிக்கப்பட்டது. கவனமாக செல்லவும்.",
  };

  const lang = window.currentUserLanguage || 'en';
  const text = (lang === 'ta' ? msgs_ta[conditionOrClass] : msgs_en[conditionOrClass])
            || (lang === 'ta' ? msgs_ta.poor : msgs_en.poor);

  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 0.95; u.pitch = 1; u.volume = 1;
  if (lang === 'ta') {
    u.lang = 'ta-IN';
    const voices = window.speechSynthesis.getVoices();
    const taVoice = voices.find(v => v.lang.startsWith('ta'));
    if (taVoice) u.voice = taVoice;
  } else {
    u.lang = 'en-US';
  }
  window.speechSynthesis.speak(u);
  console.log('[Voice] Played:', text);
}

function speakAlert() {
  if (!detectionResult) { showToast('No detection result to speak','warning'); return; }
  playVoiceAlert((detectionResult.road_condition || 'poor').toLowerCase());
  showToast('Playing voice alert...', 'info', 2000);
}

// ── Send Email (POST to separate email endpoint) ───────────────────────────────
async function sendEmail() {
  const email = document.getElementById('emailInput').value.trim();
  if (!email) { showToast('Enter an email address first','warning'); return; }
  if (!detectionResult || !detectionResult.detection_id) {
    showToast('Analyse an image first','warning'); return;
  }
  const btn = document.getElementById('emailBtn');
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Sending...';
  btn.disabled  = true;

  try {
    const res  = await fetch(`/detect/api/email/${detectionResult.detection_id}`, {
      method:  'POST',
      headers: { 'Content-Type':'application/json', 'X-CSRFToken': getCsrfToken() },
      body:    JSON.stringify({ email }),
    });
    const data = await res.json();
    if (data.success) showToast('Email report sent successfully!', 'success');
    else              showToast('Email failed: ' + (data.error || 'Unknown error'), 'danger');
  } catch (e) {
    showToast('Email error: ' + e.message, 'danger');
  }
  btn.innerHTML = '<i class="fas fa-envelope me-2"></i>Send Report';
  btn.disabled  = false;
}

function printReport() { window.print(); }
