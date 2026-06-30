"""
Detection Blueprint
====================
Image upload detection + live camera frame detection.
"""

import os
import uuid
from datetime import datetime
from flask import (Blueprint, render_template, request, jsonify,
                   current_app, url_for, send_from_directory)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from extensions import db
from models.detection import Detection
from models.settings_model import UserSettings
from utils.yolo_inference import run_inference
from utils.gps_utils import reverse_geocode, google_maps_link
from utils.email_utils import send_detection_report
from utils.voice_alert import speak_alert
from utils.security import validate_image, log_activity, sanitize_email

detection_bp = Blueprint("detection", __name__, url_prefix="/detect")


# ── Helper ────────────────────────────────────────────────────────────────────
def _get_thresholds():
    conf = current_app.config["DEFAULT_CONF_THRESHOLD"]
    nms  = current_app.config["DEFAULT_NMS_THRESHOLD"]
    if current_user.is_authenticated:
        s = UserSettings.query.filter_by(user_id=current_user.id).first()
        if s:
            conf = s.conf_threshold
            nms  = s.nms_threshold
    return conf, nms


def _save_detection(result: dict, original_name: str, lat=None, lon=None,
                    location_name=None, maps_link_val=None, source="image") -> Detection:
    try:
        det = Detection(
            user_id        = current_user.id if current_user.is_authenticated else None,
            original_image = original_name,
            result_image   = result["result_image_name"],
            road_condition = result["road_condition"],
            severity       = result["severity"],
            avg_confidence = result["avg_confidence"],
            detection_count= result["detection_count"],
            prediction_time= result["prediction_time"],
            max_depth_cm   = result.get("max_depth_cm", 0.0),
            total_volume_liters = result.get("total_volume_liters", 0.0),
            latitude       = lat,
            longitude      = lon,
            location_name  = location_name,
            maps_link      = maps_link_val,
            source         = source,
        )
        det.set_damage_types(result["damage_types"])
        det.set_confidences(result["confidences"])
        db.session.add(det)
        db.session.commit()
        current_app.logger.info("[DB] Database updated: detection_id=%s", det.id)
        print(f"[DB] Database updated: detection_id={det.id}")
        return det
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("[DB] Database failure while saving detection")
        raise RuntimeError(f"Database failure: {type(exc).__name__}: {exc}") from exc


def _trigger_sms_alert(result, settings, lat, lon, location_name):
    if not settings or not settings.sms_alerts:
        return
    if result.get("severity") != "Critical":
        return

    from utils.sms_utils import send_sms_alert

    is_ta = (settings.language == "ta")
    loc = location_name or ("தென்சிறுவளூர்" if is_ta else "Thensiruvalur")
    if is_ta:
        msg = f"⚠️ எச்சரிக்கை (RoadGuard AI): {loc} பகுதியில் ஆபத்தான சாலைப் பழுது (Critical Pothole) கண்டறியப்பட்டுள்ளது.\n"
        if lat is not None and lon is not None:
            msg += f"📍 அமைவிடம்: {lat:.5f}, {lon:.5f}\n"
            msg += f"🗺️ கூகுள் மேப்: https://maps.google.com/?q={lat},{lon}"
    else:
        msg = f"⚠️ ALERT (RoadGuard AI): Critical road damage detected at {loc}.\n"
        if lat is not None and lon is not None:
            msg += f"📍 Location: {lat:.5f}, {lon:.5f}\n"
            msg += f"🗺️ Google Maps: https://maps.google.com/?q={lat},{lon}"

    send_sms_alert(msg, settings)


# ── Image Detection Page ──────────────────────────────────────────────────────
@detection_bp.route("/image")
@login_required
def image_detection():
    return render_template("detection/image_detection.html")


