# Security Policy & Implementation Architecture

## 1. Scope & Context
This document outlines the security controls implemented in the **KMIE Student Enquiry & Demo Booking Automation System**.

---

## 2. Authentication & Credential Security

### Administrator Access Control
- **Werkzeug Password Hashing**: Passwords are never stored in plaintext. Passwords are encrypted using modern `scrypt` or `pbkdf2:sha256` key derivation algorithms via `werkzeug.security`.
- **Generation Tool**: A dedicated CLI utility ([`scripts/generate_admin_hash.py`](file:///c:/Users/Nandini/Documents/Projects/KMIE_Project/KMIE_Student_Enquiry/scripts/generate_admin_hash.py)) generates secure password hashes for the `ADMIN_PASSWORD_HASH` environment variable.
- **Protected Routing**: All administrative endpoints (`/admin`, `/admin/dashboard`, `/admin/booking/*`, `/admin/sync/*`) are guarded by the server-side `@admin_required` session decorator.
- **Session Protection**: Flask sessions are configured with:
  - `SESSION_COOKIE_HTTPONLY = True` (mitigates XSS cookie exfiltration).
  - `SESSION_COOKIE_SAMESITE = 'Lax'` (mitigates cross-site request forgery).
  - `SESSION_COOKIE_SECURE = True` in production environments.

---

## 3. Form & API Defense Mechanisms

### CSRF (Cross-Site Request Forgery)
- **Flask-WTF CSRF Protection**: Initialized globally via `CSRFProtect(app)`.
- **Cryptographic Tokens**: Every state-changing HTML form includes `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>`.
- **Meta Tag Injection**: `<meta name="csrf-token" content="{{ csrf_token() }}">` allows authenticated AJAX requests if required.

### Anti-Spam Honeypot
- The public student enquiry form includes an invisible honeypot field (`website_url`).
- Legitimate users do not see or populate this field; automated bot submissions that populate it are silently discarded without polluting the database.

---

## 4. Database Security & Data Integrity

### Local SQLite Database (`database/kmie.db`)
- **Parameterized SQL Queries**: All database interactions use parameter substitution (`?`), eliminating SQL injection vulnerabilities.
- **Relational Integrity**: `PRAGMA foreign_keys = ON;` is enforced on every connection, guaranteeing that deleting a lead automatically cascades to its associated demo bookings.
- **Unique Constraint Enforcement**: `phone_e164` and `lead_id` uniqueness constraints prevent race conditions and duplicate writes.
- **Safe Transaction Handling**: Transactions use structured `BEGIN / COMMIT / ROLLBACK` patterns to prevent partial or corrupted database writes.

---

## 5. External Credentials Management (Google Sheets)

- **In-Memory Base64 Decoding**: Google Cloud service account keys are supplied as base64-encoded strings (`GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`) and decoded strictly in memory.
- **Zero Secrets Logging**: Private keys and service account credentials are never printed to console logs or error traces.
- **`.gitignore` Rules**: All `.env`, `*.json`, and credential artifacts are strictly excluded from version control.

---

## 6. Production Hardening Checklist

When deploying to a public host (such as Render):
1. Set `APP_ENV=production` and `FLASK_ENV=production` to disable debug mode.
2. Generate a cryptographically strong secret key (`APP_SECRET_KEY`).
3. Deploy behind a production WSGI HTTP server like Gunicorn (`gunicorn wsgi:app --workers 2`).
4. Mount a persistent disk volume to ensure SQLite database preservation across container restarts.
