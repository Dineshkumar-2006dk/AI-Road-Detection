"""Activity log model – tracks user actions for admin audit trail."""

from datetime import datetime
from extensions import db


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action     = db.Column(db.String(120))
    details    = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="logs")

    def to_dict(self):
        return {
            "id":        self.id,
            "user_id":   self.user_id,
            "action":    self.action,
            "details":   self.details,
            "ip":        self.ip_address,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }
