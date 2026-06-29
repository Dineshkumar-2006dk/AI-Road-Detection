"""
History Blueprint
==================
View, search, filter, delete, and export detection history.
"""

import io
from flask import (Blueprint, render_template, jsonify, request,
                   make_response, current_app, send_file)
from flask_login import login_required, current_user
from extensions import db
from models.detection import Detection
from utils.report_utils import generate_csv_report, generate_excel_report, generate_pdf_report
from utils.security import admin_required

history_bp = Blueprint("history", __name__, url_prefix="/history")


def _user_detections():
    """Base query respecting user scope."""
    if current_user.role == "admin":
        return Detection.query
    return Detection.query.filter_by(user_id=current_user.id)


@history_bp.route("/")
@login_required
def history():
    return render_template("history/history.html")


@history_bp.route("/api/list")
@login_required
def api_list():
    """Paginated, filterable list of detections."""
    page     = request.args.get("page",      1,    type=int)
    per_page = request.args.get("per_page",  20,   type=int)
    search   = request.args.get("search",    "")
    condition= request.args.get("condition", "all")
    severity = request.args.get("severity",  "all")
    source   = request.args.get("source",    "all")

    q = _user_detections().order_by(Detection.timestamp.desc())

    if search:
        q = q.filter(Detection.damage_types.ilike(f"%{search}%"))
    if condition != "all":
        q = q.filter_by(road_condition=condition)
    if severity != "all":
        q = q.filter_by(severity=severity)
    if source != "all":
        q = q.filter_by(source=source)

    paginated = q.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items":       [d.to_dict() for d in paginated.items],
        "total":       paginated.total,
        "pages":       paginated.pages,
        "current":     page,
        "has_next":    paginated.has_next,
        "has_prev":    paginated.has_prev,
    })


@history_bp.route("/api/delete/<int:det_id>", methods=["DELETE"])
@login_required
def api_delete(det_id):
    det = _user_detections().filter_by(id=det_id).first_or_404()
    db.session.delete(det)
    db.session.commit()
    return jsonify({"success": True})


@history_bp.route("/api/export/csv")
@login_required
def export_csv():
    detections = _user_detections().order_by(Detection.timestamp.desc()).all()
    csv_str    = generate_csv_report(detections)
    response   = make_response(csv_str)
    response.headers["Content-Disposition"] = "attachment; filename=roadguard_history.csv"
    response.headers["Content-Type"]        = "text/csv"
    return response


@history_bp.route("/api/export/excel")
@login_required
def export_excel():
    detections = _user_detections().order_by(Detection.timestamp.desc()).all()
    xlsx_bytes = generate_excel_report(detections)
    return send_file(
        io.BytesIO(xlsx_bytes),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="roadguard_history.xlsx",
    )


@history_bp.route("/api/export/pdf/<int:det_id>")
@login_required
def export_pdf(det_id):
    det = _user_detections().filter_by(id=det_id).first_or_404()
    import os
    result_path = os.path.join(current_app.config["RESULT_FOLDER"], det.result_image or "")
    pdf_bytes   = generate_pdf_report(det.to_dict(), result_path)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"roadguard_report_{det_id}.pdf",
    )
