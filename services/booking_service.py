"""
services/booking_service.py — Business logic for demo bookings.
Uses SQLite bookings table with UNIQUE(lead_id) constraint.
Supports demo creation, rescheduling (in-place update), status management,
and Google Sheets synchronization hooks.
"""
import logging
import os
import sqlite3
from datetime import date, datetime, timezone
from typing import Optional, List, Dict

from database.db import get_db_connection
from services.validators import (
    canonical_slot_time,
    display_slot_time,
    validate_slot_time,
    validate_booking_status,
    normalize_phone_e164,
)
from services.google_sheets_service import sync_booking_to_sheet

logger = logging.getLogger(__name__)

DEFAULT_ZOOM_URL = "https://zoom.us/j/DEMO-PLACEHOLDER"


def get_zoom_placeholder_url() -> str:
    """Return the configured DEMO_MEETING_URL or the default placeholder."""
    return os.getenv("DEMO_MEETING_URL", DEFAULT_ZOOM_URL).strip() or DEFAULT_ZOOM_URL


def create_or_reschedule_booking(first_arg, second_arg=None) -> dict:
    """
    Validate, schedule, or reschedule a demo booking for a student lead.
    Maintains one current booking per student via UNIQUE(lead_id).

    Returns:
        {"success": True, "booking": <row dict>, "confirmation": <str>, "rescheduled": bool, "sheet_synced": bool}
        {"success": False, "errors": {field: msg}}
        {"success": False, "db_error": True, "message": …}
    """
    if second_arg is not None:
        conn = first_arg
        form_data = second_arg
        own_conn = False
    else:
        conn = None
        form_data = first_arg
        own_conn = True

    errors: dict[str, str] = {}

    # 1. Validate lead_id
    raw_lead_id = form_data.get("lead_id")
    try:
        lead_id = int(str(raw_lead_id).strip())
    except (ValueError, TypeError):
        errors["lead_id"] = "Please select a valid student lead."
        lead_id = 0

    # 2. Validate demo_date (today or future in Asia/Kolkata timezone)
    raw_date = (form_data.get("demo_date") or "").strip()
    demo_date: date | None = None
    if not raw_date:
        errors["demo_date"] = "Please select a demo date."
    else:
        try:
            demo_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            today = datetime.now(timezone.utc).date()
            if demo_date < today:
                errors["demo_date"] = "Demo date must be today or in the future."
        except ValueError:
            errors["demo_date"] = "Invalid date format. Use YYYY-MM-DD."

    # 3. Validate and canonicalize slot_time ('13:00', '15:00', '17:00', '19:00')
    raw_slot = form_data.get("slot_time") or form_data.get("demo_time", "")
    slot_err = validate_slot_time(raw_slot)
    if slot_err:
        errors["slot_time"] = slot_err
    slot_time = canonical_slot_time(raw_slot)

    if errors:
        return {"success": False, "errors": errors}

    connection = conn if conn is not None else get_db_connection()
    now_utc = datetime.now(timezone.utc).isoformat()
    zoom_link = get_zoom_placeholder_url()

    try:
        cursor = connection.cursor()

        # Check lead exists
        cursor.execute("SELECT id, student_name FROM leads WHERE id = ?", (lead_id,))
        lead_row = cursor.fetchone()
        if not lead_row:
            return {
                "success": False,
                "errors": {"lead_id": "The selected student lead record does not exist."},
            }
        student_name = lead_row["student_name"]

        # Check if booking already exists for this lead (Rescheduling behavior)
        cursor.execute("SELECT * FROM bookings WHERE lead_id = ?", (lead_id,))
        existing_booking = cursor.fetchone()

        if existing_booking:
            # Reschedule existing booking
            booking_id = existing_booking["id"]
            cursor.execute(
                """
                UPDATE bookings 
                SET demo_date = ?, slot_time = ?, booking_status = 'Booked',
                    zoom_link = ?, updated_at = ?, sheet_sync_status = 'pending'
                WHERE id = ?
                """,
                (str(demo_date), slot_time, zoom_link, now_utc, booking_id),
            )
            rescheduled = True
        else:
            # Insert new booking
            cursor.execute(
                """
                INSERT INTO bookings (
                    lead_id, demo_date, slot_time, booking_status,
                    zoom_link, created_at, updated_at, sheet_sync_status
                ) VALUES (?, ?, ?, 'Booked', ?, ?, ?, 'pending')
                """,
                (lead_id, str(demo_date), slot_time, zoom_link, now_utc, now_utc),
            )
            booking_id = cursor.lastrowid
            rescheduled = False

        connection.commit()

        # Fetch saved booking record with joined student name
        cursor.execute(
            """
            SELECT b.*, l.student_name, l.email as student_email, l.exam_goal
            FROM bookings b
            JOIN leads l ON b.lead_id = l.id
            WHERE b.id = ?
            """,
            (booking_id,),
        )
        booking = dict(cursor.fetchone())

        # Sync to Google Sheets
        sheet_synced = sync_booking_to_sheet(booking, connection)

        # Build confirmation message
        display_time = display_slot_time(slot_time)
        confirmation = _build_confirmation(student_name, demo_date, display_time, zoom_link, rescheduled)

        return {
            "success": True,
            "booking": booking,
            "confirmation": confirmation,
            "rescheduled": rescheduled,
            "sheet_synced": sheet_synced,
        }

    except Exception as exc:
        logger.error("Booking operation failed: %s", exc)
        return {
            "success": False,
            "db_error": True,
            "message": "A database error occurred while saving the demo booking. Please try again.",
        }
    finally:
        if own_conn and connection:
            connection.close()