# ── Image Inference API ───────────────────────────────────────────────────────
@detection_bp.route("/api/image", methods=["POST"])
@login_required
def api_detect_image():
    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image uploaded"}), 400

    file = request.files["image"]
    current_app.logger.info("[Detection] Image received: %s", file.filename)
    print(f"[Detection] Image received: {file.filename}")
    valid, err = validate_image(file)
    if not valid:
        return jsonify({"success": False, "error": err}), 400

    # Save upload
    ext      = file.filename.rsplit(".", 1)[1].lower()
    uid      = str(uuid.uuid4())[:8]
    filename = secure_filename(f"upload_{uid}.{ext}")
    upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(upload_path)

    # GPS
    lat = request.form.get("latitude",  type=float)
    lon = request.form.get("longitude", type=float)
    location_name = None
    maps_link_val = None
    if lat is not None and lon is not None:
        location_name = reverse_geocode(lat, lon)
        maps_link_val = google_maps_link(lat, lon)
        current_app.logger.info("[GPS] GPS captured: %s,%s", lat, lon)
        print(f"[GPS] GPS captured: {lat},{lon}")

    # Run inference
    conf, nms = _get_thresholds()
    try:
        result = run_inference(upload_path, conf_threshold=conf, nms_threshold=nms)
    except Exception as e:
        current_app.logger.exception("[Detection] Image inference error")
        return jsonify({"success": False, "error": str(e)}), 500

    # Save to DB
    try:
        det = _save_detection(result, filename, lat, lon, location_name, maps_link_val)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    # Retrieve user settings
    settings = None
    if current_user.is_authenticated:
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()

    # Voice alert
    if result["detection_count"] > 0:
        speak_alert(result["damage_types"][0] if result["damage_types"] else result["road_condition"].lower())
        current_app.logger.info("[Voice] Voice played")
        print("[Voice] Voice played")

    # Trigger SMS alert
    if settings:
        _trigger_sms_alert(result, settings, lat, lon, location_name)

    # Send email if requested
    email_status = {"sent": False, "message": ""}
    recipient = sanitize_email(request.form.get("email", ""))
    if not recipient and settings:
        if settings.email_alerts and settings.notification_email:
            recipient = sanitize_email(settings.notification_email)
    if recipient:
        result_path = result["result_image_path"]
        email_result = send_detection_report(recipient, {
            **result,
            "latitude":      lat,
            "longitude":     lon,
            "location_name": location_name,
            "maps_link":     maps_link_val,
        }, result_path, user_settings=settings)
        email_status = {"sent": email_result["success"], "message": email_result["message"]}
        if email_result["success"]:
            det.email_sent      = True
            det.email_recipient = recipient
            db.session.commit()
            current_app.logger.info("[Email] Email sent: %s", recipient)
            print(f"[Email] Email sent: {recipient}")

    log_activity("image_detection", f"Condition: {result['road_condition']}, Severity: {result['severity']}")

    return jsonify({
        "success":          True,
        "detection_id":     det.id,
        "original_image_url": url_for("detection.serve_upload", filename=filename),
        "result_image_url": url_for("detection.serve_result", filename=result["result_image_name"]),
        "message":          result["message"],
        "road_condition":   result["road_condition"],
        "condition_color":  result["condition_color"],
        "severity":         result["severity"],
        "damage_types":     result["damage_types"],
        "confidences":      result["confidences"],
        "avg_confidence":   round(result["avg_confidence"] * 100, 1),
        "detection_count":  result["detection_count"],
        "prediction_time":  round(result["prediction_time"], 3),
        "simulation_mode":  result.get("simulation_mode", False),
        "latitude":         lat,
        "longitude":        lon,
        "location_name":    location_name,
        "maps_link":        maps_link_val,
        "email":            email_status,
    })


@detection_bp.route("/api/email/<int:det_id>", methods=["POST"])
@login_required
def api_send_email(det_id):
    data = request.get_json(silent=True) or {}
    recipient = sanitize_email(data.get("email", ""))
    if not recipient:
        return jsonify({"success": False, "error": "Email address is required."}), 400

    query = Detection.query.filter_by(id=det_id)
    if current_user.role != "admin":
        query = query.filter_by(user_id=current_user.id)
    det = query.first_or_404()

    settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    result_path = os.path.join(current_app.config["RESULT_FOLDER"], det.result_image or "")
    email_result = send_detection_report(recipient, {
        "road_condition": det.road_condition,
        "severity": det.severity,
        "damage_types": det.get_damage_types(),
        "avg_confidence": det.avg_confidence,
        "latitude": det.latitude,
        "longitude": det.longitude,
        "location_name": det.location_name,
        "maps_link": det.maps_link,
    }, result_path, user_settings=settings)

    if email_result["success"]:
        det.email_sent = True
        det.email_recipient = recipient
        try:
            db.session.commit()
            current_app.logger.info("[Email] Email sent: %s", recipient)
            print(f"[Email] Email sent: {recipient}")
        except Exception as exc:
            db.session.rollback()
            return jsonify({"success": False, "error": f"Database failure: {type(exc).__name__}: {exc}"}), 500
        return jsonify({"success": True, "message": "Email sent successfully."})

    current_app.logger.error("[Email] SMTP failure: %s", email_result["message"])
    return jsonify({"success": False, "error": email_result["message"]}), 500


