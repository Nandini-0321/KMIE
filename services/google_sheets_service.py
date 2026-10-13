"""
services/google_sheets_service.py — Google Sheets API Integration.
Uses gspread and google-auth with base64-encoded or file service account credentials.
Maintains two tabs: 'Enquiries' and 'Demo Bookings'.
Updates existing rows on reschedule/status change and prevents duplicate rows during retries.
"""
import base64
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from database.db import get_db_connection
from services.validators import display_slot_time

PROJECT_ROOT = Path(__file__).resolve().parent.parent

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

TAB_ENQUIRIES = "Enquiries"
TAB_BOOKINGS = "Demo Bookings"

HEADERS_ENQUIRIES = [
    "Lead ID",
    "Submission Timestamp",
    "Student Name",
    "Normalized Phone Number",
    "Email",
    "Class",
    "Exam Goal",
    "Interested Course",
    "Last Updated",
]

HEADERS_BOOKINGS = [
    "Booking ID",
    "Lead ID",
    "Student Name",
    "Demo Date",
    "Demo Time",
    "Booking Status",
    "Last Updated",
]


def _get_sheet_id() -> str:
    """Extract clean Google Sheet ID even if full URL was provided."""
    raw = os.getenv("GOOGLE_SHEET_ID", "").strip()
    if "/d/" in raw:
        raw = raw.split("/d/")[1].split("/")[0].split("?")[0].split("#")[0]
    return raw


def is_configured() -> bool:
    """Check if required Google Sheets environment variables are present."""
    sheet_id = _get_sheet_id()
    file_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "").strip()
    has_file = False
    if file_path:
        p = Path(file_path)
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        has_file = p.exists()
    has_creds = bool(
        os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_BASE64", "").strip()
        or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
        or has_file
    )
    return bool(sheet_id and has_creds)


def get_sheets_client():
    """Decode service account credentials and return an authorized gspread client."""
    if not is_configured():
        return None

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        b64_creds = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_BASE64", "").strip()
        raw_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
        file_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "").strip()

        creds_data = None
        if b64_creds:
            decoded = base64.b64decode(b64_creds).decode("utf-8")
            creds_data = json.loads(decoded)
        elif raw_json:
            creds_data = json.loads(raw_json)
        elif file_path:
            p = Path(file_path)
            if not p.is_absolute():
                p = PROJECT_ROOT / p
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    creds_data = json.load(f)

        if creds_data:
            creds = Credentials.from_service_account_info(creds_data, scopes=SCOPES)
            return gspread.authorize(creds)
        return None
    except Exception as exc:
        logger.error("Failed to authenticate Google Sheets client: %s", exc)
        return None


def get_or_create_worksheet(spreadsheet, title: str, headers: list):
    """Retrieve an existing tab or create it with headers if missing."""
    try:
        ws = spreadsheet.worksheet(title)
    except Exception:
        ws = spreadsheet.add_worksheet(title=title, rows=100, cols=len(headers) + 2)

    # Check if header row exists
    existing_headers = ws.row_values(1)
    if not existing_headers:
        ws.append_row(headers)
    return ws


def sync_lead_to_sheet(lead: dict, conn=None) -> bool:
    """
    Sync a student enquiry to the 'Enquiries' tab in Google Sheets.
    Updates existing row if Lead ID matches; otherwise appends a new row.
    Updates SQLite sheet_sync_status accordingly.
    """
    lead_id = lead["id"]
    now_utc = datetime.now(timezone.utc).isoformat()
    own_conn = conn is None
    connection = conn if conn is not None else get_db_connection()

    if not is_configured():
        _update_lead_sync_status(connection, lead_id, "pending", None, "Google Sheets unconfigured")
        if own_conn:
            connection.close()
        return False

    client = get_sheets_client()
    if not client:
        _update_lead_sync_status(connection, lead_id, "failed", None, "Authentication failed")
        if own_conn:
            connection.close()
        return False

    try:
        sheet_id = _get_sheet_id()
        sh = client.open_by_key(sheet_id)
        ws = get_or_create_worksheet(sh, TAB_ENQUIRIES, HEADERS_ENQUIRIES)

        # Search for existing Lead ID in column 1
        cell = ws.find(str(lead_id), in_column=1)

        row_data = [
            str(lead["id"]),
            str(lead.get("created_at", now_utc)),
            str(lead.get("student_name", "")),
            str(lead.get("phone_e164") or lead.get("phone", "")),
            str(lead.get("email", "")),
            str(lead.get("class_level") or lead.get("student_class", "")),
            str(lead.get("exam_goal", "")),
            str(lead.get("interested_course") or lead.get("course", "")),
            now_utc,
        ]

        if cell:
            # Update existing row
            ws.update(values=[row_data], range_name=f"A{cell.row}:I{cell.row}")
            logger.info("Updated Google Sheet Enquiry row %d for Lead %d", cell.row, lead_id)
        else:
            # Append new row
            ws.append_row(row_data)
            logger.info("Appended new Google Sheet Enquiry row for Lead %d", lead_id)

        _update_lead_sync_status(connection, lead_id, "synced", now_utc, None)
        if own_conn:
            connection.close()
        return True

    except Exception as exc:
        err_msg = str(exc)[:200]
        logger.error("Failed to sync Lead %d to Google Sheet: %s", lead_id, err_msg)
        _update_lead_sync_status(connection, lead_id, "failed", None, err_msg)
        if own_conn:
            connection.close()
        return False


