"""
services/sheets_service.py — Google Sheets API Integration.
Uses gspread and google-auth with service-account credentials.
Syncs student enquiries and demo bookings to Google Sheets with graceful offline fallback.
"""
import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Scopes for Google Drive & Sheets API
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_sheets_client():
    """
    Return an authenticated gspread client if credentials exist in environment,
    or None if credentials are not configured.
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        # Check for service account json file path
        creds_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
        # Check for inline json string
        creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")

        creds = None
        if creds_file and os.path.exists(creds_file):
            creds = Credentials.from_service_account_file(creds_file, scopes=SCOPES)
        elif creds_json:
            creds_data = json.loads(creds_json)
            creds = Credentials.from_service_account_info(creds_data, scopes=SCOPES)

        if creds:
            return gspread.authorize(creds)
        return None
    except Exception as exc:
        logger.warning("Google Sheets client initialization skipped: %s", exc)
        return None


def append_enquiry_to_sheet(enquiry: dict) -> bool:
    """
    Append a student enquiry row to the configured Google Sheet.
    Returns True if appended, False if unconfigured or failed.
    """
    sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
    if not sheet_id:
        # Not configured — graceful no-op
        return False

    client = get_sheets_client()
    if not client:
        return False

    try:
        sh = client.open_by_key(sheet_id)
        worksheet = sh.sheet1
        row = [
            enquiry.get("id", ""),
            enquiry.get("student_name", ""),
            enquiry.get("phone", ""),
            enquiry.get("normalized_phone", ""),
            enquiry.get("email", ""),
            enquiry.get("student_class", ""),
            enquiry.get("exam_goal", ""),
            enquiry.get("course", ""),
            enquiry.get("created_at", ""),
        ]
        worksheet.append_row(row)
        logger.info("Enquiry synced to Google Sheet %s", sheet_id[:8])
        return True
    except Exception as exc:
        logger.error("Failed to append enquiry to Google Sheet: %s", exc)
        return False


def append_booking_to_sheet(booking: dict) -> bool:
    """
    Append a demo booking row to the configured Google Sheet.
    Returns True if appended, False if unconfigured or failed.
    """
    sheet_id = os.getenv("GOOGLE_SHEET_ID", "").strip()
    if not sheet_id:
        return False

    client = get_sheets_client()
    if not client:
        return False

    try:
        sh = client.open_by_key(sheet_id)
        try:
            worksheet = sh.worksheet("Demo Bookings")
        except Exception:
            worksheet = sh.sheet1
        row = [
            booking.get("id", ""),
            booking.get("lead_id", ""),
            booking.get("student_name", ""),
            booking.get("demo_date", ""),
            booking.get("demo_time", ""),
            booking.get("status", ""),
            booking.get("created_at", ""),
        ]
        worksheet.append_row(row)
        logger.info("Booking synced to Google Sheet %s", sheet_id[:8])
        return True
    except Exception as exc:
        logger.error("Failed to append booking to Google Sheet: %s", exc)
        return False
