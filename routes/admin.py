"""
Admin Blueprint
================
Admin-only routes for user management and system monitoring.
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from extensions import db
from models.user import User
from models.detection import Detection
from models.logs import ActivityLog
from utils.security import admin_required, sanitize_string, sanitize_email

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@admin_required
def admin_panel():
    total_users      = User.query.count()
    total_detections = Detection.query.count()
    recent_logs      = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(20).all()
    return render_template("admin/admin_panel.html",
                           total_users=total_users,
                           total_detections=total_detections,
                           recent_logs=recent_logs)


@admin_bp.route("/users")
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/admin_users.html", users=users)


@admin_bp.route("/api/users", methods=["GET"])
@login_required
@admin_required
def api_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])


@admin_bp.route("/api/users/<int:uid>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_user(uid):
    user = User.query.get_or_404(uid)
    if user.id == current_user.id:
        return jsonify({"success": False, "error": "Cannot disable yourself"}), 400
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({"success": True, "is_active": user.is_active})


@admin_bp.route("/api/users/<int:uid>", methods=["DELETE"])
@login_required
@admin_required
def delete_user(uid):
    user = User.query.get_or_404(uid)
    if user.id == current_user.id:
        return jsonify({"success": False, "error": "Cannot delete yourself"}), 400
    db.session.delete(user)
    db.session.commit()
    return jsonify({"success": True})


@admin_bp.route("/api/detections/clear", methods=["DELETE"])
@login_required
@admin_required
def clear_detections():
    Detection.query.delete()
    db.session.commit()
    return jsonify({"success": True, "message": "All detections cleared"})


@admin_bp.route("/api/logs/delete/login", methods=["DELETE"])
@login_required
@admin_required
def delete_login_logs():
    try:
        ActivityLog.query.filter_by(action="login").delete()
        db.session.commit()
        return jsonify({"success": True, "message": "User login history cleared"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/logs/delete/logout", methods=["DELETE"])
@login_required
@admin_required
def delete_logout_logs():
    try:
        ActivityLog.query.filter_by(action="logout").delete()
        db.session.commit()
        return jsonify({"success": True, "message": "User logout history cleared"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/logs/delete/all", methods=["DELETE"])
@login_required
@admin_required
def delete_all_logs():
    try:
        ActivityLog.query.delete()
        db.session.commit()
        return jsonify({"success": True, "message": "All user activity logs cleared"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/stats")
@login_required
@admin_required
def admin_stats():
    return jsonify({
        "total_users":       User.query.count(),
        "active_users":      User.query.filter_by(is_active=True).count(),
        "total_detections":  Detection.query.count(),
        "critical_roads":    Detection.query.filter_by(road_condition="Critical").count(),
        "poor_roads":        Detection.query.filter_by(road_condition="Poor").count(),
        "emails_sent":       Detection.query.filter_by(email_sent=True).count(),
        "camera_detections": Detection.query.filter_by(source="camera").count(),
        "image_detections":  Detection.query.filter_by(source="image").count(),
    })