def update_booking_status(arg1, arg2, arg3=None) -> dict:
    """
    Update booking status to 'Booked', 'Attended', or 'Not Attended' and sync to Google Sheets.
    Supports update_booking_status(booking_id, new_status, conn=None)
          or update_booking_status(conn, booking_id, new_status).
    """
    if arg3 is not None:
        conn = arg1
        booking_id = arg2
        new_status = arg3
        own_conn = False
    else:
        conn = None
        booking_id = arg1
        new_status = arg2
        own_conn = True

    err = validate_booking_status(new_status)
    if err:
        return {"success": False, "message": err}

    connection = conn if conn is not None else get_db_connection()
    now_utc = datetime.now(timezone.utc).isoformat()

    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE bookings 
            SET booking_status = ?, updated_at = ?, sheet_sync_status = 'pending'
            WHERE id = ?
            """,
            (new_status, now_utc, booking_id),
        )
        connection.commit()

        if cursor.rowcount == 0:
            return {"success": False, "message": "Booking not found."}

        # Fetch updated record and sync to Google Sheets
        cursor.execute(
            """
            SELECT b.*, l.student_name, l.email as student_email, l.exam_goal
            FROM bookings b
            JOIN leads l ON b.lead_id = l.id
            WHERE b.id = ?
            """,
            (booking_id,),
        )
        booking = dict(cursor.fetchone())
        sync_booking_to_sheet(booking, connection)

        logger.info("Booking %s status updated to %s", booking_id, new_status)
        return {"success": True, "booking": booking}

    except Exception as exc:
        logger.error("Failed to update status for booking %s: %s", booking_id, exc)
        return {"success": False, "message": "Database error while updating booking status."}
    finally:
        if own_conn and connection:
            connection.close()


def get_all_bookings(conn=None) -> List[Dict]:
    """Return all bookings joined with lead information ordered by demo_date and slot_time."""
    own_conn = conn is None
    connection = conn if conn is not None else get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT 
                b.id, b.lead_id, b.demo_date, b.slot_time, b.booking_status,
                b.zoom_link, b.created_at, b.updated_at, b.sheet_sync_status,
                COALESCE(l.student_name, '—') AS student_name,
                COALESCE(l.email, '—') AS student_email,
                COALESCE(l.exam_goal, '—') AS exam_goal,
                COALESCE(l.phone, '—') AS student_phone
            FROM bookings b
            LEFT JOIN leads l ON b.lead_id = l.id
            ORDER BY b.demo_date ASC, b.slot_time ASC
            """
        )
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["demo_time"] = display_slot_time(d["slot_time"])
            d["status"] = d["booking_status"]
            result.append(d)
        return result
    except Exception as exc:
        logger.error("Failed to fetch bookings: %s", exc)
        return []
    finally:
        if own_conn and connection:
            connection.close()