# ── Serve result images ───────────────────────────────────────────────────────
@detection_bp.route("/results/<filename>")
@login_required
def serve_result(filename):
    return send_from_directory(current_app.config["RESULT_FOLDER"], filename)


@detection_bp.route("/uploads/<filename>")
@login_required
def serve_upload(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


# ── Camera Detection Page ─────────────────────────────────────────────────────
@detection_bp.route("/camera")
@login_required
def camera_detection():
    return render_template("detection/camera_detection.html")


# ── Camera Frame Inference API ────────────────────────────────────────────────
@detection_bp.route("/api/frame", methods=["POST"])
@login_required
def api_detect_frame():
    import base64
    import cv2
    import numpy as np

    data = request.get_json(silent=True)
    if not data or "frame" not in data:
        return jsonify({"success": False, "error": "No frame data"}), 400

    # Decode base64 frame
    try:
        frame_b64 = data["frame"].split(",")[-1]
        frame_bytes = base64.b64decode(frame_b64)
        nparr = np.frombuffer(frame_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            return jsonify({"success": False, "error": "Invalid image: camera frame could not be decoded."}), 400
    except Exception as exc:
        return jsonify({"success": False, "error": f"Invalid frame data: {type(exc).__name__}: {exc}"}), 400

    # Save temp frame
    uid = str(uuid.uuid4())[:8]
    tmp_path = os.path.join(current_app.config["UPLOAD_FOLDER"], f"frame_{uid}.jpg")
    cv2.imwrite(tmp_path, img_bgr)

    conf, nms = _get_thresholds()
    try:
        result = run_inference(tmp_path, conf_threshold=conf, nms_threshold=nms)
    except Exception as e:
        current_app.logger.exception("[Detection] Frame inference error")
        return jsonify({"success": False, "error": str(e)}), 500

    force_save = bool(data.get("force_save", False))
    saved_to_db = False
    email_status = {"sent": False, "message": ""}
    if result["detection_count"] > 0 or force_save:
        lat = data.get("latitude")
        lon = data.get("longitude")
        location_name = reverse_geocode(lat, lon) if lat is not None and lon is not None else None
        maps_link_val = google_maps_link(lat, lon) if lat is not None and lon is not None else None
        try:
            det = _save_detection(result, f"frame_{uid}.jpg", lat, lon, location_name, maps_link_val, source="camera")
            saved_to_db = True

            # Auto email alert for live camera detection
            if current_user.is_authenticated:
                settings = UserSettings.query.filter_by(user_id=current_user.id).first()
                if settings:
                    _trigger_sms_alert(result, settings, lat, lon, location_name)
                    if settings.email_alerts and settings.notification_email:
                        recipient = sanitize_email(settings.notification_email)
                        if recipient:
                            result_path = result["result_image_path"]
                            email_result = send_detection_report(recipient, {
                                **result,
                                "latitude":      lat,
                                "longitude":     lon,
                                "location_name": location_name,
                                "maps_link":     maps_link_val,
                            }, result_path, user_settings=settings)
                            email_status = {"sent": email_result["success"], "message": email_result["message"]}
                            if email_result["success"]:
                                det.email_sent      = True
                                det.email_recipient = recipient
                                db.session.commit()
                                current_app.logger.info("[Email] Auto Email sent for live camera: %s", recipient)
        except Exception as exc:
            return jsonify({"success": False, "error": str(exc)}), 500

    return jsonify({
        "success":         True,
        "result_image_url":url_for("detection.serve_result", filename=result["result_image_name"]),
        "road_condition":  result["road_condition"],
        "condition_color": result["condition_color"],
        "severity":        result["severity"],
        "damage_types":    result["damage_types"],
        "detections":      result["detections"],
        "avg_confidence":  round(result["avg_confidence"] * 100, 1),
        "detection_count": result["detection_count"],
        "prediction_time": round(result["prediction_time"], 3),
        "message":         result["message"],
        "saved_to_db":     saved_to_db,
        "email":           email_status,
    })