def sync_booking_to_sheet(booking: dict, conn=None) -> bool:
    """
    Sync a demo booking to the 'Demo Bookings' tab in Google Sheets.
    Updates existing row if Booking ID or Lead ID matches; otherwise appends.
    """
    booking_id = booking["id"]
    lead_id = booking.get("lead_id")
    now_utc = datetime.now(timezone.utc).isoformat()
    own_conn = conn is None
    connection = conn if conn is not None else get_db_connection()

    if not is_configured():
        _update_booking_sync_status(connection, booking_id, "pending", None, "Google Sheets unconfigured")
        if own_conn:
            connection.close()
        return False

    client = get_sheets_client()
    if not client:
        _update_booking_sync_status(connection, booking_id, "failed", None, "Authentication failed")
        if own_conn:
            connection.close()
        return False

    try:
        sheet_id = _get_sheet_id()
        sh = client.open_by_key(sheet_id)
        ws = get_or_create_worksheet(sh, TAB_BOOKINGS, HEADERS_BOOKINGS)

        # Look up student name from SQLite if missing
        student_name = booking.get("student_name")
        if not student_name and lead_id:
            row = connection.execute("SELECT student_name FROM leads WHERE id = ?", (lead_id,)).fetchone()
            student_name = row["student_name"] if row else "—"

        display_time = display_slot_time(booking.get("slot_time") or booking.get("demo_time", ""))

        row_data = [
            str(booking["id"]),
            str(lead_id),
            str(student_name or "—"),
            str(booking.get("demo_date", "")),
            str(display_time),
            str(booking.get("booking_status") or booking.get("status", "Booked")),
            now_utc,
        ]

        # Search for existing booking by Booking ID (col 1) or Lead ID (col 2)
        cell = ws.find(str(booking_id), in_column=1)
        if not cell and lead_id:
            cell = ws.find(str(lead_id), in_column=2)

        if cell:
            ws.update(values=[row_data], range_name=f"A{cell.row}:G{cell.row}")
            logger.info("Updated Google Sheet Booking row %d for Booking %d", cell.row, booking_id)
        else:
            ws.append_row(row_data)
            logger.info("Appended new Google Sheet Booking row for Booking %d", booking_id)

        _update_booking_sync_status(connection, booking_id, "synced", now_utc, None)
        if own_conn:
            connection.close()
        return True

    except Exception as exc:
        err_msg = str(exc)[:200]
        logger.error("Failed to sync Booking %d to Google Sheet: %s", booking_id, err_msg)
        _update_booking_sync_status(connection, booking_id, "failed", None, err_msg)
        if own_conn:
            connection.close()
        return False


def retry_all_pending_syncs() -> Tuple[int, int]:
    """
    Admin utility: scan SQLite for all unsynced leads and bookings and retry synchronization.
    Returns (synced_count, failed_count).
    """
    conn = get_db_connection()
    synced = 0
    failed = 0

    try:
        # Retry unsynced leads
        unsynced_leads = conn.execute(
            "SELECT * FROM leads WHERE sheet_sync_status != 'synced'"
        ).fetchall()
        for l in unsynced_leads:
            if sync_lead_to_sheet(dict(l), conn):
                synced += 1
            else:
                failed += 1

        # Retry unsynced bookings
        unsynced_bookings = conn.execute(
            """
            SELECT b.*, l.student_name 
            FROM bookings b 
            LEFT JOIN leads l ON b.lead_id = l.id 
            WHERE b.sheet_sync_status != 'synced'
            """
        ).fetchall()
        for b in unsynced_bookings:
            if sync_booking_to_sheet(dict(b), conn):
                synced += 1
            else:
                failed += 1

    finally:
        conn.close()

    return synced, failed


def _update_lead_sync_status(conn, lead_id: int, status: str, synced_at: Optional[str], error: Optional[str]):
    try:
        conn.execute(
            """
            UPDATE leads 
            SET sheet_sync_status = ?, sheet_synced_at = ?, sheet_sync_error = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, synced_at, error, datetime.now(timezone.utc).isoformat(), lead_id),
        )
        conn.commit()
    except Exception as exc:
        logger.error("Could not update lead %d sync status: %s", lead_id, exc)


def _update_booking_sync_status(conn, booking_id: int, status: str, synced_at: Optional[str], error: Optional[str]):
    try:
        conn.execute(
            """
            UPDATE bookings 
            SET sheet_sync_status = ?, sheet_synced_at = ?, sheet_sync_error = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, synced_at, error, datetime.now(timezone.utc).isoformat(), booking_id),
        )
        conn.commit()
    except Exception as exc:
        logger.error("Could not update booking %d sync status: %s", booking_id, exc)
