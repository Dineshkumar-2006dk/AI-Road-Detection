"""Report model – tracks generated PDF / Excel exports."""

from datetime import datetime
from extensions import db


class Report(db.Model):
    __tablename__ = "reports"

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    detection_id = db.Column(db.Integer, db.ForeignKey("detections.id"), nullable=True)
    report_type  = db.Column(db.String(20))   # "pdf" | "excel" | "csv"
    filename     = db.Column(db.String(256))
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":           self.id,
            "report_type":  self.report_type,
            "filename":     self.filename,
            "created_at":   self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
