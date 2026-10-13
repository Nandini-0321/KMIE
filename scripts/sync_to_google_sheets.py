"""
scripts/sync_to_google_sheets.py
Command-line utility to synchronize SQLite enquiries and demo bookings to Google Sheets.
Usage:
    python -m scripts.sync_to_google_sheets
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Set UTF-8 output encoding for Windows command prompt
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables from .env
load_dotenv(PROJECT_ROOT / ".env")

from database.db import get_db_connection
from services.google_sheets_service import is_configured, retry_all_pending_syncs


def main():
    print("=" * 70)
    print("  KMIE Google Sheets Synchronization Utility")
    print("=" * 70)

    conn = get_db_connection()
    leads = conn.execute("SELECT * FROM leads ORDER BY id ASC").fetchall()
    bookings = conn.execute("SELECT * FROM bookings ORDER BY id ASC").fetchall()

    print(f"\n[*] Total records in local SQLite database (database/kmie.db):")
    print(f"    - Enquiries: {len(leads)}")
    print(f"    - Bookings:  {len(bookings)}\n")

    print("-" * 70)
    print("  SAMPLE ENQUIRIES READY FOR GOOGLE SHEETS (with Submission Timestamp):")
    print("-" * 70)
    print(f"{'ID':<4} | {'Student Name':<16} | {'Phone (E.164)':<14} | {'Goal':<5} | {'Submission Timestamp (UTC)'}")
    print("-" * 70)
    for lead in leads[:5]:
        print(f"#{lead['id']:<3} | {lead['student_name']:<16} | {lead['phone_e164']:<14} | {lead['exam_goal']:<5} | {lead['created_at']}")
    print("-" * 70)

    configured = is_configured()
    if not configured:
        print("\n[!] Google Sheets is currently UNCONFIGURED in your environment.")
        print("To connect a live Google Sheet, add these two variables to your `.env` file:")
        print("   1. GOOGLE_SHEET_ID=<your-spreadsheet-id-from-url>")
        print("   2. GOOGLE_SERVICE_ACCOUNT_JSON_BASE64=<base64-encoded-service-account-json>")
        print("      (Or GOOGLE_SERVICE_ACCOUNT_FILE=path/to/credentials.json)")
        print("\nThen re-run this script or click 'Retry Sheets Sync' in the Admin Console.")
        print("SQLite will remain the reliable primary system of record.\n")
        return

    print("\n[OK] Google Sheets credentials detected. Initiating synchronization...")
    synced, failed = retry_all_pending_syncs()
    print(f"    - Successfully synchronized: {synced}")
    print(f"    - Failed syncs:             {failed}")
    print("\nSynchronization routine complete.")


if __name__ == "__main__":
    main()
