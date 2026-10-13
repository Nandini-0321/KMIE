"""
tests/test_validators.py

Unit tests for normalize_phone() and all field validators.
No external database connection required — pure Python logic tests.
"""
import pytest
from services.validators import (
    normalize_phone,
    validate_student_name,
    validate_phone,
    validate_email,
    validate_student_class,
    validate_exam_goal,
    validate_course,
    validate_enquiry_form,
    validate_time_slot,
    validate_booking_status,
    VALID_TIME_SLOTS,
    VALID_STATUSES,
)


# ============================================================
# normalize_phone — valid formats
# ============================================================

class TestNormalizePhoneValid:
    """All these inputs must resolve to '9876543210'."""

    TARGET = "9876543210"

    def test_plain_10_digit(self):
        assert normalize_phone("9876543210") == self.TARGET

    def test_spaces(self):
        assert normalize_phone("98765 43210") == self.TARGET

    def test_hyphens(self):
        assert normalize_phone("98765-43210") == self.TARGET

    def test_plus91_space(self):
        assert normalize_phone("+91 98765 43210") == self.TARGET

    def test_plus91_hyphen(self):
        assert normalize_phone("+91-98765-43210") == self.TARGET

    def test_0091_prefix(self):
        assert normalize_phone("0091 9876543210") == self.TARGET

    def test_leading_zero(self):
        assert normalize_phone("09876543210") == self.TARGET

    def test_plus91_no_space(self):
        assert normalize_phone("+919876543210") == self.TARGET

    def test_extra_spaces_around(self):
        assert normalize_phone("  +91 9876543210  ") == self.TARGET


# ============================================================
# normalize_phone — invalid inputs
# ============================================================

class TestNormalizePhoneInvalid:

    def test_empty_string(self):
        assert normalize_phone("") is None

    def test_none_input(self):
        assert normalize_phone(None) is None

    def test_alphabetic(self):
        assert normalize_phone("abcdefghij") is None

    def test_too_short(self):
        assert normalize_phone("98765") is None

    def test_too_long(self):
        assert normalize_phone("98765432109876") is None

    def test_starts_with_1(self):
        """Indian mobile must start with 6–9."""
        assert normalize_phone("1234567890") is None

    def test_starts_with_5(self):
        assert normalize_phone("5876543210") is None

    def test_invalid_after_strip(self):
        assert normalize_phone("+91 123-456-7890") is None

    def test_whitespace_only(self):
        assert normalize_phone("   ") is None


# ============================================================
# validate_student_name
# ============================================================

class TestValidateStudentName:

    def test_valid_name(self):
        assert validate_student_name("Aarav Sharma") is None

    def test_valid_with_hyphen(self):
        assert validate_student_name("Mary-Jane Watson") is None

    def test_empty(self):
        assert validate_student_name("") is not None

    def test_whitespace_only(self):
        assert validate_student_name("  ") is not None

    def test_too_short(self):
        assert validate_student_name("A") is not None

    def test_too_long(self):
        assert validate_student_name("A" * 101) is not None

    def test_numbers_in_name(self):
        assert validate_student_name("Aarav123") is not None


# ============================================================
# validate_phone
# ============================================================

class TestValidatePhone:

    def test_valid_phone(self):
        assert validate_phone("9876543210") is None

    def test_valid_plus91(self):
        assert validate_phone("+91 98765 43210") is None

    def test_empty(self):
        assert validate_phone("") is not None

    def test_invalid(self):
        assert validate_phone("12345") is not None

    def test_alpha(self):
        assert validate_phone("ABCDEABCDE") is not None


# ============================================================
# validate_email
# ============================================================

class TestValidateEmail:

    def test_valid_email(self):
        assert validate_email("student@example.com") is None

    def test_valid_subdomain(self):
        assert validate_email("s@mail.co.in") is None

    def test_empty(self):
        assert validate_email("") is not None

    def test_no_at(self):
        assert validate_email("studentexample.com") is not None

    def test_no_domain(self):
        assert validate_email("student@") is not None

    def test_no_tld(self):
        assert validate_email("student@example") is not None


