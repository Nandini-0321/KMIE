"""
tests/test_find_booking.py — Test suite for Find My Demo Booking retrieval feature.
Verifies lookup by ID, Phone, and Email, data masking, unbooked lead handling,
validation, and HTTP endpoints.
"""
import time
import pytest
from database.db import get_db_connection
from services.enquiry_service import submit_enquiry
from services.booking_service import (
    create_or_reschedule_booking,
    find_booking_or_enquiry,
    mask_phone,
    mask_email,
)


def _unique_phone():
    return f"98{str(time.time_ns())[-8:]}"


def test_masking_helpers():
    """Verify phone and email masking functions protect sensitive data."""
    # Phone masking
    assert mask_phone("+919876543210") == "+91 ******3210"
    assert mask_phone("9876543210") == "******3210"
    assert mask_phone("123") == "****"
    assert mask_phone("") == ""

    # Email masking
    assert mask_email("student@example.com") == "s*****t@example.com"
    assert mask_email("ab@example.com") == "a*@example.com"
    assert mask_email("a@example.com") == "a*@example.com"
    assert mask_email("invalid-email") == ""


def test_find_booking_by_id(client):
    """Find an existing booking using its Booking reference ID and Enquiry ID."""
    test_phone = _unique_phone()
    # 1. Create enquiry
    enq_res = submit_enquiry({
        "student_name": "Rohan Verma",
        "phone": test_phone,
        "email": f"rohan_{test_phone}@example.com",
        "class_level": "11",
        "exam_goal": "JEE",
        "interested_course": "JEE Main Preparation",
    })
    assert enq_res["success"] is True
    lead_id = enq_res["lead"]["id"]

    # 2. Schedule demo booking
    book_res = create_or_reschedule_booking({
        "lead_id": str(lead_id),
        "demo_date": "2026-11-15",
        "slot_time": "15:00",
    })
    assert book_res["success"] is True
    booking_id = book_res["booking"]["id"]

    # 3. Lookup by booking ID
    res1 = find_booking_or_enquiry("id", str(booking_id))
    assert res1["success"] is True
    assert res1["has_booking"] is True
    assert res1["data"]["student_name"] == "Rohan Verma"
    assert res1["data"]["booking_id"] == booking_id
    assert res1["data"]["lead_id"] == lead_id
    assert res1["data"]["slot_time"] == "15:00"
    assert "3:00 PM" in res1["data"]["slot_time_display"]
    assert test_phone[-4:] in res1["data"]["phone_masked"]
    assert "@example.com" in res1["data"]["email_masked"]

    # 4. Lookup by lead ID (with '#' prefix like '#1')
    res2 = find_booking_or_enquiry("id", f"#{lead_id}")
    assert res2["success"] is True
    assert res2["has_booking"] is True
    assert res2["data"]["booking_id"] == booking_id


def test_find_booking_by_phone_with_formatting(client):
    """Find an existing booking using different phone number formatting."""
    test_phone = _unique_phone()
    enq_res = submit_enquiry({
        "student_name": "Priya Patel",
        "phone": test_phone,
        "email": f"priya_{test_phone}@example.com",
        "class_level": "12",
        "exam_goal": "NEET",
        "interested_course": "NEET Long-Term Preparation",
    })
    assert enq_res["success"] is True
    lead_id = enq_res["lead"]["id"]

    create_or_reschedule_booking({
        "lead_id": str(lead_id),
        "demo_date": "2026-11-16",
        "slot_time": "17:00",
    })

    # Search with 10 digits
    res1 = find_booking_or_enquiry("phone", test_phone)
    assert res1["success"] is True
    assert res1["data"]["student_name"] == "Priya Patel"

    # Search with spaces and +91
    spaced_phone = f"+91 {test_phone[:5]} {test_phone[5:]}"
    res2 = find_booking_or_enquiry("phone", spaced_phone)
    assert res2["success"] is True
    assert res2["data"]["student_name"] == "Priya Patel"

    # Search with dashes
    dashed_phone = f"{test_phone[:5]}-{test_phone[5:]}"
    res3 = find_booking_or_enquiry("phone", dashed_phone)
    assert res3["success"] is True
    assert res3["data"]["student_name"] == "Priya Patel"


