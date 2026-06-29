"""models package – import all models here so SQLAlchemy sees them."""
from .user import User
from .detection import Detection
from .report import Report
from .settings_model import UserSettings
from .logs import ActivityLog
