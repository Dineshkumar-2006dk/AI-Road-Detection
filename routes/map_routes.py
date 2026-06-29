"""Map Blueprint – Interactive Folium map of all detections."""

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.detection import Detection
from utils.gps_utils import build_folium_map

map_bp = Blueprint("map", __name__, url_prefix="/map")


@map_bp.route("/")
@login_required
def road_map():
    if current_user.role == "admin":
        detections = Detection.query.filter(
            Detection.latitude.isnot(None),
            Detection.longitude.isnot(None)
        ).all()
    else:
        detections = Detection.query.filter_by(user_id=current_user.id).filter(
            Detection.latitude.isnot(None),
            Detection.longitude.isnot(None)
        ).all()

    map_html = build_folium_map(detections)
    return render_template("map/map.html", map_html=map_html,
                           total_markers=len(detections))
