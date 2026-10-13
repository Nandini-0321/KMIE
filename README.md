# KMIE Student Enquiry & Demo Booking Automation System

[![Deploy Status: Live on Render](https://img.shields.io/badge/Render-Live%20Deployment-brightgreen)](https://kmie-student-enquiry.onrender.com)
[![GitHub Repository](https://img.shields.io/badge/GitHub-Nandini--0321%2FKMIE-blue?logo=github)](https://github.com/Nandini-0321/KMIE)
[![Test Suite: 114 Passed](https://img.shields.io/badge/pytest-114%20passed-success)](https://github.com/Nandini-0321/KMIE)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Database: SQLite](https://img.shields.io/badge/database-SQLite%203-lightgrey)](https://www.sqlite.org/)
[![Sync: Google Sheets](https://img.shields.io/badge/sync-Google%20Sheets%20API-green)](https://developers.google.com/sheets/api)
[![UI: Fully Responsive](https://img.shields.io/badge/responsive-320px%20to%201920px%2B-teal)](https://kmie-student-enquiry.onrender.com)

**Organization:** Komali Mam Institute of Excellence (KMIE)  
**Project:** Assessment Practical Task — Student Enquiry & Demo Booking Automation System  
**Role:** Software Developer & Automation Intern  
**Candidate:** Nandini R  
**Live Application URL:** [https://kmie-student-enquiry.onrender.com](https://kmie-student-enquiry.onrender.com)  
**GitHub Repository:** [https://github.com/Nandini-0321/KMIE](https://github.com/Nandini-0321/KMIE)  

---

## 1. Project Overview

Komali Mam Institute of Excellence (KMIE) manages prospective student admissions across multiple channels. This production-ready web application automates the lead lifecycle from initial enquiry capture and Indian phone normalization to demo slot booking, attendance tracking, and two-way Google Sheets synchronization.

### Key Capabilities
- **Two-Tier Input Validation**: Client-side feedback paired with strict server-side validation (RFC-compliant email, Indian phone regex, allowed classes, exam goals, and courses).
- **Canonical Phone Normalization (E.164)**: Powered by Google's `phonenumbers` engine (`libphonenumber`). Handles `+91`, `0091`, leading `0`, spaces, and hyphens to enforce unique lead records in SQLite.
- **Demo Booking Automation**: Schedules demo slots (`1:00 PM`, `3:00 PM`, `5:00 PM`, `7:00 PM` IST) for today or future dates. Enforces a strict one-booking-per-student rule and supports seamless rescheduling.
- **Local SQLite Primary Storage**: All records persist in `database/kmie.db` with ACID guarantees, foreign keys, and ISO-8601 UTC timestamps.
- **Live Google Sheets Synchronization**: Integrates with Google Sheets (`Enquiries` and `Demo Bookings` tabs) via service accounts. Features deduplication and non-blocking background retry.
- **Dual-Portal Modern UI**: Dedicated, mobile-first responsive interfaces for students (`/`) and administrators (`/admin/dashboard`) with zero page-level horizontal overflow from 320px to 1920px+.

---

## 2. Quick Start for Evaluator (Run in 3 Steps)

### Step 1: Open Terminal in Project Directory
```powershell
cd c:\Users\Nandini\Documents\Projects\KMIE_Project\KMIE_Student_Enquiry
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
python app.py
```
Open **`http://127.0.0.1:5000`** in your browser.

> [!NOTE]
> The application runs locally out-of-the-box using the bundled SQLite database (`database/kmie.db`). Google Cloud credentials are pre-configured for live sync, but if offline, the app operates gracefully with local SQLite persistence.

---

## 3. Application Portals & URL Directory

| Route / URL | Portal / Feature | Access | Description |
|---|---|---|---|
| **`/`** | **Student Portal** | Public | Single-column page for student enquiry submission and demo slot booking. |
| **`/admin/login`** | **Admin Login** | Public | Protected login card with password visibility toggle. |
| **`/admin/dashboard`** | **Admin Console** | Admin Session | Dashboard with metrics, lead filters, attendance updater, and Google Sheets sync retry. |
| **`/admin/logout`** | **Admin Logout** | Admin Session | Safely invalidates the administrative session. |
| **`/api/enquiries`** | **Enquiries API** | Public / Internal | JSON endpoint returning registered student leads. |
| **`/api/bookings`** | **Bookings API** | Public / Internal | JSON endpoint returning scheduled demo sessions. |
| **`/health/live`** | **Liveness Probe** | Public | Process health probe returning HTTP 200 `{"status": "alive"}`. |
| **`/health/ready`** | **Readiness Probe** | Public | Database accessibility probe returning HTTP 200 `{"status": "ready", "database": "ok"}`. |

### Administrator Credentials
- **Login URL:** [`http://127.0.0.1:5000/admin/login`](http://127.0.0.1:5000/admin/login)
- **Username:** `admin`
- **Password:** `admin123`

---

## 4. Evaluator 5-Minute Verification Script

Follow these steps to evaluate all core features:

```
[Student Portal]                     [Admin Console]                    [Google Sheets]
      │                                     │                                  │
      ├── 1. Submit Enquiry ───────────────>│                                  │
      │   (Check validation & duplicate)    │                                  │
      │                                     ├── 4. Search & Filter Leads       │
      ├── 2. Book Demo Session ────────────>│                                  │
      │   (Pick date & 3:00 PM slot)        ├── 5. Update Status ('Attended')   │
      │                                     │                                  │
      │                                     ├── 6. Trigger Sync ──────────────>│ (Synced to
      │                                     │      (Verify status badge)       │  both tabs)
```

### Test 1: Submit a New Student Enquiry
1. Navigate to **`http://127.0.0.1:5000/`**.
2. Scroll to **"Start Your Learning Journey"**.
3. Fill in the form:
   - **Student Name:** `Pooja Hegde`
   - **Phone Number:** `+91 98450 12345` *(test phone with spaces and +91 prefix)*
   - **Email Address:** `pooja.hegde@example.com`
   - **Class:** `Class 11`
   - **Exam Goal:** `NEET`
   - **Interested Course:** `NEET Long-Term Preparation`
4. Click **Submit Enquiry**.
5. **Expected Result:** A success alert appears confirming registration, phone number normalizes to canonical `+919845012345`, and Pooja Hegde appears in the Demo Booking dropdown.

### Test 2: Verify Duplicate Phone Prevention
1. Re-enter the same phone number (`9845012345` or `09845012345`) with a different student name.
2. Click **Submit Enquiry**.
3. **Expected Result:** Form submission is rejected with an inline error: *"A student enquiry with this phone number already exists."*

### Test 3: Book a Demo Session
1. In the **"Book Your Demo Session"** card:
   - **Select Student Lead:** Choose `# - Pooja Hegde`
   - **Demo Date:** Select today or tomorrow's date
   - **Demo Time Slot:** `3:00 PM (IST)`
2. Click **Confirm Demo Booking**.
3. **Expected Result:** Confirmation banner appears displaying student details, scheduled date, slot, and meeting link.

### Test 4: Admin Management & Status Update
1. Navigate to [`http://127.0.0.1:5000/admin/login`](http://127.0.0.1:5000/admin/login).
2. Log in with `admin` / `admin123` (use the `👁️` toggle to verify password show/hide).
3. On the **Admin Dashboard**:
   - Verify summary metric cards (Total Leads, Total Bookings, Pending, Confirmed).
   - In the search bar, type `Pooja` and click **Filter**.
   - Change Pooja's booking status from `Booked` to `Attended` and click **Save**.
4. **Expected Result:** Status badge updates immediately in SQLite and reflects on the dashboard.

### Test 5: Verify Google Sheets Synchronization
1. Click **🔄 Retry Sheets Sync** (or **Trigger Sync Now**).
2. **Expected Result:** Status pill displays `✅ Synced (X/X)` indicating all records are synchronized with the Google Sheet tabs.

---

## 5. Technology Stack & Architecture

| Layer | Component | Details |
|---|---|---|
| **Backend Framework** | Python 3.12 / Flask 3.x | Clean architectural separation: routes, controllers, services, repositories. |
| **Database** | SQLite 3 (`database/kmie.db`) | Relational ACID storage, foreign keys enabled (`PRAGMA foreign_keys = ON;`), unique constraints. |
| **Phone Normalization** | Google `phonenumbers` | Parses Indian phone numbers with `'IN'` default region into canonical **E.164** format. |
| **External Cloud Sync** | `gspread` + `google-auth` | Service account integration synchronizing to Google Sheets with automated batching and deduplication. |
| **Security & Auth** | Flask-WTF, Werkzeug Security | CSRF token validation, scrypt password hashing, session cookies, and honeypot anti-spam. |
| **Frontend** | Vanilla HTML5 / CSS3 / JavaScript | Modern institutional UI (Deep Teal / Slate Navy), zero external frontend dependencies. |
| **Test Engine** | Pytest 8.x, pytest-mock | 114 automated tests covering validation, routes, admin security, bookings, and sync. |
| **Production Server** | Gunicorn (`wsgi.py`) | Production WSGI HTTP server configured for Render deployment. |

---

## 6. SQLite Database Schema

Primary database file: **`database/kmie.db`**

```sql
-- Leads Table (Student Enquiries)
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL CHECK(length(trim(student_name)) >= 2),
    phone TEXT NOT NULL,
    phone_e164 TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL CHECK(email LIKE '%@%'),
    class_level INTEGER NOT NULL CHECK(class_level IN (11, 12)),
    exam_goal TEXT NOT NULL CHECK(exam_goal IN ('NEET', 'JEE')),
    interested_course TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    sheet_sync_status TEXT NOT NULL DEFAULT 'pending' CHECK(sheet_sync_status IN ('pending', 'synced', 'failed')),
    sheet_synced_at TEXT,
    sheet_sync_error TEXT
);

-- Bookings Table (Demo Sessions)
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL UNIQUE,
    demo_date TEXT NOT NULL,
    slot_time TEXT NOT NULL CHECK(slot_time IN ('13:00', '15:00', '17:00', '19:00')),
    booking_status TEXT NOT NULL DEFAULT 'Booked' CHECK(booking_status IN ('Booked', 'Attended', 'Not Attended')),
    zoom_link TEXT NOT NULL DEFAULT 'https://zoom.us/j/DEMO-PLACEHOLDER',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    sheet_sync_status TEXT NOT NULL DEFAULT 'pending' CHECK(sheet_sync_status IN ('pending', 'synced', 'failed')),
    sheet_synced_at TEXT,
    sheet_sync_error TEXT,
    FOREIGN KEY (lead_id) REFERENCES leads (id) ON DELETE CASCADE
);
```

---

## 7. Responsive Design System & Breakpoints

The user interface uses a mobile-first CSS architecture with CSS Grid, Flexbox, and `clamp()` fluid typography.

### Responsive Breakpoint Coverage

| Viewport Range | Devices | Layout Adaptation |
|---|---|---|
| **320px – 374px** | iPhone SE, small Android | Single-column form, compact header, tagline hidden, full-width touch buttons. Zero overflow. |
| **375px – 480px** | Standard smartphones | Single-column form, 2-column stats grid, comfortable 44px touch targets. |
| **481px – 767px** | Large smartphones, phablets | 2-column filter grid, responsive form controls, wrap-safe buttons. |
| **768px – 1023px** | Tablets (iPad portrait/landscape) | 2-column form grid, internal scrollable data table, collapsible mobile admin menu drawer. |
| **1024px – 1439px**| Laptops & desktop monitors | Sticky desktop admin sidebar (240px), 4-column overview metrics, 2-column enquiry form. |
| **1440px – 1920px+**| Large displays, Full HD | Centered maximum width container (820px student, 1240px admin) preventing layout stretching. |

---

## 8. Google Sheets Integration Architecture

### Spreadsheet Structure
The target spreadsheet contains two pre-configured tabs:
1. **`Enquiries` Tab**: `Lead ID | Student Name | Phone (Raw) | Phone (E.164) | Email | Class | Exam Goal | Course | Submitted At | Sync Status`
2. **`Demo Bookings` Tab**: `Booking ID | Lead ID | Student Name | Phone | Demo Date | Slot Time | Status | Meeting Link | Booked At | Sync Status`

### Resilient Sync Workflow
```
[Enquiry / Booking Action]
           │
           ▼
[Persist in SQLite (Immediate)] ──> Returns success to user instantly
           │
           ▼
[Background Sync Attempt]
     ├── If Google API Available: Appends / updates row ──> Sets sheet_sync_status = 'synced'
     └── If Network / Cloud Error: Logs warning ──────────> Sets sheet_sync_status = 'pending'
                                                                 │
                                                                 ▼
                                                  Admin clicks '🔄 Retry Sheets Sync'
                                                  (Batches and syncs all pending rows)
```

---

## 9. Running the Automated Test Suite

Run all 114 tests using `pytest`:

```powershell
python -m pytest -v
```

### Test Suite Structure
| Test Module | Tests | Focus Area |
|---|---|---|
| **`tests/test_validators.py`** | 48 | Phone normalization, name length, RFC email, class level, exam goal, demo slot validation. |
| **`tests/test_phone_normalization.py`** | 18 | Edge cases for Indian numbers (`+91`, `0091`, spaces, hyphens, prefixes, invalid lengths). |
| **`tests/test_enquiries.py`** | 12 | Database CRUD, duplicate rejection, check constraints, transaction rollbacks. |
| **`tests/test_bookings.py`** | 15 | Slot collision, past date rejection, single-booking rule, reschedule updates in-place. |
| **`tests/test_routes.py`** | 8 | End-to-end Flask route rendering, CSRF protection, template context verification. |
| **`tests/test_admin_security.py`** | 7 | Session auth, password verification, route protection, health probes (`/health/live`, `/health/ready`). |
| **`tests/test_google_sheets.py`** | 6 | Mocked Google Sheets communication, deduplication logic, error fallback. |
| **Total** | **114** | **100% Passing in ~40 seconds** |

---

## 10. Configuration & Environment Variables (`.env`)

| Variable | Default Value | Description |
|---|---|---|
| `FLASK_ENV` | `development` | Environment mode (`development` or `production`). |
| `SECRET_KEY` | *(Generated string)* | Flask session signing key. |
| `DATABASE_PATH` | `database/kmie.db` | Relative or absolute path to SQLite database. |
| `ADMIN_USERNAME` | `admin` | Administrator login username. |
| `ADMIN_PASSWORD_HASH` | *(scrypt hash for `admin123`)* | Securely hashed password. |
| `GOOGLE_SHEET_ID` | `1E4-bbB2_Ewj3TvKPoHwLmmeaq0C7OJrp6DCucs5nZfk` | ID of the linked Google Spreadsheet. |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | `credentials.json` | Path to Google Service Account JSON key. |
| `APP_TIMEZONE` | `Asia/Kolkata` | Timezone for business logic date validation. |

---

## 11. Project Directory Layout

```
KMIE_Student_Enquiry/
├── app.py                      # Main Flask application factory & route handlers
├── config.py                   # Centralized configuration & environment loader
├── wsgi.py                     # Production WSGI entry point for Gunicorn
├── requirements.txt            # Python package dependencies
├── render.yaml                 # Render Infrastructure-as-Code Blueprint
├── pytest.ini                  # Pytest configuration
├── credentials.json            # Google Service Account JSON credentials
├── .env.example                # Template for environment variables
├── database/
│   ├── kmie.db                 # Primary SQLite database file
│   └── schema.sql              # Relational SQL schema definitions
├── models/
│   ├── enquiry_model.py        # Lead database queries & transaction handlers
│   └── booking_model.py        # Booking database queries & status updater
├── services/
│   ├── auth_service.py         # Admin authentication & session security
│   ├── enquiry_service.py      # Lead business logic & normalization pipeline
│   ├── booking_service.py      # Demo scheduling, validation & rescheduling
│   └── google_sheets_service.py# Google Sheets API client & retry sync engine
├── utils/
│   ├── validators.py           # Two-tier input validation functions
│   └── phone_normalizer.py     # libphonenumber E.164 normalization logic
├── static/
│   ├── css/
│   │   └── style.css           # Institutional design system & responsive rules
│   └── js/
│       └── app.js              # Client-side validation, password toggle & menu
├── templates/
│   ├── base.html               # Base layout, navbar, flash alerts & footer
│   ├── index.html              # Student Portal (single-column enquiry & booking)
│   ├── admin_login.html        # Centered administrator login card
│   ├── admin_dashboard.html    # Admin management console with sidebar
│   └── partials/
│       ├── enquiry_form.html   # Enquiry form inputs & validation messages
│       └── booking_form.html   # Demo booking form inputs & time slot picker
├── scripts/
│   ├── seed_demo_data.py       # Populates sample assessment records
│   ├── generate_admin_hash.py  # Utility to hash administrator passwords
│   └── sync_to_sheets.py       # Standalone CLI synchronization script
└── tests/                      # Automated test suite (114 pytest tests)
```

---

## 12. Assessment Requirements Compliance Checklist

| Requirement | Implementation Detail | Status |
|---|---|---|
| **Student Enquiry Capture** | Name, Phone, Email, Class (11/12), Exam (NEET/JEE), Course | ✅ Verified |
| **Phone Normalization** | Google `phonenumbers` engine normalizing to Indian E.164 format | ✅ Verified |
| **Duplicate Prevention** | Application-level check + database `UNIQUE(phone_e164)` constraint | ✅ Verified |
| **Demo Slot Booking** | Today or future date, 4 slots (`1 PM`, `3 PM`, `5 PM`, `7 PM` IST) | ✅ Verified |
| **One Booking per Student** | `UNIQUE(lead_id)` foreign key constraint; rescheduling updates in-place | ✅ Verified |
| **Attendance Status** | `Booked`, `Attended`, `Not Attended` tracked and updated in real time | ✅ Verified |
| **Admin Console** | Search by name/phone/email, class & goal filters, inline status updates | ✅ Verified |
| **Google Sheets Sync** | Two-tab live sync (`Enquiries`, `Demo Bookings`) with web UI retry trigger | ✅ Verified |
| **Responsive Design** | Fluid layouts tested and verified across 320px–1920px viewports | ✅ Verified |
| **CSRF & Security** | Flask-WTF tokens on all POST requests, scrypt hashing, honeypot field | ✅ Verified |
| **Automated Testing** | 114 automated tests passing without external dependency requirements | ✅ Verified |
| **Deployment Ready** | Gunicorn `wsgi.py`, Render blueprint (`render.yaml`), health probes | ✅ Verified |

---

## 13. Troubleshooting & FAQ

**Q: Port 5000 is already in use.**  
*Fix:* Run Flask on an alternative port:
```powershell
python app.py --port 5001
```
Or stop the existing process using port 5000 in Task Manager / PowerShell:
```powershell
Stop-Process -Id (Get-NetTCPConnection -LocalPort 5000).OwningProcess -Force
```

**Q: Can the application run if Google Sheets is offline?**  
*Yes.* The application is designed to be offline-first. SQLite retains all records safely and flags sync as `pending`. When internet connectivity or credentials are restored, an administrator can click **🔄 Retry Sheets Sync** to batch upload all pending rows.

**Q: How do I reset the local database?**  
*Fix:* Delete `database/kmie.db` and run the application. The schema initializes automatically. To populate sample records, run `python -m scripts.seed_demo_data`.
