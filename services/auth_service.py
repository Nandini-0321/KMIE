"""
services/auth_service.py — Administrator Authentication and Session Security.
Uses Werkzeug password hashing (scrypt/pbkdf2) and session-based protection.
"""
import functools
import logging
import os
from flask import session, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash

logger = logging.getLogger(__name__)

# Default demo credentials (used only if not supplied in environment)
DEFAULT_ADMIN_USER = "admin"
# Hash for 'admin123'
DEFAULT_ADMIN_HASH = generate_password_hash("admin123", method="scrypt")


def get_admin_credentials():
    """Return tuple of (username, password_hash)."""
    username = os.getenv("ADMIN_USERNAME", "").strip() or DEFAULT_ADMIN_USER
    pwd_hash = os.getenv("ADMIN_PASSWORD_HASH", "").strip() or DEFAULT_ADMIN_HASH
    return username, pwd_hash


def verify_admin_login(username: str, password: str) -> bool:
    """Validate username and password hash."""
    expected_user, expected_hash = get_admin_credentials()
    if username.strip() != expected_user:
        return False
    return check_password_hash(expected_hash, password)


def admin_required(f):
    """Decorator to protect admin routes from unauthenticated access."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Please log in with administrator credentials to access this area.", "error")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function
