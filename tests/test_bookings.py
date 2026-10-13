"""
tests/test_bookings.py — Tests for demo bookings, rescheduling, and status management.
"""
from datetime import date, timedelta
import pytest
from services.booking_service import (
    create_or_reschedule_booking,
    update_booking_status,
    get_all_bookings,
)

FUTURE_DATE = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")
RESCHEDULE_DATE = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")
PAST_DATE = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")


@pytest.fixture
def seeded_db(temp_db):
    """Temporary SQLite database with 1 seeded lead."""
    temp_db.execute(
        """
        INSERT INTO leads (
            id, student_name, phone, phone_e164, email, class_level,
            exam_goal, interested_course, created_at, updated_at
        ) VALUES (1, 'Priya Patel', '+91 98765 43211', '+919876543211', 'priya@example.com', 12, 'JEE', 'JEE Advanced Preparation', 'now', 'now')
        """
    )
    temp_db.commit()
    return temp_db


def test_booking_creation_success(seeded_db):
    form_data = {
        "lead_id": 1,
        "demo_date": FUTURE_DATE,
        "slot_time": "15:00",
    }
    res = create_or_reschedule_booking(seeded_db, form_data)
    assert res["success"] is True
    assert res["rescheduled"] is False
    assert "booking" in res
    assert res["booking"]["lead_id"] == 1
    assert res["booking"]["slot_time"] == "15:00"
    assert res["booking"]["booking_status"] == "Booked"

    # Verify confirmation message
    assert "Priya Patel" in res["confirmation"]
    assert "3:00 PM" in res["confirmation"]
    assert "https://zoom.us/j/DEMO-PLACEHOLDER" in res["confirmation"]

    count = seeded_db.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
    assert count == 1


def test_past_date_rejection(seeded_db):
    form_data = {
        "lead_id": 1,
        "demo_date": PAST_DATE,
        "slot_time": "15:00",
    }
    res = create_or_reschedule_booking(seeded_db, form_data)
    assert res["success"] is False
    assert "demo_date" in res["errors"]
    assert "future" in res["errors"]["demo_date"]

    count = seeded_db.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
    assert count == 0


def test_invalid_time_slot_rejection(seeded_db):
    form_data = {
        "lead_id": 1,
        "demo_date": FUTURE_DATE,
        "slot_time": "14:00",  # Not in {13:00, 15:00, 17:00, 19:00}
    }
    res = create_or_reschedule_booking(seeded_db, form_data)
    assert res["success"] is False
    assert "slot_time" in res["errors"]


def test_nonexistent_lead_rejection(seeded_db):
    form_data = {
        "lead_id": 9999,
        "demo_date": FUTURE_DATE,
        "slot_time": "13:00",
    }
    res = create_or_reschedule_booking(seeded_db, form_data)
    assert res["success"] is False
    assert "lead_id" in res["errors"]


def test_reschedule_existing_booking(seeded_db):
    # Initial booking
    create_or_reschedule_booking(seeded_db, {
        "lead_id": 1,
        "demo_date": FUTURE_DATE,
        "slot_time": "13:00",
    })
    assert seeded_db.execute("SELECT COUNT(*) FROM bookings").fetchone()[0] == 1

    # Reschedule to a different date and slot
    res2 = create_or_reschedule_booking(seeded_db, {
        "lead_id": 1,
        "demo_date": RESCHEDULE_DATE,
        "slot_time": "19:00",
    })
    assert res2["success"] is True
    assert res2["rescheduled"] is True
    assert "Rescheduled" in res2["confirmation"]

    # Must still maintain exactly one booking row for that student
    assert seeded_db.execute("SELECT COUNT(*) FROM bookings").fetchone()[0] == 1

    row = seeded_db.execute("SELECT demo_date, slot_time FROM bookings WHERE lead_id = 1").fetchone()
    assert row["demo_date"] == RESCHEDULE_DATE
    assert row["slot_time"] == "19:00"


def test_booking_status_updates(seeded_db):
    created = create_or_reschedule_booking(seeded_db, {
        "lead_id": 1,
        "demo_date": FUTURE_DATE,
        "slot_time": "17:00",
    })
    booking_id = created["booking"]["id"]

    # Update to Attended
    res = update_booking_status(seeded_db, booking_id, "Attended")
    assert res["success"] is True

    row = seeded_db.execute("SELECT booking_status FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    assert row["booking_status"] == "Attended"

    # Update to Not Attended
    res = update_booking_status(seeded_db, booking_id, "Not Attended")
    assert res["success"] is True
    row = seeded_db.execute("SELECT booking_status FROM bookings WHERE id = ?", (booking_id,)).fetchone()
    assert row["booking_status"] == "Not Attended"


def test_invalid_status_rejection(seeded_db):
    res = update_booking_status(seeded_db, 1, "Completed")
    assert res["success"] is False
    assert "Status must be one of" in res["message"]


def test_cascade_delete_lead_removes_booking(seeded_db):
    create_or_reschedule_booking(seeded_db, {
        "lead_id": 1,
        "demo_date": FUTURE_DATE,
        "slot_time": "15:00",
    })
    assert seeded_db.execute("SELECT COUNT(*) FROM bookings").fetchone()[0] == 1

    seeded_db.execute("DELETE FROM leads WHERE id = 1")
    seeded_db.commit()

    assert seeded_db.execute("SELECT COUNT(*) FROM bookings").fetchone()[0] == 0