def _build_confirmation(student_name: str, demo_date: date, demo_time: str, zoom_url: str, rescheduled: bool) -> str:
    formatted_date = demo_date.strftime("%A, %d %B %Y")
    header = "🔄 Demo Booking Rescheduled!" if rescheduled else "✅ Demo Booking Confirmed!"
    return (
        f"{header}\n\n"
        f"Student Name : {student_name}\n"
        f"Demo Date    : {formatted_date}\n"
        f"Demo Time    : {demo_time} (IST)\n"
        f"Meeting Link : {zoom_url}\n\n"
        f"⚠️  Note: The Zoom link above is a demonstration placeholder.\n"
        f"A real link will be provided prior to the session."
    )


def mask_phone(phone_str: str) -> str:
    """Mask phone number, preserving prefix and last 4 digits (e.g. +91 ******3210)."""
    if not phone_str:
        return ""
    clean = str(phone_str).strip()
    digits = [c for c in clean if c.isdigit()]
    if len(digits) < 4:
        return "****"
    last4 = "".join(digits[-4:])
    has_plus91 = clean.startswith("+91")
    if has_plus91:
        return f"+91 ******{last4}"
    return f"******{last4}"


def mask_email(email_str: str) -> str:
    """Mask email address (e.g. student@example.com -> s*****t@example.com)."""
    if not email_str or "@" not in email_str:
        return ""
    try:
        user, domain = email_str.strip().lower().split("@", 1)
        if len(user) <= 2:
            masked_user = user[0] + "*"
        else:
            masked_user = user[0] + "*" * min(len(user) - 2, 5) + user[-1]
        return f"{masked_user}@{domain}"
    except Exception:
        return "****@****"


