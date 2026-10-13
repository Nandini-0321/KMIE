# KMIE Assessment 3–5 Minute Demonstration Script

**Candidate:** Nandini R  
**Role:** Software Developer & Automation Intern  
**Project:** KMIE Student Enquiry & Demo Booking Automation  

---

### Introduction (0:00 – 0:30)
> *"Hello! My name is Nandini R, and this is my practical assessment demonstration for the Software Developer & Automation Intern position at Komali Mam Institute of Excellence (KMIE).*
>
> *Today, I will walk you through our complete Student Enquiry and Demo Booking Automation System built with Python, Flask, a persistent local SQLite database (`database/kmie.db`), Google Sheets API synchronization, and a protected Administrator Console."*
>
> *(Show browser on `http://127.0.0.1:5000`)*
>
> *"Here on the public student portal, we have our clean Emerald and Teal dashboard overview displaying live database counters, the enquiry form, and the booking scheduler."*

---

### Scenario 1: New Student Enquiry Submission (0:30 – 1:00)
> *"Let's submit a new student enquiry."*
>
> 1. Scroll to the **New Student Enquiry** form.
> 2. Fill in:
>    - **Student Name**: `Ananya Verma`
>    - **Phone Number**: `9812345678`
>    - **Email**: `ananya.verma@example.com`
>    - **Class**: `Class 11`
>    - **Exam Goal**: `NEET`
>    - **Interested Course**: `NEET Long-Term Preparation`
> 3. Click **Submit Enquiry**.
> 4. Point out:
>    - Success banner: *"✅ Enquiry submitted successfully! Lead ID: #... — Welcome, Ananya Verma!"*
>    - The new student appears at the top of the **Student Enquiries** table.
>    - Phone number is normalized to E.164 (`+919812345678`).
>    - Lead is immediately available in the demo booking selector.

---

### Scenario 2: Saved Lead in SQLite & Google Sheets Sync (1:00 – 1:30)
> *"Data is immediately committed to our local SQLite database at `database/kmie.db`.*
>
> *If Google Sheets credentials are configured, the enquiry row is appended to the **Enquiries** tab. If offline or unconfigured, the system marks the synchronization status as `pending` without interrupting the student's submission."*

---

### Scenario 3: Duplicate Submission with Different Phone Formatting (1:30 – 2:15)
> *"Now, let's test our duplicate prevention system. Suppose the same parent or student submits the form again using spaces, dashes, or the country code `+91`."*
>
> 1. In the Enquiry form, enter:
>    - **Student Name**: `Ananya Verma`
>    - **Phone Number**: `+91 98123 45678` *(Different format, same canonical number)*
>    - **Email**: `ananya.verma@example.com`
>    - **Class**: `Class 11`
>    - **Exam Goal**: `NEET`
>    - **Interested Course**: `NEET Long-Term Preparation`
> 2. Click **Submit Enquiry**.
> 3. Point out:
>    - Warning banner: *"⚠️ This phone number is already registered under the name 'Ananya Verma' (Lead ID: #...). Please use the existing enquiry for demo booking."*
>    - Scroll to the table: confirm that no second lead was created.
>    - Explain: *"Our `phonenumbers` engine canonicalizes both representations to E.164 `+919812345678`, enforced at both the Flask layer and via a SQLite `UNIQUE(phone_e164)` constraint."*

---

### Scenario 4: Demo Booking & Confirmation (2:15 – 3:00)
> *"Next, let's book a demo session for Ananya."*
>
> 1. Scroll to **Book a Demo Session**.
> 2. Select:
>    - **Student Lead**: `Ananya Verma`
>    - **Demo Date**: *(Pick a future date, e.g., 3 days ahead)*
>    - **Demo Time Slot**: `3:00 PM (IST)` (internally stored as `15:00`)
> 3. Click **Confirm Demo Booking**.
> 4. Point out:
>    - Confirmation box:
>      ```
>      ✅ Demo Booking Confirmed!
>      Student Name : Ananya Verma
>      Demo Date    : Thursday, 16 October 2026
>      Demo Time    : 3:00 PM (IST)
>      Meeting Link : https://zoom.us/j/DEMO-PLACEHOLDER
>      ```
>    - Notice that each student maintains exactly one current booking. If rescheduled later, the existing record is updated in-place.

---

### Scenario 5: Protected Admin Console & Booking Status Management (3:00 – 3:45)
> *"Now let's examine the Administrator Console."*
>
> 1. Click **🔐 Admin Login** in the header.
> 2. Enter credentials (`admin` / `admin123`).
> 3. Click **Log In to Dashboard**.
> 4. Point out:
>    - Protected management console with summary metrics.
>    - Multi-criteria search and filter by student name, phone, class, and exam goal.
>    - In the table, find Ananya's row and change status from `Booked` to `Attended`.
>    - Click **Save**.
>    - Point out that the green `Attended` counter increments, and the change persists in `database/kmie.db` across server restarts.

---

### Scenario 6: Google Sheets Failure & Successful Retry (3:45 – 4:15)
> *"In the top bar, we have a dedicated **🔄 Retry Sheets Sync** button.*
>
> *If Google Sheets experienced temporary network downtime, SQLite retains the record with status `failed` or `pending`. Once connectivity resumes, clicking Retry synchronizes all pending records. The sync engine locates existing rows by ID and updates them, guaranteeing zero duplicate spreadsheet rows."*

---

### Scenario 7: Validation, Anti-Spam & Failure Handling (4:15 – 4:45)
> *"Lastly, our system enforces robust failure handling:
> - Invalid or past demo dates are rejected by both HTML5 `min` attributes and server-side Python checks.
> - Invalid phone numbers (such as `12345`) are rejected with understandable messages.
> - A hidden honeypot field transparently traps automated spam submissions.
> - Database transactions utilize automatic rollbacks to prevent corrupt states.
> - Health check probes at `/health/live` and `/health/ready` ensure production readiness on hosts like Render."*

---

### Conclusion (4:45 – 5:00)
> *"To conclude: All assessment requirements across enquiry capture, duplicate prevention, SQLite persistence, demo scheduling, status management, admin security, and Google Sheets sync are implemented and verified with 114 passing automated tests. Thank you!"*
