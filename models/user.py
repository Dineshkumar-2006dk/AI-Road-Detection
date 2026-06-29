"""User model with Flask-Login integration."""

from datetime import datetime
from flask_login import UserMixin
from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80),  unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(256), nullable=False)
    role       = db.Column(db.String(20),  default="user")   # "admin" | "user"
    is_active  = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    detections = db.relationship("Detection",    back_populates="user", lazy="dynamic")
    settings   = db.relationship("UserSettings", back_populates="user", uselist=False)
    logs       = db.relationship("ActivityLog",  back_populates="user", lazy="dynamic")

    def __repr__(self):
        return f"<User {self.username} [{self.role}]>"

    def to_dict(self):
        return {
            "id":         self.id,
            "username":   self.username,
            "email":      self.email,
            "role":       self.role,
            "is_active":  self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
