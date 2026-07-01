"""Per-user application settings model."""

from extensions import db


class UserSettings(db.Model):
    __tablename__ = "user_settings"

    id                = db.Column(db.Integer, primary_key=True)
    user_id           = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True)

    # Detection
    conf_threshold    = db.Column(db.Float,   default=0.40)
    nms_threshold     = db.Column(db.Float,   default=0.45)

    # UI / Preferences
    theme             = db.Column(db.String(10), default="dark")   # dark | light
    language          = db.Column(db.String(5),  default="en")     # en | ta

    # Features
    voice_enabled     = db.Column(db.Boolean, default=True)
    email_alerts      = db.Column(db.Boolean, default=False)
    notification_email= db.Column(db.String(120), nullable=True)

    # Camera
    camera_index      = db.Column(db.Integer, default=0)
    camera_fps        = db.Column(db.Integer, default=10)

    # SMTP Custom Configuration
    smtp_server       = db.Column(db.String(120), default="smtp.gmail.com")
    smtp_port         = db.Column(db.Integer,     default=587)
    smtp_username     = db.Column(db.String(120), nullable=True)
    smtp_password     = db.Column(db.String(120), nullable=True)

    # Twilio SMS Configuration
    sms_alerts        = db.Column(db.Boolean,     default=False)
    sms_sid           = db.Column(db.String(120), nullable=True)
    sms_token         = db.Column(db.String(120), nullable=True)
    sms_from          = db.Column(db.String(40),  nullable=True)
    sms_to            = db.Column(db.String(40),  nullable=True)
    sms_mode          = db.Column(db.String(20),  default="sms")   # sms | whatsapp

    # Relationship
    user              = db.relationship("User", back_populates="settings")

    def to_dict(self):
        return {
            "conf_threshold":     self.conf_threshold,
            "nms_threshold":      self.nms_threshold,
            "theme":              self.theme,
            "language":           self.language,
            "voice_enabled":      self.voice_enabled,
            "email_alerts":       self.email_alerts,
            "notification_email": self.notification_email,
            "camera_index":       self.camera_index,
            "camera_fps":         self.camera_fps,
            "smtp_server":        self.smtp_server,
            "smtp_port":          self.smtp_port,
            "smtp_username":      self.smtp_username,
            "smtp_password":      self.smtp_password,
            "sms_alerts":         self.sms_alerts,
            "sms_sid":            self.sms_sid,
            "sms_token":          self.sms_token,
            "sms_from":           self.sms_from,
            "sms_to":             self.sms_to,
            "sms_mode":           self.sms_mode,
        }
