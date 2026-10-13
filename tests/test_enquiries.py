"""
tests/test_enquiries.py — Tests for student enquiry submission and duplicate prevention.
"""
import sqlite3
import pytest
from services.enquiry_service import submit_enquiry, get_all_enquiries, get_enquiry_by_id

VALID_FORM = {
    "student_name": "Aarav Sharma",
    "phone": "9876543210",
    "email": "aarav.sharma@example.com",
    "class_level": "11",
    "exam_goal": "NEET",
    "interested_course": "NEET Long-Term Preparation",
}


def test_valid_enquiry_creation(temp_db):
    res = submit_enquiry(temp_db, VALID_FORM)
    assert res["success"] is True
    assert "lead" in res
    assert res["lead"]["phone_e164"] == "+919876543210"
    assert res["lead"]["student_name"] == "Aarav Sharma"

    row = temp_db.execute("SELECT COUNT(*) FROM leads").fetchone()
    assert row[0] == 1


def test_missing_required_fields(temp_db):
    bad_form = {
        "student_name": "",
        "phone": "",
        "email": "",
        "class_level": "",
        "exam_goal": "",
        "interested_course": "",
    }
    res = submit_enquiry(temp_db, bad_form)
    assert res["success"] is False
    assert len(res["errors"]) >= 5


def test_invalid_email(temp_db):
    bad_form = {**VALID_FORM, "email": "not-an-email"}
    res = submit_enquiry(temp_db, bad_form)
    assert res["success"] is False
    assert "email" in res["errors"]


def test_invalid_phone(temp_db):
    bad_form = {**VALID_FORM, "phone": "12345"}
    res = submit_enquiry(temp_db, bad_form)
    assert res["success"] is False
    assert "phone" in res["errors"]


def test_duplicate_phone_rejection(temp_db):
    # First submission
    res1 = submit_enquiry(temp_db, VALID_FORM)
    assert res1["success"] is True

    # Duplicate submission with different formatting (+91 prefix and spaces)
    dup_form = {**VALID_FORM, "phone": "+91 98765 43210"}
    res2 = submit_enquiry(temp_db, dup_form)
    assert res2["success"] is False
    assert res2.get("duplicate") is True
    assert "already registered" in res2["message"]

    count = temp_db.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    assert count == 1


def test_database_uniqueness_enforcement(temp_db):
    # Directly verify SQLite UNIQUE(phone_e164) constraint
    temp_db.execute(
        """
        INSERT INTO leads (
            student_name, phone, phone_e164, email, class_level,
            exam_goal, interested_course, created_at, updated_at
        ) VALUES ('Lead 1', '9876543210', '+919876543210', 'l1@test.com', 11, 'NEET', 'Course', '2026-10-13T10:00:00', '2026-10-13T10:00:00')
        """
    )
    temp_db.commit()

    with pytest.raises(sqlite3.IntegrityError):
        temp_db.execute(
            """
            INSERT INTO leads (
                student_name, phone, phone_e164, email, class_level,
                exam_goal, interested_course, created_at, updated_at
            ) VALUES ('Lead 2', '+91 98765 43210', '+919876543210', 'l2@test.com', 12, 'JEE', 'Course', '2026-10-13T10:00:00', '2026-10-13T10:00:00')
            """
        )
        temp_db.commit()


def test_enquiry_persistence_and_retrieval(temp_db):
    submit_enquiry(temp_db, VALID_FORM)
    submit_enquiry(temp_db, {
        "student_name": "Priya Patel",
        "phone": "9876543211",
        "email": "priya@example.com",
        "class_level": "12",
        "exam_goal": "JEE",
        "interested_course": "JEE Advanced Preparation",
    })

    enquiries = get_all_enquiries(temp_db)
    assert len(enquiries) == 2
    assert enquiries[0]["student_name"] in ["Aarav Sharma", "Priya Patel"]

    lead_id = enquiries[0]["id"]
    single = get_enquiry_by_id(lead_id, temp_db)
    assert single is not None
    assert single["id"] == lead_id


def test_database_transaction_rollback_on_failure(temp_db):
    # Verify that if an exception occurs mid-transaction, database state is consistent
    try:
        temp_db.execute("BEGIN TRANSACTION")
        temp_db.execute(
            """
            INSERT INTO leads (
                student_name, phone, phone_e164, email, class_level,
                exam_goal, interested_course, created_at, updated_at
            ) VALUES ('Temp Lead', '9876543210', '+919876543210', 'tmp@test.com', 11, 'NEET', 'Course', 'now', 'now')
            """
        )
        # Force a failure
        temp_db.execute("INSERT INTO leads (id) VALUES ('invalid')")
        temp_db.commit()
    except Exception:
        temp_db.rollback()

    count = temp_db.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    assert count == 0
