"""
tests/test_routes.py — End-to-end integration tests for Flask routes and template rendering.
"""
import pytest
from app import app


def test_index_page_renders_successfully(client):
    """Verify that the home page (index.html) renders with HTTP 200 without template errors."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"KMIE" in resp.data
    assert b"New Student Enquiry" in resp.data
    assert b"Book a Demo Session" in resp.data
    assert b"Dashboard Overview" in resp.data


def test_submit_enquiry_and_render(client):
    """Verify enquiry submission redirects back to index and renders newly submitted student."""
    post_data = {
        "student_name": "Test Student Route",
        "phone": "9811122233",
        "email": "test.route@example.com",
        "class_level": "12",
        "exam_goal": "JEE",
        "interested_course": "JEE Advanced Preparation",
    }
    resp = client.post("/enquiry/submit", data=post_data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Test Student Route" in resp.data


def test_create_booking_and_render(client):
    """Verify demo booking can be scheduled and rendered in the bookings table."""
    # First submit enquiry
    lead_data = {
        "student_name": "Booking Candidate",
        "phone": "9822233344",
        "email": "candidate@example.com",
        "class_level": "11",
        "exam_goal": "NEET",
        "interested_course": "NEET Crash Course",
    }
    client.post("/enquiry/submit", data=lead_data, follow_redirects=True)

    # Get enquiries to find the ID
    api_resp = client.get("/api/enquiries")
    assert api_resp.status_code == 200
    leads = api_resp.get_json()["data"]
    lead = next(l for l in leads if l["email"] == "candidate@example.com")

    # Schedule demo
    booking_data = {
        "lead_id": str(lead["id"]),
        "demo_date": "2026-12-01",
        "slot_time": "15:00",
    }
    b_resp = client.post("/booking/schedule", data=booking_data, follow_redirects=True)
    assert b_resp.status_code == 200
    assert b"Demo Booking" in b_resp.data


def test_update_status_route(client):
    """Verify booking status update route updates and renders properly."""
    # Query existing bookings
    resp = client.get("/")
    assert resp.status_code == 200

    # Submit status update for booking 1
    update_data = {
        "booking_id": "1",
        "status": "Attended",
    }
    post_resp = client.post("/booking/update-status", data=update_data, follow_redirects=True)
    assert post_resp.status_code == 200
    assert b"Booking status updated" in post_resp.data


def test_admin_dashboard_rendering(client):
    """Verify admin login and dashboard rendering with leads, filters, and bookings."""
    # Login
    login_resp = client.post(
        "/admin/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=True,
    )
    assert login_resp.status_code == 200
    assert b"Admin Management Console" in login_resp.data

    # Filter dashboard
    filter_resp = client.get("/admin/dashboard?goal_filter=NEET")
    assert filter_resp.status_code == 200
    assert b"Admin Management Console" in filter_resp.data
