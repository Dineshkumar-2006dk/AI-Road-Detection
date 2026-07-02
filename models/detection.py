"""Detection history model – one row per AI inference."""

import json
from datetime import datetime
from extensions import db


class Detection(db.Model):
    __tablename__ = "detections"

    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # Files
    original_image = db.Column(db.String(256))   # filename in uploads/
    result_image   = db.Column(db.String(256))   # filename in history/

    # AI Results
    damage_types   = db.Column(db.Text)           # JSON list of detected classes
    confidences    = db.Column(db.Text)           # JSON list of confidence scores
    road_condition = db.Column(db.String(30))     # Good / Moderate / Poor / Critical
    severity       = db.Column(db.String(20))     # Low / Medium / High / Critical
    avg_confidence = db.Column(db.Float, default=0.0)
    detection_count= db.Column(db.Integer, default=0)
    prediction_time= db.Column(db.Float, default=0.0)  # seconds
    max_depth_cm   = db.Column(db.Float, default=0.0)
    total_volume_liters = db.Column(db.Float, default=0.0)

    # GPS
    latitude       = db.Column(db.Float, nullable=True)
    longitude      = db.Column(db.Float, nullable=True)
    location_name  = db.Column(db.String(256), nullable=True)
    maps_link      = db.Column(db.String(512), nullable=True)

    # Notification
    email_sent     = db.Column(db.Boolean, default=False)
    email_recipient= db.Column(db.String(120), nullable=True)
    sms_sent       = db.Column(db.Boolean, default=False)
    sms_recipient  = db.Column(db.String(40), nullable=True)

    # Persistence fallbacks (binary storage for Render ephemeral disk)
    original_image_data = db.Column(db.LargeBinary, nullable=True)
    result_image_data   = db.Column(db.LargeBinary, nullable=True)

    # Meta
    timestamp      = db.Column(db.DateTime, default=datetime.utcnow)
    source         = db.Column(db.String(20), default="image")  # image | camera

    # Relationship
    user           = db.relationship("User", back_populates="detections")

    # ── Helpers ──────────────────────────────────────────────────────────────

    def get_damage_types(self):
        try:
            return json.loads(self.damage_types) if self.damage_types else []
        except Exception:
            return []

    def set_damage_types(self, lst):
        self.damage_types = json.dumps(lst)

    def get_confidences(self):
        try:
            return json.loads(self.confidences) if self.confidences else []
        except Exception:
            return []

    def set_confidences(self, lst):
        self.confidences = json.dumps(lst)

    def to_dict(self):
        return {
            "id":             self.id,
            "user_id":        self.user_id,
            "original_image": self.original_image,
            "result_image":   self.result_image,
            "damage_types":   self.get_damage_types(),
            "confidences":    self.get_confidences(),
            "road_condition": self.road_condition,
            "severity":       self.severity,
            "avg_confidence": round(self.avg_confidence * 100, 1),
            "detection_count":self.detection_count,
            "prediction_time":round(self.prediction_time, 3),
            "max_depth_cm":   self.max_depth_cm,
            "total_volume_liters": self.total_volume_liters,
            "latitude":       self.latitude,
            "longitude":      self.longitude,
            "location_name":  self.location_name,
            "maps_link":      self.maps_link,
            "email_sent":     self.email_sent,
            "sms_sent":       self.sms_sent,
            "sms_recipient":  self.sms_recipient,
            "timestamp":      self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else "",
            "source":         self.source,
        }
