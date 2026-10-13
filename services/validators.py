"""
services/validators.py — Phone normalization and validation engine.
Uses phonenumbers (libphonenumber) with default region 'IN' (India) and E.164 formatting.
Validates email, class level, exam goal, interested course, and demo slot times.
"""
import re
from typing import Optional
import phonenumbers
from phonenumbers import NumberParseException

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_CLASSES = {"Class 11", "Class 12", 11, 12, "11", "12"}
VALID_EXAM_GOALS = {"NEET", "JEE"}

ALLOWED_COURSES = {
    "NEET Long-Term Preparation",
    "NEET Crash Course",
    "JEE Main Preparation",
    "JEE Advanced Preparation",
    "Foundation Course",
    "Other",
}

# Slot mapping between internal representation and human-friendly display
SLOT_TIME_MAP = {
    "13:00": "1:00 PM",
    "15:00": "3:00 PM",
    "17:00": "5:00 PM",
    "19:00": "7:00 PM",
    "1:00 PM": "13:00",
    "3:00 PM": "15:00",
    "5:00 PM": "17:00",
    "7:00 PM": "19:00",
}

VALID_SLOT_TIMES_INTERNAL = {"13:00", "15:00", "17:00", "19:00"}
VALID_TIME_SLOTS = {"1:00 PM", "3:00 PM", "5:00 PM", "7:00 PM", "13:00", "15:00", "17:00", "19:00"}
VALID_BOOKING_STATUSES = {"Booked", "Attended", "Not Attended"}
VALID_STATUSES = VALID_BOOKING_STATUSES

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


# ---------------------------------------------------------------------------
# Phone normalization using libphonenumber
# ---------------------------------------------------------------------------

def normalize_phone_e164(raw: str) -> Optional[str]:
    """
    Validate and normalize a phone number to canonical E.164 format (e.g. +919876543210).
    Default region is 'IN' (India). Supports international numbers if country code is present.
    """
    if not raw or not isinstance(raw, str):
        return None

    cleaned = raw.strip()
    if not cleaned:
        return None

    # Handle 0091 international prefix
    if cleaned.startswith("0091"):
        cleaned = "+91" + cleaned[4:].strip()

    try:
        parsed = phonenumbers.parse(cleaned, "IN")
        if not phonenumbers.is_valid_number(parsed):
            return None

        # If Indian number, ensure it's a 10-digit mobile starting with 6–9
        if parsed.country_code == 91:
            national_str = str(parsed.national_number)
            if len(national_str) != 10 or national_str[0] not in "6789":
                return None

        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except NumberParseException:
        return None
    except Exception:
        return None


def normalize_phone(raw: str) -> Optional[str]:
    """
    Convenience wrapper returning 10-digit national number for Indian numbers
    or digits for backward compatibility.
    """
    e164 = normalize_phone_e164(raw)
    if e164:
        if e164.startswith("+91") and len(e164) == 13:
            return e164[3:]
        return e164.lstrip("+")
    return None


# ---------------------------------------------------------------------------
# Individual field validators
# ---------------------------------------------------------------------------

def validate_student_name(name: str) -> Optional[str]:
    name = (name or "").strip()
    if not name:
        return "Student name is required."
    if len(name) < 2:
        return "Student name must be at least 2 characters."
    if len(name) > 100:
        return "Student name must not exceed 100 characters."
    if not re.match(r"^[a-zA-Z\s'\-\.]+$", name):
        return "Student name may only contain letters, spaces, hyphens, apostrophes, and dots."
    return None


def validate_phone(phone: str) -> Optional[str]:
    phone = (phone or "").strip()
    if not phone:
        return "Phone number is required."
    if normalize_phone_e164(phone) is None:
        return "Enter a valid mobile number (e.g. 10-digit Indian mobile starting with 6–9)."
    return None


def validate_email(email: str) -> Optional[str]:
    email = (email or "").strip()
    if not email:
        return "Email address is required."
    if not EMAIL_RE.match(email):
        return "Enter a valid email address (e.g. student@example.com)."
    return None


def validate_class_level(class_val) -> Optional[str]:
    s = str(class_val or "").strip()
    if s.startswith("Class "):
        s = s.replace("Class ", "").strip()
    if not s:
        return "Please select a class."
    try:
        val = int(s)
        if val not in {11, 12}:
            return "Class must be either 11 or 12."
        return None
    except (ValueError, TypeError):
        return "Class must be either 11 or 12."


validate_student_class = validate_class_level


def validate_exam_goal(goal: str) -> Optional[str]:
    g = (goal or "").strip()
    if not g:
        return "Please select an exam goal."
    if g not in VALID_EXAM_GOALS:
        return "Exam goal must be either NEET or JEE."
    return None


def validate_interested_course(course: str) -> Optional[str]:
    c = (course or "").strip()
    if not c:
        return "Please select or enter an interested course."
    if len(c) > 150:
        return "Course name must not exceed 150 characters."
    return None


validate_course = validate_interested_course


def canonical_slot_time(slot_str: str) -> Optional[str]:
    """Convert display slot (e.g. '3:00 PM') or internal slot ('15:00') to internal '15:00'."""
    slot = (slot_str or "").strip()
    if slot in VALID_SLOT_TIMES_INTERNAL:
        return slot
    if slot in SLOT_TIME_MAP:
        return SLOT_TIME_MAP[slot]
    return None


def display_slot_time(slot_str: str) -> str:
    """Convert internal slot ('15:00') to display '3:00 PM'."""
    slot = (slot_str or "").strip()
    if slot in SLOT_TIME_MAP and ":" in slot and not slot.endswith("M"):
        return SLOT_TIME_MAP[slot]
    return slot


def validate_slot_time(slot_str: str) -> Optional[str]:
    canon = canonical_slot_time(slot_str)
    if canon is None:
        return "Please select one of the four time slots: 1:00 PM, 3:00 PM, 5:00 PM, or 7:00 PM."
    return None


validate_time_slot = validate_slot_time


def validate_booking_status(status: str) -> Optional[str]:
    st = (status or "").strip()
    if not st:
        return "Please select a booking status."
    if st not in VALID_BOOKING_STATUSES:
        return f"Status must be one of: {', '.join(sorted(VALID_BOOKING_STATUSES))}."
    return None


# ---------------------------------------------------------------------------
# Aggregate enquiry validation
# ---------------------------------------------------------------------------

def validate_enquiry_form(data: dict) -> dict:
    errors: dict[str, str] = {}

    err = validate_student_name(data.get("student_name", ""))
    if err:
        errors["student_name"] = err

    err = validate_phone(data.get("phone", ""))
    if err:
        errors["phone"] = err

    err = validate_email(data.get("email", ""))
    if err:
        errors["email"] = err

    # Smart detection of class field name
    class_key = "student_class" if "student_class" in data else "class_level"
    class_val = data.get(class_key)
    err = validate_class_level(class_val)
    if err:
        errors[class_key] = err

    err = validate_exam_goal(data.get("exam_goal", ""))
    if err:
        errors["exam_goal"] = err

    # Smart detection of course field name
    course_key = "course" if "course" in data else "interested_course"
    course_val = data.get(course_key)
    err = validate_interested_course(course_val)
    if err:
        errors[course_key] = err

    return errors
