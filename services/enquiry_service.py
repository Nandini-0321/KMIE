"""
services/enquiry_service.py — Business logic for student enquiries.
Uses local SQLite database (leads table) with E.164 phone normalization,
duplicate prevention, and Google Sheets synchronization hooks.
"""
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Optional, List, Dict

from database.db import get_db_connection
from services.validators import normalize_phone_e164, validate_enquiry_form
from services.google_sheets_service import sync_lead_to_sheet

logger = logging.getLogger(__name__)


def submit_enquiry(first_arg, second_arg=None) -> dict:
    """
    Validate, normalise to E.164, duplicate-check, and insert a new student enquiry.
    Supports submit_enquiry(form_data) and submit_enquiry(conn, form_data).

    Returns:
        {"success": True, "lead": <row dict>, "sheet_synced": bool}
        {"success": False, "errors": {field: msg}}
        {"success": False, "duplicate": True, "message": …}
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

    # 1. Validate fields
    errors = validate_enquiry_form(form_data)
    if errors:
        return {"success": False, "errors": errors}

    # 2. Normalise phone to canonical E.164
    raw_phone = form_data["phone"].strip()
    phone_e164 = normalize_phone_e164(raw_phone)
    if not phone_e164:
        return {
            "success": False,
            "errors": {"phone": "Please enter a valid mobile number (e.g. 10-digit Indian mobile starting with 6–9)."},
        }

    connection = conn if conn is not None else get_db_connection()
    now_utc = datetime.now(timezone.utc).isoformat()

    try:
        cursor = connection.cursor()

        # 3. Application-level duplicate check on phone_e164
        cursor.execute(
            "SELECT * FROM leads WHERE phone_e164 = ?",
            (phone_e164,),
        )
        existing = cursor.fetchone()
        if existing:
            return {
                "success": False,
                "duplicate": True,
                "lead": dict(existing),
                "message": (
                    f"This phone number is already registered under the name "
                    f"'{existing['student_name']}' (Lead ID: {existing['id']}). "
                    f"Please use the existing enquiry for demo booking."
                ),
            }

        # 4. Insert lead into SQLite
        class_val = form_data.get("class_level") or form_data.get("student_class")
        if isinstance(class_val, str) and class_val.startswith("Class "):
            class_val = class_val.replace("Class ", "").strip()
        class_int = int(str(class_val).strip())

        course_val = form_data.get("interested_course") or form_data.get("course")

        cursor.execute(
            """
            INSERT INTO leads (
                student_name, phone, phone_e164, email,
                class_level, exam_goal, interested_course,
                created_at, updated_at, sheet_sync_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
            (
                form_data["student_name"].strip(),
                raw_phone,
                phone_e164,
                form_data["email"].strip().lower(),
                class_int,
                form_data["exam_goal"].strip(),
                course_val.strip(),
                now_utc,
                now_utc,
            ),
        )
        connection.commit()
        lead_id = cursor.lastrowid

        # Fetch the created lead
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        lead = dict(cursor.fetchone())
        logger.info("New enquiry saved in SQLite: %s (Lead ID: %d)", lead["student_name"], lead["id"])

        # 5. Sync to Google Sheets
        sheet_synced = sync_lead_to_sheet(lead, connection)

        return {"success": True, "lead": lead, "sheet_synced": sheet_synced}

    except sqlite3.IntegrityError as exc:
        err_str = str(exc).lower()
        logger.warning("Integrity error on lead insert: %s", exc)
        if "unique" in err_str or "phone_e164" in err_str:
            return {
                "success": False,
                "duplicate": True,
                "message": "This phone number is already registered (database constraint). Please use the existing enquiry.",
            }
        return {
            "success": False,
            "db_error": True,
            "message": "Database constraint violation while saving enquiry.",
        }
    except Exception as exc:
        logger.error("Enquiry submission failed: %s", exc)
        return {
            "success": False,
            "db_error": True,
            "message": "A database error occurred while saving your enquiry. Please try again.",
        }
    finally:
        if own_conn and connection:
            connection.close()


def get_all_enquiries(conn=None, search: Optional[str] = None, class_filter: Optional[str] = None, goal_filter: Optional[str] = None) -> List[Dict]:
    """Return filtered enquiries ordered by created_at DESC."""
    own_conn = conn is None
    connection = conn if conn is not None else get_db_connection()
    try:
        query = "SELECT * FROM leads WHERE 1=1"
        params = []

        if search:
            query += " AND (student_name LIKE ? OR phone LIKE ? OR phone_e164 LIKE ? OR email LIKE ?)"
            s = f"%{search.strip()}%"
            params.extend([s, s, s, s])

        if class_filter:
            try:
                c = int(str(class_filter).replace("Class ", "").strip())
                query += " AND class_level = ?"
                params.append(c)
            except ValueError:
                pass

        if goal_filter and goal_filter in {"NEET", "JEE"}:
            query += " AND exam_goal = ?"
            params.append(goal_filter.strip())

        query += " ORDER BY id DESC"
        cursor = connection.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.error("Failed to query leads: %s", exc)
        return []
    finally:
        if own_conn and connection:
            connection.close()


def get_enquiry_by_id(lead_id: int, conn=None) -> Optional[dict]:
    """Retrieve single lead by ID."""
    own_conn = conn is None
    connection = conn if conn is not None else get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except Exception as exc:
        logger.error("Failed to fetch lead %s: %s", lead_id, exc)
        return None
    finally:
        if own_conn and connection:
            connection.close()
