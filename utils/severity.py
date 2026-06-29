"""
Severity and Road Condition Classification
==========================================
Classifies damage severity (Low / Medium / High / Critical) and road
condition (Good / Moderate / Poor / Critical) based on detections.
"""

import numpy as np

# ── Damage weight table ──────────────────────────────────────────────────────
DAMAGE_WEIGHTS = {
    "pothole":            1.0,
    "alligator_crack":    0.90,
    "road_depression":    0.85,
    "patch_failure":      0.80,
    "road_edge_failure":  0.80,
    "water_logging":      0.75,
    "transverse_crack":   0.70,
    "longitudinal_crack": 0.65,
    "surface_damage":     0.60,
    "crack":              0.55,
    "loose_gravel":       0.45,
    "normal_road":        0.00,
    "shadow":             0.00,
    "manhole":            0.10,
    "speed_breaker":      0.05,
    "road_marking":       0.00,
}

DAMAGE_COLORS = {
    "Low":      "#28a745",
    "Medium":   "#ffc107",
    "High":     "#fd7e14",
    "Critical": "#dc3545",
}

CONDITION_COLORS = {
    "Good":     "#28a745",
    "Moderate": "#ffc107",
    "Poor":     "#fd7e14",
    "Critical": "#dc3545",
}


def compute_severity(detections: list, img_bgr=None) -> str:
    """
    Compute overall severity based on:
      - damage class weights
      - confidence scores
      - bounding box area relative to image size
      - count of damage instances
    """
    if not detections:
        return "Low"

    img_area = 1
    if img_bgr is not None:
        h, w = img_bgr.shape[:2]
        img_area = h * w

    scores = []
    for det in detections:
        cls    = det.get("class_name", "")
        conf   = det.get("confidence", 0.5)
        area   = det.get("area", 0)
        weight = DAMAGE_WEIGHTS.get(cls, 0.5)
        area_ratio = min(area / img_area, 1.0) if img_area else 0
        score = weight * conf * (0.6 + 0.4 * area_ratio)
        scores.append(score)

    max_score = max(scores) if scores else 0
    count     = len(scores)

    # Boost for multiple damages
    adjusted = min(max_score + 0.05 * (count - 1), 1.0)

    if adjusted >= 0.75:
        return "Critical"
    elif adjusted >= 0.50:
        return "High"
    elif adjusted >= 0.25:
        return "Medium"
    else:
        return "Low"


def compute_road_condition(detections: list, avg_confidence: float):
    """
    Classify road condition based on detections and confidence.
    Returns (condition_str, hex_color).
    """
    damage_detections = [
        d for d in detections
        if d.get("class_name") not in ("normal_road", "shadow", "road_marking",
                                        "manhole", "speed_breaker")
    ]

    critical_classes = {"pothole", "alligator_crack", "road_depression",
                         "patch_failure", "road_edge_failure"}
    has_critical = any(d["class_name"] in critical_classes for d in damage_detections)
    count = len(damage_detections)

    if count == 0:
        condition = "Good"
    elif has_critical or count >= 4:
        condition = "Critical"
    elif count >= 2 or avg_confidence > 0.70:
        condition = "Poor"
    elif count == 1 and avg_confidence > 0.55:
        condition = "Moderate"
    else:
        condition = "Good"

    return condition, CONDITION_COLORS.get(condition, "#28a745")


def severity_to_badge_class(severity: str) -> str:
    mapping = {
        "Low":      "success",
        "Medium":   "warning",
        "High":     "warning",
        "Critical": "danger",
    }
    return mapping.get(severity, "secondary")


def condition_to_badge_class(condition: str) -> str:
    mapping = {
        "Good":     "success",
        "Moderate": "warning",
        "Poor":     "warning",
        "Critical": "danger",
    }
    return mapping.get(condition, "secondary")
