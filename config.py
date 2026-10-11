"""
RoadGuard AI – Central Configuration
=====================================
Edit the values in this file (or set environment variables) before running.
"""

import os
from datetime import timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import sys
BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.dirname(__file__))


class Config:
    # ──────────────────────────────────────────────────────────
    #  Flask Core
    # ──────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "roadguard-super-secret-key-2024-change-me")
    DEBUG = os.environ.get("DEBUG", "True") == "True"

    # ──────────────────────────────────────────────────────────
    #  Database
    # ──────────────────────────────────────────────────────────
    db_url = os.environ.get("DATABASE_URL")
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    DATABASE_PATH = os.path.join(BASE_DIR, "database", "roadguard.db")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ──────────────────────────────────────────────────────────
    #  Session
    # ──────────────────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # ──────────────────────────────────────────────────────────
    #  File Uploads
    # ──────────────────────────────────────────────────────────
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    RESULT_FOLDER = os.path.join(BASE_DIR, "history")
    REPORT_FOLDER = os.path.join(BASE_DIR, "reports")
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32 MB
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp"}

    # ──────────────────────────────────────────────────────────
    #  AI Model
    # ──────────────────────────────────────────────────────────
    MODEL_PATH = os.environ.get("MODEL_PATH", os.path.join(BASE_DIR, "weights", "best.pt"))
    # Confidence & NMS defaults (can be overridden per-user in Settings)
    DEFAULT_CONF_THRESHOLD = 0.40
    DEFAULT_NMS_THRESHOLD = 0.45
    # Real YOLOv8 inference only. Missing weights are reported as detailed errors.
    SIMULATION_MODE = False

    # ──────────────────────────────────────────────────────────
    # ──────────────────────────────────────────────────────────
    #  Email / Brevo HTTP API (Port 443 HTTPS on Render)
    # ──────────────────────────────────────────────────────────
    BREVO_API_KEY      = os.environ.get("BREVO_API_KEY",      os.environ.get("SMTP_PASSWORD", ""))
    BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", os.environ.get("SMTP_USERNAME", ""))
    BREVO_SENDER_NAME  = os.environ.get("BREVO_SENDER_NAME",  os.environ.get("SMTP_SERVER", "RoadGuard AI"))
    NOTIFICATION_EMAIL = os.environ.get("NOTIFICATION_EMAIL", "")

    SMTP_SERVER   = BREVO_SENDER_NAME or os.environ.get("SMTP_SERVER", "RoadGuard AI")
    SMTP_PORT     = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USERNAME = BREVO_SENDER_EMAIL or os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = BREVO_API_KEY or os.environ.get("SMTP_PASSWORD", "")
    SMTP_FROM     = os.environ.get("SMTP_FROM", f"RoadGuard AI <{SMTP_USERNAME}>" if SMTP_USERNAME else "RoadGuard AI")

    # ──────────────────────────────────────────────────────────
    #  Maps / Geo
    # ──────────────────────────────────────────────────────────
    DEFAULT_MAP_CENTER_LAT = 11.0168  # Coimbatore, Tamil Nadu
    DEFAULT_MAP_CENTER_LON = 76.9558

    # ──────────────────────────────────────────────────────────
    #  Voice
    # ──────────────────────────────────────────────────────────
    VOICE_ENABLED = True
    VOICE_LANGUAGE = "en"  # "en" or "ta"

    # ──────────────────────────────────────────────────────────
    #  Damage Classes  (must match your YOLO labels)
    # ──────────────────────────────────────────────────────────
    DAMAGE_CLASSES = [
        "pothole",
        "crack",
        "longitudinal_crack",
        "transverse_crack",
        "alligator_crack",
        "surface_damage",
        "road_edge_failure",
        "road_depression",
        "patch_failure",
        "water_logging",
        "loose_gravel",
        "normal_road",
    ]

    # ──────────────────────────────────────────────────────────
    #  Road Condition Thresholds
    # ──────────────────────────────────────────────────────────
    CONDITION_THRESHOLDS = {
        "good":    (0.80, 1.00),   # confidence range for "good road"
        "moderate":(0.50, 0.79),
        "poor":    (0.25, 0.49),
        "critical":(0.00, 0.24),
    }

    # ──────────────────────────────────────────────────────────
    #  Admin credentials (initial seed – change after first run)
    # ──────────────────────────────────────────────────────────
    ADMIN_EMAIL    = "admin@roadguard.ai"
    ADMIN_PASSWORD = "Admin@1234"

    # ──────────────────────────────────────────────────────────
    #  WTF CSRF
    # ──────────────────────────────────────────────────────────
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get("CSRF_SECRET", "csrf-secret-roadguard-2024")