# ============================================================
# validate_student_class
# ============================================================

class TestValidateStudentClass:

    def test_class_11(self):
        assert validate_student_class("Class 11") is None

    def test_class_12(self):
        assert validate_student_class("Class 12") is None

    def test_empty(self):
        assert validate_student_class("") is not None

    def test_invalid(self):
        assert validate_student_class("Class 10") is not None

    def test_lowercase(self):
        assert validate_student_class("class 11") is not None


# ============================================================
# validate_exam_goal
# ============================================================

class TestValidateExamGoal:

    def test_neet(self):
        assert validate_exam_goal("NEET") is None

    def test_jee(self):
        assert validate_exam_goal("JEE") is None

    def test_empty(self):
        assert validate_exam_goal("") is not None

    def test_invalid(self):
        assert validate_exam_goal("IIT") is not None

    def test_lowercase(self):
        assert validate_exam_goal("neet") is not None


# ============================================================
# validate_course
# ============================================================

class TestValidateCourse:

    def test_valid_course(self):
        assert validate_course("NEET Foundation") is None

    def test_empty(self):
        assert validate_course("") is not None

    def test_too_long(self):
        assert validate_course("A" * 151) is not None


# ============================================================
# validate_enquiry_form (aggregate)
# ============================================================

class TestValidateEnquiryForm:

    VALID_DATA = {
        "student_name": "Test Student",
        "phone": "9876543210",
        "email": "test@example.com",
        "student_class": "Class 11",
        "exam_goal": "NEET",
        "course": "NEET Foundation",
    }

    def test_all_valid(self):
        errors = validate_enquiry_form(self.VALID_DATA)
        assert errors == {}

    def test_missing_name(self):
        data = {**self.VALID_DATA, "student_name": ""}
        errors = validate_enquiry_form(data)
        assert "student_name" in errors

    def test_invalid_phone(self):
        data = {**self.VALID_DATA, "phone": "12345"}
        errors = validate_enquiry_form(data)
        assert "phone" in errors

    def test_invalid_email(self):
        data = {**self.VALID_DATA, "email": "notanemail"}
        errors = validate_enquiry_form(data)
        assert "email" in errors

    def test_invalid_class(self):
        data = {**self.VALID_DATA, "student_class": "Class 10"}
        errors = validate_enquiry_form(data)
        assert "student_class" in errors

    def test_invalid_exam_goal(self):
        data = {**self.VALID_DATA, "exam_goal": "SAT"}
        errors = validate_enquiry_form(data)
        assert "exam_goal" in errors

    def test_missing_course(self):
        data = {**self.VALID_DATA, "course": ""}
        errors = validate_enquiry_form(data)
        assert "course" in errors

    def test_multiple_errors(self):
        data = {
            "student_name": "",
            "phone": "",
            "email": "",
            "student_class": "",
            "exam_goal": "",
            "course": "",
        }
        errors = validate_enquiry_form(data)
        assert len(errors) == 6


# ============================================================
# validate_time_slot
# ============================================================

class TestValidateTimeSlot:

    def test_all_valid_slots(self):
        for slot in ["1:00 PM", "3:00 PM", "5:00 PM", "7:00 PM"]:
            assert validate_time_slot(slot) is None

    def test_empty(self):
        assert validate_time_slot("") is not None

    def test_invalid_slot(self):
        assert validate_time_slot("2:00 PM") is not None

    def test_lowercase_invalid(self):
        assert validate_time_slot("1:00 pm") is not None


# ============================================================
# validate_booking_status
# ============================================================

class TestValidateBookingStatus:

    def test_booked(self):
        assert validate_booking_status("Booked") is None

    def test_attended(self):
        assert validate_booking_status("Attended") is None

    def test_not_attended(self):
        assert validate_booking_status("Not Attended") is None

    def test_empty(self):
        assert validate_booking_status("") is not None

    def test_invalid(self):
        assert validate_booking_status("Pending") is not None

    def test_case_sensitive(self):
        assert validate_booking_status("booked") is not None
