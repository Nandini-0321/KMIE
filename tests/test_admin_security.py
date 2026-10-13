"""
tests/test_admin_security.py — Tests for admin route security, authentication, and health probes.
"""
import pytest
from app import app
from services.auth_service import verify_admin_login


def test_health_live_endpoint(client):
    res = client.get("/health/live")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "alive"
    assert data["service"] == "kmie-booking-system"


def test_health_ready_endpoint(client):
    res = client.get("/health/ready")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ready"
    assert data["database"] == "ok"


def test_unauthorized_admin_access_redirects(client):
    # Attempting to access admin dashboard without login should redirect
    res = client.get("/admin/dashboard", follow_redirects=False)
    assert res.status_code == 302
    assert "/admin/login" in res.headers["Location"]


def test_admin_login_wrong_credentials(client):
    res = client.post("/admin/login", data={"username": "wrong", "password": "badpassword"})
    assert res.status_code == 200
    assert b"Invalid administrator username or password" in res.data


def test_admin_login_and_logout_flow(client):
    # Login with default admin credentials
    res = client.post(
        "/admin/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Admin Management Console" in res.data

    # Access dashboard while authenticated
    dash_res = client.get("/admin/dashboard")
    assert dash_res.status_code == 200
    assert b"Student Leads" in dash_res.data

    # Logout
    logout_res = client.get("/admin/logout", follow_redirects=True)
    assert logout_res.status_code == 200
    assert b"logged out safely" in logout_res.data

    # Accessing dashboard after logout redirects again
    post_logout = client.get("/admin/dashboard", follow_redirects=False)
    assert post_logout.status_code == 302
