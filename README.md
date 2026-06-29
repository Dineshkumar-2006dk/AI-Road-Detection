# 🛡️ RoadGuard AI – AI-Based Road Quality Monitoring System

> Real-Time Intelligent Road Damage Detection using Computer Vision, YOLOv8, and Deep Learning.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey?style=flat-square&logo=flask)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-purple?style=flat-square)
![SQLite](https://img.shields.io/badge/Database-SQLite-green?style=flat-square)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-blueviolet?style=flat-square&logo=bootstrap)

---

## 🚀 Features

| Feature | Status |
|---------|--------|
| Image-based road damage detection | ✅ |
| Live camera (webcam) detection | ✅ |
| 11+ damage class detection | ✅ |
| Road condition classification | ✅ |
| Damage severity scoring | ✅ |
| GPS location tagging | ✅ |
| Interactive Folium map | ✅ |
| Voice alerts (English & Tamil) | ✅ |
| SMTP email reports | ✅ |
| Detection history (SQLite) | ✅ |
| CSV / Excel / PDF export | ✅ |
| Chart.js dashboard | ✅ |
| Admin panel | ✅ |
| Dark / Light theme | ✅ |
| OpenCV simulation mode | ✅ |

---

## 📦 Installation

### Prerequisites
- Python 3.10+
- pip
- A webcam (for live detection)
- Gmail account with App Password (for email alerts)

### 1. Clone / Extract the Project

```bash
cd "AI Road detection"
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ If you don't have a CUDA GPU, PyTorch CPU-only is sufficient for inference.
> For CPU: `pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu`

### 4. Configure Settings

Copy `.env.example` to `.env` and fill in your credentials:

```bash
copy .env.example .env   # Windows
cp  .env.example .env    # Linux
```

Edit `.env`:

```
SMTP_USERNAME=your_gmail@gmail.com
SMTP_PASSWORD=your_16_character_app_password
SECRET_KEY=random-secret-key-here
```

> 📧 **Gmail App Password**: Go to Google Account → Security → 2-Step Verification → App Passwords.
> Generate a password for "Mail" and paste it as `SMTP_PASSWORD`.

### 5. (Optional) Add YOLOv8 Weights

Place your trained `best.pt` file in the `weights/` folder:

```
weights/
  └── best.pt
```

If no weights file is present, the app runs in **OpenCV Simulation Mode** — all features work, detection uses intelligent heuristic analysis.

### 6. Run the Application

```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## 🔑 Default Admin Credentials

| Field    | Value                  |
|----------|------------------------|
| Email    | `admin@roadguard.ai`   |
| Password | `Admin@1234`           |

> ⚠️ Change these immediately after first login via the Settings page.

---

## 📁 Project Structure

```
AI Road detection/
├── app.py                    # Flask app factory + entry point
├── config.py                 # Central configuration
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
├── README.md
│
├── routes/                   # Flask blueprints
│   ├── auth.py               # Login / register / logout
│   ├── detection.py          # Image + camera detection APIs
│   ├── dashboard.py          # Dashboard stats API
│   ├── history.py            # History CRUD + export
│   ├── map_routes.py         # Folium map page
│   ├── admin.py              # Admin panel
│   └── settings.py           # User settings
│
├── utils/                    # Helper modules
│   ├── yolo_inference.py     # YOLOv8 + OpenCV simulation
│   ├── severity.py           # Severity classification
│   ├── gps_utils.py          # Geolocation + map builder
│   ├── email_utils.py        # SMTP email
│   ├── voice_alert.py        # pyttsx3 + gTTS
│   ├── report_utils.py       # PDF + Excel export
│   └── security.py           # File validation + auth helpers
│
├── models/                   # SQLAlchemy models
│   ├── user.py
│   ├── detection.py
│   ├── report.py
│   ├── settings_model.py
│   └── logs.py
│
├── templates/                # Jinja2 HTML templates
│   ├── base.html             # Sidebar + topbar layout
│   ├── index.html            # Landing page
│   ├── auth/                 # Login, register, forgot password
│   ├── detection/            # Image + camera pages
│   ├── dashboard/            # Dashboard with charts
│   ├── history/              # Detection history table
│   ├── map/                  # Interactive Folium map
│   ├── features/             # Features showcase
│   ├── settings/             # User settings
│   └── admin/                # Admin panel
│
├── static/
│   ├── css/
│   │   ├── main.css          # Glassmorphism dark theme
│   │   └── auth.css          # Auth page styles
│   └── js/
│       ├── main.js           # Global helpers + toasts
│       ├── detection.js      # Upload + inference
│       ├── camera.js         # Webcam + auto-detect
│       └── dashboard.js      # Chart.js charts
│
├── database/                 # SQLite DB (auto-created)
├── weights/                  # YOLOv8 model weights
├── uploads/                  # Uploaded images
├── history/                  # Detection result images
└── reports/                  # Generated PDF/Excel files
```

---

## 🎯 Damage Classes Detected

| Class | Description |
|-------|-------------|
| `pothole` | Circular road pits |
| `crack` | General surface cracks |
| `longitudinal_crack` | Along-road cracks |
| `transverse_crack` | Cross-road cracks |
| `alligator_crack` | Fatigue/network cracking |
| `surface_damage` | General surface deterioration |
| `road_edge_failure` | Edge crumbling |
| `road_depression` | Sunken road sections |
| `patch_failure` | Failed repair patches |
| `water_logging` | Standing water |
| `loose_gravel` | Loose stone/gravel |
| `normal_road` | Undamaged road |

---

## 📊 Road Condition Colors

| Condition | Color | Description |
|-----------|-------|-------------|
| Good | 🟢 Green | No significant damage |
| Moderate | 🟡 Yellow | Minor damage detected |
| Poor | 🟠 Orange | Moderate damage |
| Critical | 🔴 Red | Severe damage, immediate action needed |

---

## 🤖 AI Model Details

| Attribute | Value |
|-----------|-------|
| Architecture | YOLOv8 (nano/small) |
| Framework | Ultralytics |
| Classes | 16 |
| Target mAP50 | ≥ 0.95 |
| Input | RGB images (any resolution) |
| Fallback | OpenCV heuristic simulation |

### Training Augmentations
- Random brightness / contrast
- Horizontal flip
- Random rotation (±15°)
- Random scaling
- Gaussian blur / noise
- Shadow simulation
- Weather simulation (rain/fog)

---

## 🔒 Security Features

- Werkzeug password hashing (bcrypt)
- Flask-WTF CSRF protection on all POST routes
- File magic-byte validation
- SQL injection protection via SQLAlchemy ORM
- Session timeout
- Admin-only route decorator
- Input sanitization

---

## 📧 Email Setup (Gmail)

1. Enable 2-Step Verification on your Google account
2. Go to: Google Account → Security → App Passwords
3. Generate an App Password for "Mail"
4. Add to `.env`:
   ```
   SMTP_USERNAME=yourname@gmail.com
   SMTP_PASSWORD=xxxx xxxx xxxx xxxx
   ```

---

## 🗺️ GPS Features

- Browser Geolocation API (works on localhost)
- Reverse geocoding via Geopy/Nominatim
- Google Maps link generation
- Folium interactive map with color-coded markers
- Layer controls (Good / Moderate / Poor / Critical)

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Camera not working | Allow camera permissions in browser |
| Email not sending | Check SMTP credentials in `.env` |
| Model not loading | Place `best.pt` in `weights/` folder |
| Voice not working | Install `pyttsx3`: `pip install pyttsx3` |
| SQLite error | Delete `database/roadguard.db` and restart |

---

## 📄 License

MIT License – Free for educational and research purposes.

---

## 👨‍💻 Built With

- **Python Flask** – Web framework
- **YOLOv8** – Object detection model
- **OpenCV** – Computer vision
- **SQLite** – Lightweight database
- **Bootstrap 5** – Responsive UI
- **Chart.js** – Interactive charts
- **Folium** – Interactive maps
- **pyttsx3** – Voice alerts

---

*🛡️ RoadGuard AI – Making roads safer with Artificial Intelligence*
