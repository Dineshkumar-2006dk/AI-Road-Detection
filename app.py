"""
RoadGuard AI – Application Factory
====================================
Entry point: python app.py
"""

import os
from flask import Flask, redirect, url_for, make_response, request
from config import Config
from extensions import db, login_mgr, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ── Create required directories ──────────────────────────────────────────
    for folder in [
        app.config["UPLOAD_FOLDER"],
        app.config["RESULT_FOLDER"],
        app.config["REPORT_FOLDER"],
        os.path.join(app.root_path, "database"),
        os.path.join(app.root_path, "weights"),
        os.path.join(app.root_path, "static", "uploads"),
    ]:
        os.makedirs(folder, exist_ok=True)

    # ── Initialise extensions ────────────────────────────────────────────────
    db.init_app(app)
    csrf.init_app(app)

    login_mgr.init_app(app)
    login_mgr.login_view             = "auth.login"
    login_mgr.login_message          = "Please log in to access this page."
    login_mgr.login_message_category = "warning"

    # ── User loader (Flask-Login) ────────────────────────────────────────────
    @login_mgr.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))

    # ── Register Blueprints ──────────────────────────────────────────────────
    from routes.auth       import auth_bp
    from routes.detection  import detection_bp
    from routes.dashboard  import dashboard_bp
    from routes.history    import history_bp
    from routes.map_routes import map_bp
    from routes.admin      import admin_bp
    from routes.settings   import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(detection_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(map_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(settings_bp)

    # ── Root redirect ────────────────────────────────────────────────────────
    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    # ── No-cache headers for protected pages (fixes back-button bypass) ──────
    @app.after_request
    def add_no_cache_headers(response):
        # Apply to all HTML pages (not static assets)
        if response.content_type and "text/html" in response.content_type:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"]        = "no-cache"
            response.headers["Expires"]       = "0"
        return response

    # ── Create DB tables & seed admin ───────────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed_admin(app)

    return app


def _seed_admin(app):
    """Create default admin account if not present."""
    from models.user import User
    from werkzeug.security import generate_password_hash
    if not User.query.filter_by(email=app.config["ADMIN_EMAIL"]).first():
        admin = User(
            username="admin",
            email=app.config["ADMIN_EMAIL"],
            password=generate_password_hash(app.config["ADMIN_PASSWORD"]),
            role="admin",
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()
        print(f"[RoadGuard] Admin seeded: {app.config['ADMIN_EMAIL']}")


# ── Application instance ─────────────────────────────────────────────────────
application = create_app()

if __name__ == "__main__":
    application.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False,  # Prevent double model load on Windows
    )
