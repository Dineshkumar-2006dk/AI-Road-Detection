"""
Security Utilities
===================
File validation, input sanitization, and helper decorators.
"""

import os
import re
import functools
from flask import abort, flash, redirect, url_for, request, current_app
from flask_login import current_user


ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp"}
MAX_FILE_SIZE_MB   = 32


def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def validate_image(file_storage) -> tuple[bool, str]:
    """
    Validate an uploaded image FileStorage object.
    Returns (is_valid, error_message).
    """
    if not file_storage or file_storage.filename == "":
        return False, "No file selected."

    if not allowed_file(file_storage.filename):
        return False, f"File type not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}"

    # Check file size
    file_storage.seek(0, 2)
    size_mb = file_storage.tell() / (1024 * 1024)
    file_storage.seek(0)
    if size_mb > MAX_FILE_SIZE_MB:
        return False, f"File too large ({size_mb:.1f} MB). Maximum: {MAX_FILE_SIZE_MB} MB."

    # Basic magic byte check
    header = file_storage.read(12)
    file_storage.seek(0)
    if not _is_valid_image_header(header):
        return False, "Invalid image file. File content does not match its extension."

    return True, ""


def _is_valid_image_header(header: bytes) -> bool:
    """Verify magic bytes for common image formats."""
    if header[:3] == b"\xff\xd8\xff":          # JPEG
        return True
    if header[:8] == b"\x89PNG\r\n\x1a\n":     # PNG
        return True
    if header[:2] in (b"BM",):                  # BMP
        return True
    if header[:6] in (b"GIF87a", b"GIF89a"):   # GIF (not used but harmless)
        return True
    return False


def sanitize_string(value: str, max_length: int = 256) -> str:
    """Remove potentially dangerous characters and truncate."""
    if not value:
        return ""
    # Strip HTML tags
    clean = re.sub(r"<[^>]+>", "", str(value))
    # Remove SQL meta characters
    clean = re.sub(r"[;\'\"\-\-]", "", clean)
    return clean[:max_length].strip()


def sanitize_email(email: str) -> str:
    """Basic email sanitization."""
    return re.sub(r"[^a-zA-Z0-9@._\-+]", "", str(email))[:120]


def admin_required(f):
    """Decorator: require admin role."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.role != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated


def log_activity(action: str, details: str = ""):
    """Helper to write an activity log entry."""
    try:
        from extensions import db
        from models.logs import ActivityLog
        entry = ActivityLog(
            user_id    = current_user.id if current_user.is_authenticated else None,
            action     = action[:120],
            details    = details[:500] if details else None,
            ip_address = request.remote_addr,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"[Log] Failed: {e}")


def get_client_ip() -> str:
    """Get real client IP behind proxies."""
    x_forwarded = request.headers.get("X-Forwarded-For")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"