def find_booking_or_enquiry(search_type: str, search_value: str, conn=None) -> dict:
    """
    Look up booking or registered enquiry details using ONE criterion:
    - 'id': Booking ID or Enquiry ID
    - 'phone': Registered student mobile number (E.164 normalized)
    - 'email': Registered email address

    Returns:
        {
            "success": True,
            "has_booking": True/False,
            "data": {
                "student_name": str,
                "phone_masked": str,
                "email_masked": str,
                "lead_id": int,
                "booking_id": Optional[int],
                "demo_date": Optional[str],
                "demo_date_formatted": Optional[str],
                "slot_time": Optional[str],
                "slot_time_display": Optional[str],
                "booking_status": str,
                "class_level": Optional[int],
                "exam_goal": Optional[str],
                "interested_course": Optional[str],
                "zoom_link": str,
                "sheet_sync_status": str,
            }
        }
    """
    if not search_type or not search_value:
        return {
            "success": False,
            "error": "Please select a search method and enter your details.",
        }

    stype = str(search_type).strip().lower()
    sval = str(search_value).strip()

    if not sval:
        return {
            "success": False,
            "error": "Please enter a value to search.",
        }

    own_conn = conn is None
    connection = conn if conn is not None else get_db_connection()

    try:
        cursor = connection.cursor()
        lead_row = None
        booking_row = None

        if stype in ("id", "booking_id", "enquiry_id", "ref_id"):
            clean_id_str = sval.lstrip("#").replace("Lead", "").replace("Booking", "").replace("B-", "").replace("L-", "").strip()
            if not clean_id_str.isdigit():
                return {
                    "success": False,
                    "error": "Please enter a valid numeric reference ID (e.g. 1 or #1).",
                }
            ref_id = int(clean_id_str)

            # Try finding booking first by booking id
            cursor.execute(
                """
                SELECT b.*, l.student_name, l.phone, l.phone_e164, l.email,
                       l.class_level, l.exam_goal, l.interested_course
                FROM bookings b
                JOIN leads l ON b.lead_id = l.id
                WHERE b.id = ?
                """,
                (ref_id,),
            )
            b_match = cursor.fetchone()
            if b_match:
                booking_row = dict(b_match)
                lead_row = {
                    "id": booking_row["lead_id"],
                    "student_name": booking_row["student_name"],
                    "phone": booking_row["phone"],
                    "phone_e164": booking_row["phone_e164"],
                    "email": booking_row["email"],
                    "class_level": booking_row["class_level"],
                    "exam_goal": booking_row["exam_goal"],
                    "interested_course": booking_row["interested_course"],
                }
            else:
                # Try finding lead by lead id
                cursor.execute("SELECT * FROM leads WHERE id = ?", (ref_id,))
                l_match = cursor.fetchone()
                if l_match:
                    lead_row = dict(l_match)
                    # Check if this lead has a booking
                    cursor.execute("SELECT * FROM bookings WHERE lead_id = ?", (ref_id,))
                    b_by_lead = cursor.fetchone()
                    if b_by_lead:
                        booking_row = dict(b_by_lead)

        elif stype in ("phone", "mobile", "phone_number"):
            phone_e164 = normalize_phone_e164(sval)
            if not phone_e164:
                # If user entered 10 digits without prefix, try +91
                digits_only = "".join(c for c in sval if c.isdigit())
                if len(digits_only) == 10 and digits_only[0] in "6789":
                    phone_e164 = normalize_phone_e164("+91" + digits_only)

            if not phone_e164:
                return {
                    "success": False,
                    "error": "Please enter a valid 10-digit mobile number.",
                }

            cursor.execute("SELECT * FROM leads WHERE phone_e164 = ? OR phone = ?", (phone_e164, sval))
            matches = cursor.fetchall()
            if len(matches) > 1:
                return {
                    "success": False,
                    "ambiguous": True,
                    "error": "Multiple records found for this phone number. Please search using your Booking / Enquiry ID to identify your booking.",
                }
            elif len(matches) == 1:
                lead_row = dict(matches[0])
                cursor.execute("SELECT * FROM bookings WHERE lead_id = ?", (lead_row["id"],))
                b_match = cursor.fetchone()
                if b_match:
                    booking_row = dict(b_match)

        elif stype in ("email", "email_address"):
            cleaned_email = sval.lower()
            if "@" not in cleaned_email or "." not in cleaned_email:
                return {
                    "success": False,
                    "error": "Please enter a valid email address.",
                }

            cursor.execute("SELECT * FROM leads WHERE lower(email) = ?", (cleaned_email,))
            matches = cursor.fetchall()
            if len(matches) > 1:
                return {
                    "success": False,
                    "ambiguous": True,
                    "error": "Multiple records found for this email address. Please search using your Booking / Enquiry ID to identify your booking.",
                }
            elif len(matches) == 1:
                lead_row = dict(matches[0])
                cursor.execute("SELECT * FROM bookings WHERE lead_id = ?", (lead_row["id"],))
                b_match = cursor.fetchone()
                if b_match:
                    booking_row = dict(b_match)
        else:
            return {
                "success": False,
                "error": f"Unsupported search method '{search_type}'. Please choose Booking ID, Phone, or Email.",
            }

        if not lead_row:
            return {
                "success": False,
                "not_found": True,
                "message": "We couldn't find a matching record. Please check your details and try again.",
            }

        # Format retrieved payload
        has_booking = booking_row is not None
        zoom_link = (booking_row.get("zoom_link") if has_booking else "") or get_zoom_placeholder_url()

        demo_date_str = booking_row.get("demo_date") if has_booking else None
        demo_date_formatted = None
        if demo_date_str:
            try:
                d_obj = datetime.strptime(demo_date_str, "%Y-%m-%d").date()
                demo_date_formatted = d_obj.strftime("%A, %d %B %Y")
            except Exception:
                demo_date_formatted = demo_date_str

        slot_time_raw = booking_row.get("slot_time") if has_booking else None
        slot_time_display = display_slot_time(slot_time_raw) if slot_time_raw else None
        booking_status = booking_row.get("booking_status", "Booked") if has_booking else "Registered — Demo Not Yet Booked"
        sheet_sync = booking_row.get("sheet_sync_status") if has_booking else lead_row.get("sheet_sync_status", "pending")

        return {
            "success": True,
            "has_booking": has_booking,
            "data": {
                "student_name": lead_row["student_name"],
                "phone_masked": mask_phone(lead_row.get("phone", "")),
                "email_masked": mask_email(lead_row.get("email", "")),
                "lead_id": lead_row["id"],
                "booking_id": booking_row["id"] if has_booking else None,
                "demo_date": demo_date_str,
                "demo_date_formatted": demo_date_formatted,
                "slot_time": slot_time_raw,
                "slot_time_display": slot_time_display,
                "booking_status": booking_status,
                "class_level": lead_row.get("class_level"),
                "exam_goal": lead_row.get("exam_goal"),
                "interested_course": lead_row.get("interested_course"),
                "zoom_link": zoom_link,
                "sheet_sync_status": sheet_sync,
            },
        }

    except Exception as exc:
        logger.error("Error finding booking or enquiry: %s", exc)
        return {
            "success": False,
            "error": "A server error occurred while retrieving your booking details. Please try again later.",
        }
    finally:
        if own_conn and connection:
            connection.close()