def test_find_booking_by_email(client):
    """Find an existing booking using email address with case and whitespace insensitivity."""
    test_phone = _unique_phone()
    email = f"aditya_{test_phone}@example.com"
    enq_res = submit_enquiry({
        "student_name": "Aditya Singh",
        "phone": test_phone,
        "email": email,
        "class_level": "11",
        "exam_goal": "JEE",
        "interested_course": "JEE Advanced Preparation",
    })
    assert enq_res["success"] is True
    lead_id = enq_res["lead"]["id"]

    create_or_reschedule_booking({
        "lead_id": str(lead_id),
        "demo_date": "2026-11-20",
        "slot_time": "19:00",
    })

    # Search with leading/trailing spaces and uppercase
    res = find_booking_or_enquiry("email", f"  {email.upper()}  ")
    assert res["success"] is True
    assert res["data"]["student_name"] == "Aditya Singh"
    assert res["data"]["slot_time"] == "19:00"


def test_find_registered_enquiry_without_booking(client):
    """Search for a registered student who has not booked a demo yet."""
    test_phone = _unique_phone()
    enq_res = submit_enquiry({
        "student_name": "Meera Nair",
        "phone": test_phone,
        "email": f"meera_{test_phone}@example.com",
        "class_level": "12",
        "exam_goal": "NEET",
        "interested_course": "NEET Crash Course",
    })
    assert enq_res["success"] is True
    lead_id = enq_res["lead"]["id"]

    res = find_booking_or_enquiry("phone", test_phone)
    assert res["success"] is True
    assert res["has_booking"] is False
    assert res["data"]["student_name"] == "Meera Nair"
    assert res["data"]["booking_id"] is None
    assert res["data"]["booking_status"] == "Registered — Demo Not Yet Booked"


def test_find_nonexistent_and_invalid_inputs(client):
    """Test nonexistent records and invalid input queries."""
    # Nonexistent ID
    res1 = find_booking_or_enquiry("id", "999999")
    assert res1["success"] is False
    assert res1["not_found"] is True
    assert "couldn't find a matching record" in res1["message"]

    # Nonexistent Phone
    res2 = find_booking_or_enquiry("phone", "9111111111")
    assert res2["success"] is False
    assert res2["not_found"] is True

    # Invalid ID
    res3 = find_booking_or_enquiry("id", "abc")
    assert res3["success"] is False
    assert "valid numeric reference ID" in res3["error"]

    # Invalid Phone
    res4 = find_booking_or_enquiry("phone", "123")
    assert res4["success"] is False
    assert "valid 10-digit mobile number" in res4["error"]

    # Invalid Email
    res5 = find_booking_or_enquiry("email", "not-an-email")
    assert res5["success"] is False
    assert "valid email address" in res5["error"]


def test_find_booking_http_endpoint(client):
    """Test /booking/find endpoint via GET and POST requests."""
    test_phone = _unique_phone()
    # Create test lead & booking
    enq_res = submit_enquiry({
        "student_name": "Tanvi Joshi",
        "phone": test_phone,
        "email": f"tanvi_{test_phone}@example.com",
        "class_level": "11",
        "exam_goal": "NEET",
        "interested_course": "Foundation Course",
    })
    lead_id = enq_res["lead"]["id"]

    create_or_reschedule_booking({
        "lead_id": str(lead_id),
        "demo_date": "2026-11-25",
        "slot_time": "13:00",
    })

    # AJAX GET request
    resp = client.get(
        f"/booking/find?search_type=phone&search_value={test_phone}",
        headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"},
    )
    assert resp.status_code == 200
    json_data = resp.get_json()
    assert json_data["success"] is True
    assert json_data["data"]["student_name"] == "Tanvi Joshi"

    # Nonexistent AJAX GET -> 404
    resp_nf = client.get(
        "/booking/find?search_type=id&search_value=888888",
        headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"},
    )
    assert resp_nf.status_code == 404
    assert resp_nf.get_json()["not_found"] is True
