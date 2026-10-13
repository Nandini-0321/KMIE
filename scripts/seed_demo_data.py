"""
scripts/seed_demo_data.py
Explicitly seeds sample assessment records from sample_data/enquiries.csv into SQLite.
Usage:
    python -m scripts.seed_demo_data
    or
    python scripts/seed_demo_data.py
"""
import csv
import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db import get_db_connection, init_db
from services.validators import normalize_phone_e164

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("seed_demo_data")


def seed_data():
    init_db(seed_samples=False)  # Ensure schema exists without auto-seeding
    conn = get_db_connection()
    csv_path = PROJECT_ROOT / "sample_data" / "enquiries.csv"

    if not csv_path.exists():
        logger.error("Sample CSV file not found at %s", csv_path)
        return

    now_utc = datetime.now(timezone.utc).isoformat()
    logger.info("Reading sample data from %s...", csv_path)

    inserted_leads = 0
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_phone = row["phone"].strip()
            e164 = normalize_phone_e164(raw_phone)
            if not e164:
                logger.warning("Skipping invalid phone %s for %s", raw_phone, row["student_name"])
                continue

            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO leads (
                        student_name, phone, phone_e164, email,
                        class_level, exam_goal, interested_course,
                        created_at, updated_at, sheet_sync_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                    ON CONFLICT(phone_e164) DO NOTHING
                    """,
                    (
                        row["student_name"].strip(),
                        raw_phone,
                        e164,
                        row["email"].strip().lower(),
                        int(row["class_level"]),
                        row["exam_goal"].strip(),
                        row["interested_course"].strip(),
                        now_utc,
                        now_utc,
                    ),
                )
                if cursor.rowcount > 0:
                    inserted_leads += 1
            except Exception as exc:
                logger.error("Failed to insert lead %s: %s", row["student_name"], exc)

    conn.commit()
    logger.info("Inserted %d new sample leads.", inserted_leads)

    # Seed 2 sample demo bookings for the first 2 leads if not already booked
    leads = conn.execute("SELECT id, student_name FROM leads ORDER BY id ASC LIMIT 2").fetchall()
    inserted_bookings = 0

    if len(leads) >= 1:
        lead_id = leads[0]["id"]
        demo_date = (datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%d")
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO bookings (
                    lead_id, demo_date, slot_time, booking_status,
                    zoom_link, created_at, updated_at, sheet_sync_status
                ) VALUES (?, ?, '15:00', 'Booked', 'https://zoom.us/j/DEMO-PLACEHOLDER', ?, ?, 'pending')
                ON CONFLICT(lead_id) DO NOTHING
                """,
                (lead_id, demo_date, now_utc, now_utc),
            )
            if cursor.rowcount > 0:
                inserted_bookings += 1
        except Exception as exc:
            logger.error("Failed to insert sample booking for lead %d: %s", lead_id, exc)

    if len(leads) >= 2:
        lead_id = leads[1]["id"]
        demo_date = (datetime.now(timezone.utc) + timedelta(days=5)).strftime("%Y-%m-%d")
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO bookings (
                    lead_id, demo_date, slot_time, booking_status,
                    zoom_link, created_at, updated_at, sheet_sync_status
                ) VALUES (?, ?, '17:00', 'Attended', 'https://zoom.us/j/DEMO-PLACEHOLDER', ?, ?, 'pending')
                ON CONFLICT(lead_id) DO NOTHING
                """,
                (lead_id, demo_date, now_utc, now_utc),
            )
            if cursor.rowcount > 0:
                inserted_bookings += 1
        except Exception as exc:
            logger.error("Failed to insert sample booking for lead %d: %s", lead_id, exc)

    conn.commit()
    conn.close()
    logger.info("Inserted %d sample bookings.", inserted_bookings)
    logger.info("Sample data seeding complete.")


if __name__ == "__main__":
    seed_data()
