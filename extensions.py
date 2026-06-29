"""
extensions.py – Shared Flask extension instances
==================================================
Import db, login_mgr, csrf from here (NOT from app.py) to avoid circular imports.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db        = SQLAlchemy()
login_mgr = LoginManager()
csrf      = CSRFProtect()
