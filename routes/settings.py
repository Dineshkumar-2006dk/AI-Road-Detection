"""Settings Blueprint – per-user preferences."""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.settings_model import UserSettings

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.route("/")
@login_required
def settings():
    s = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not s:
        s = UserSettings(user_id=current_user.id)
        db.session.add(s)
        db.session.commit()
    return render_template("settings/settings.html", settings=s)


@settings_bp.route("/api/save", methods=["POST"])
@login_required
def api_save():
    data = request.get_json(silent=True) or {}
    s = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not s:
        s = UserSettings(user_id=current_user.id)
        db.session.add(s)

    s.conf_threshold     = float(data.get("conf_threshold",  s.conf_threshold))
    s.nms_threshold      = float(data.get("nms_threshold",   s.nms_threshold))
    s.theme              = data.get("theme",              s.theme)
    s.language           = data.get("language",           s.language)
    s.voice_enabled      = bool(data.get("voice_enabled", s.voice_enabled))
    s.email_alerts       = bool(data.get("email_alerts",  s.email_alerts))
    s.notification_email = data.get("notification_email", s.notification_email)
    s.camera_index       = int(data.get("camera_index",   s.camera_index))
    s.camera_fps         = int(data.get("camera_fps",     s.camera_fps))
    s.smtp_server        = data.get("smtp_server",        s.smtp_server)
    s.smtp_port          = int(data.get("smtp_port",          s.smtp_port or 587))
    s.smtp_username      = data.get("smtp_username",      s.smtp_username)
    s.smtp_password      = data.get("smtp_password",      s.smtp_password)

    s.sms_alerts         = bool(data.get("sms_alerts",    s.sms_alerts))
    s.sms_sid            = data.get("sms_sid",            s.sms_sid)
    s.sms_token          = data.get("sms_token",          s.sms_token)
    s.sms_from           = data.get("sms_from",           s.sms_from)
    s.sms_to             = data.get("sms_to",             s.sms_to)
    s.sms_mode           = data.get("sms_mode",           s.sms_mode)

    db.session.commit()
    return jsonify({"success": True, "settings": s.to_dict()})


@settings_bp.route("/api/get")
@login_required
def api_get():
    s = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not s:
        s = UserSettings(user_id=current_user.id)
        db.session.add(s)
        db.session.commit()
    return jsonify(s.to_dict())


@settings_bp.route("/api/db_type")
@login_required
def api_db_type():
    from flask import current_app
    uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if "sqlite" in uri:
        return jsonify({"db_type": "SQLite (Temporary)", "persistent": False})
    else:
        return jsonify({"db_type": "PostgreSQL (Persistent)", "persistent": True})


@settings_bp.route("/features")
@login_required
def features():
    return render_template("features/features.html")


@settings_bp.route("/about_developer")
@login_required
def about_developer():
    return render_template("settings/about_developer.html")
