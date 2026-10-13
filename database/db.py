"""
database/db.py — SQLite Database Manager for KMIE System.
Handles connection management, schema initialization, foreign keys, and seed data.
"""
import os
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "database" / "kmie.db"


def get_db_path() -> Path:
    """Return the absolute path to the SQLite database file."""
    env_path = os.getenv("DATABASE_PATH", "").strip()
    if env_path:
        path = Path(env_path)
        if not path.is_absolute():
            path = BASE_DIR / path
    else:
        path = DEFAULT_DB_PATH

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_db_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """
    Open and return a connection to the SQLite database.
    Configures row factory to sqlite3.Row for dict-like access,
    and enables foreign key constraint enforcement.
    """
    path = db_path if db_path is not None else get_db_path()
    conn = sqlite3.connect(str(path), timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS leads (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name        TEXT NOT NULL CHECK (length(student_name) >= 2),
    phone               TEXT NOT NULL,
    phone_e164          TEXT NOT NULL UNIQUE,
    email               TEXT NOT NULL CHECK (email LIKE '%@%'),
    class_level         INTEGER NOT NULL CHECK (class_level IN (11, 12)),
    exam_goal           TEXT NOT NULL CHECK (exam_goal IN ('NEET', 'JEE')),
    interested_course   TEXT NOT NULL,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    sheet_sync_status   TEXT NOT NULL DEFAULT 'pending' CHECK (sheet_sync_status IN ('pending', 'synced', 'failed')),
    sheet_synced_at     TEXT,
    sheet_sync_error    TEXT
);

CREATE INDEX IF NOT EXISTS idx_leads_phone_e164     ON leads (phone_e164);
CREATE INDEX IF NOT EXISTS idx_leads_created_at     ON leads (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_sync_status    ON leads (sheet_sync_status);

CREATE TABLE IF NOT EXISTS bookings (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id             INTEGER NOT NULL UNIQUE REFERENCES leads(id) ON DELETE CASCADE,
    demo_date           TEXT NOT NULL,
    slot_time           TEXT NOT NULL CHECK (slot_time IN ('13:00', '15:00', '17:00', '19:00')),
    booking_status      TEXT NOT NULL DEFAULT 'Booked' CHECK (booking_status IN ('Booked', 'Attended', 'Not Attended')),
    zoom_link           TEXT NOT NULL,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    sheet_sync_status   TEXT NOT NULL DEFAULT 'pending' CHECK (sheet_sync_status IN ('pending', 'synced', 'failed')),
    sheet_synced_at     TEXT,
    sheet_sync_error    TEXT
);

CREATE INDEX IF NOT EXISTS idx_bookings_lead_id     ON bookings (lead_id);
CREATE INDEX IF NOT EXISTS idx_bookings_demo_date   ON bookings (demo_date);
CREATE INDEX IF NOT EXISTS idx_bookings_status      ON bookings (booking_status);
CREATE INDEX IF NOT EXISTS idx_bookings_sync_status ON bookings (sheet_sync_status);

CREATE TABLE IF NOT EXISTS sync_jobs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type         TEXT NOT NULL CHECK (entity_type IN ('lead', 'booking')),
    entity_id           INTEGER NOT NULL,
    action              TEXT NOT NULL CHECK (action IN ('insert', 'update')),
    status              TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'synced', 'failed')),
    attempts            INTEGER NOT NULL DEFAULT 0,
    last_error          TEXT,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sync_jobs_status     ON sync_jobs (status);
"""


SAMPLE_LEADS = [
    (
        "Aarav Sharma",
        "9876543210",
        "+919876543210",
        "aarav.sharma@example.com",
        11,
        "NEET",
        "NEET Long-Term Preparation",
    ),
    (
        "Priya Patel",
        "+91 98765 43211",
        "+919876543211",
        "priya.patel@example.com",
        12,
        "JEE",
        "JEE Advanced Preparation",
    ),
    (
        "Rohan Mehta",
        "09876543212",
        "+919876543212",
        "rohan.mehta@example.com",
        11,
        "JEE",
        "JEE Main Preparation",
    ),
    (
        "Sneha Reddy",
        "98765-43213",
        "+919876543213",
        "sneha.reddy@example.com",
        12,
        "NEET",
        "NEET Crash Course",
    ),
    (
        "Karthik Nair",
        "+91-98765-43214",
        "+919876543214",
        "karthik.nair@example.com",
        11,
        "NEET",
        "Foundation Course",
    ),
]


def init_db(db_path: Path | str | None = None, seed_samples: bool = False):
    """
    Initialize SQLite schema and optional sample data.
    Safe to call repeatedly (idempotent).
    """
    conn = get_db_connection(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()

        if seed_samples:
            count = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
            if count == 0:
                now_utc = datetime.now(timezone.utc).isoformat()
                for lead in SAMPLE_LEADS:
                    conn.execute(
                        """
                        INSERT INTO leads (
                            student_name, phone, phone_e164, email,
                            class_level, exam_goal, interested_course,
                            created_at, updated_at, sheet_sync_status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                        ON CONFLICT(phone_e164) DO NOTHING
                        """,
                        (*lead, now_utc, now_utc),
                    )

                # Seed sample bookings for lead 1 and lead 2
                leads = conn.execute("SELECT id FROM leads ORDER BY id ASC LIMIT 2").fetchall()
                if len(leads) >= 1:
                    d1 = (datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%d")
                    conn.execute(
                        """
                        INSERT INTO bookings (
                            lead_id, demo_date, slot_time, booking_status,
                            zoom_link, created_at, updated_at, sheet_sync_status
                        ) VALUES (?, ?, '15:00', 'Booked', 'https://zoom.us/j/DEMO-PLACEHOLDER', ?, ?, 'pending')
                        ON CONFLICT(lead_id) DO NOTHING
                        """,
                        (leads[0]["id"], d1, now_utc, now_utc),
                    )

                if len(leads) >= 2:
                    d2 = (datetime.now(timezone.utc) + timedelta(days=5)).strftime("%Y-%m-%d")
                    conn.execute(
                        """
                        INSERT INTO bookings (
                            lead_id, demo_date, slot_time, booking_status,
                            zoom_link, created_at, updated_at, sheet_sync_status
                        ) VALUES (?, ?, '17:00', 'Attended', 'https://zoom.us/j/DEMO-PLACEHOLDER', ?, ?, 'pending')
                        ON CONFLICT(lead_id) DO NOTHING
                        """,
                        (leads[1]["id"], d2, now_utc, now_utc),
                    )

                conn.commit()
    finally:
        conn.close()
