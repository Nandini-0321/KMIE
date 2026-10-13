-- =============================================================================
-- schema.sql — KMIE Student Enquiry & Demo Booking System (SQLite)
-- Primary Database: database/kmie.db
-- =============================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Table A: leads
-- ---------------------------------------------------------------------------
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

-- ---------------------------------------------------------------------------
-- Table B: bookings
-- ---------------------------------------------------------------------------
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

-- ---------------------------------------------------------------------------
-- Table C: sync_jobs (Tracks asynchronous or retried Google Sheets updates)
-- ---------------------------------------------------------------------------
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
