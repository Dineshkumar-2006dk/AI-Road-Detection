"""
Authentication Blueprint
=========================
Handles login, register, logout, forgot-password.
"""

from datetime import datetime
from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, session, make_response)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models.user import User
from models.settings_model import UserSettings
from utils.security import sanitize_string, sanitize_email, log_activity

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        email    = sanitize_email(request.form.get("email", ""))
        password = request.form.get("password", "")
        remember = request.form.get("remember_me") == "on"

        if not email or not password:
            flash("Please enter email and password.", "warning")
            return render_template("auth/login.html")

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password) and user.is_active:
            session.permanent = False
            login_user(user, remember=False)
            user.last_login = datetime.utcnow()
            db.session.commit()
            log_activity("login", f"User {user.username} logged in")
            next_page = request.args.get("next")
            flash(f"Welcome back, {user.username}! 👋", "success")
            return redirect(next_page or url_for("dashboard.dashboard"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        username  = sanitize_string(request.form.get("username", ""), 80)
        email     = sanitize_email(request.form.get("email", ""))
        password  = request.form.get("password", "")
        confirm   = request.form.get("confirm_password", "")

        # Validation
        if len(username) < 3:
            flash("Username must be at least 3 characters.", "danger")
            return render_template("auth/register.html")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("auth/register.html")
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return render_template("auth/register.html")
        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "warning")
            return render_template("auth/register.html")

        new_user = User(
            username = username,
            email    = email,
            password = generate_password_hash(password),
            role     = "user",
            is_active= True,
        )
        db.session.add(new_user)
        db.session.flush()   # get new_user.id

        # Default settings
        settings = UserSettings(user_id=new_user.id)
        db.session.add(settings)
        db.session.commit()

        log_activity("register", f"New user: {username}")
        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        log_activity("logout", f"User {current_user.username} logged out")
        logout_user()
    session.clear()
    response = make_response(redirect(url_for("auth.login")))
    response.set_cookie("session", "", expires=0)
    response.set_cookie("remember_token", "", expires=0)
    flash("You have been logged out.", "info")
    return response


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = sanitize_email(request.form.get("email", ""))
        user  = User.query.filter_by(email=email).first()
        # Always show same message to prevent email enumeration
        flash("If that email is registered, you will receive reset instructions.", "info")
        # TODO: implement token-based reset email
    return render_template("auth/forgot_password.html")


# ── Landing page (public) ────────────────────────────────────────────────────
@auth_bp.route("/home")
def home():
    return render_template("index.html")
