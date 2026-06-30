"""
Dashboard Blueprint
====================
Stats, charts, and the main dashboard page.
"""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from extensions import db
from models.detection import Detection

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def dashboard():
    return render_template("dashboard/dashboard.html")


@dashboard_bp.route("/api/stats")
@login_required
def api_stats():
    """Return all dashboard stats as JSON for Chart.js."""
    today = datetime.utcnow().date()
    is_admin = current_user.role == "admin"

    def base_query():
        q = Detection.query
        if not is_admin:
            q = q.filter_by(user_id=current_user.id)
        return q

    # ── Totals ───────────────────────────────────────────────────────────────
    total_detections = base_query().count()
    today_detections = base_query().filter(
        func.date(Detection.timestamp) == today
    ).count()

    # ── By condition ─────────────────────────────────────────────────────────
    cond_rows = base_query().with_entities(
        Detection.road_condition, func.count(Detection.id)
    ).group_by(Detection.road_condition).all()
    condition_counts = {row[0]: row[1] for row in cond_rows if row[0]}

    # ── By severity ───────────────────────────────────────────────────────────
    sev_rows = base_query().with_entities(
        Detection.severity, func.count(Detection.id)
    ).group_by(Detection.severity).all()
    severity_counts = {row[0]: row[1] for row in sev_rows if row[0]}

    # ── Avg confidence ────────────────────────────────────────────────────────
    avg_conf_row = base_query().with_entities(func.avg(Detection.avg_confidence)).scalar()
    avg_conf = round((avg_conf_row or 0) * 100, 1)

    # ── Last 7 days trend ─────────────────────────────────────────────────────
    trend_labels, trend_data = [], []
    for i in range(6, -1, -1):
        day   = today - timedelta(days=i)
        count = base_query().filter(func.date(Detection.timestamp) == day).count()
        trend_labels.append(day.strftime("%d %b"))
        trend_data.append(count)

    # ── Top damage types ──────────────────────────────────────────────────────
    damage_counter: dict = {}
    for det in base_query().all():
        for dmg in det.get_damage_types():
            if dmg:
                damage_counter[dmg] = damage_counter.get(dmg, 0) + 1

    top_damages = sorted(damage_counter.items(), key=lambda x: x[1], reverse=True)[:8]

    # ── Recent 5 ──────────────────────────────────────────────────────────────
    recent = base_query().order_by(Detection.timestamp.desc()).limit(5).all()

    # Calculate AI Road Quality Score & Grade
    good_c = condition_counts.get("Good", 0)
    mod_c = condition_counts.get("Moderate", 0)
    poor_c = condition_counts.get("Poor", 0)
    crit_c = condition_counts.get("Critical", 0)
    total_c = good_c + mod_c + poor_c + crit_c
    
    if total_c > 0:
        score = (good_c * 100.0 + mod_c * 80.0 + poor_c * 50.0 + crit_c * 20.0) / total_c
        score = max(10.0, min(100.0, score))
    else:
        score = 100.0
        
    if score >= 90.0:
        grade = "A"
    elif score >= 75.0:
        grade = "B"
    elif score >= 60.0:
        grade = "C"
    elif score >= 45.0:
        grade = "D"
    else:
        grade = "F"

    return jsonify({
        "total_detections":  total_detections,
        "today_detections":  today_detections,
        "avg_confidence":    avg_conf,
        "condition_counts":  condition_counts,
        "severity_counts":   severity_counts,
        "trend_labels":      trend_labels,
        "trend_data":        trend_data,
        "top_damages":       [{"name": k, "count": v} for k, v in top_damages],
        "recent":            [d.to_dict() for d in recent],
        "critical_count":    crit_c,
        "poor_count":        poor_c,
        "moderate_count":    mod_c,
        "good_count":        good_c,
        "road_quality_score": round(score, 1),
        "road_quality_grade": grade,
    })
