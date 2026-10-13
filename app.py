"""
app.py — KMIE Student Enquiry & Demo Booking Automation System
Flask application entry point with local SQLite persistence (database/kmie.db),
CSRF protection, Google Sheets synchronization, and a protected Admin Dashboard.
"""
import logging
import os
import sqlite3

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session,
)
from flask_wtf.csrf import CSRFProtect

from config import Config, initialize_app_database
from database.db import get_db_connection
from services.enquiry_service import (
    submit_enquiry,
    get_all_enquiries,
    get_enquiry_by_id,
)
from services.booking_service import (
    create_or_reschedule_booking,
    update_booking_status,
    get_all_bookings,
)
from services.google_sheets_service import (
    is_configured as is_sheets_configured,
    retry_all_pending_syncs,
)
from services.auth_service import verify_admin_login, admin_required

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if os.getenv("FLASK_ENV") == "development" else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("kmie_app")

# ---------------------------------------------------------------------------
# Flask App Factory & Security Configuration
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Session and cookie security
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("FLASK_ENV") == "production"
app.config["WTF_CSRF_TIME_LIMIT"] = None

csrf = CSRFProtect(app)

# Initialize SQLite database schema safely (without destructive resets)
try:
    initialize_app_database()
    logger.info("SQLite database verified at %s", Config.DATABASE_PATH)
except Exception as exc:
    logger.error("Database initialization failed: %s", exc)


def _compute_stats(enquiries, bookings):
    return {
        "total_enquiries": len(enquiries),
        "total_bookings": len(bookings),
        "booked": sum(1 for b in bookings if b.get("booking_status") == "Booked" or b.get("status") == "Booked"),
        "attended": sum(1 for b in bookings if b.get("booking_status") == "Attended" or b.get("status") == "Attended"),
        "not_attended": sum(1 for b in bookings if b.get("booking_status") == "Not Attended" or b.get("status") == "Not Attended"),
        "sheet_synced": sum(1 for e in enquiries if e.get("sheet_sync_status") == "synced"),
    }


# ---------------------------------------------------------------------------
# Health Check Endpoints (For Render Blueprint Probes)
# ---------------------------------------------------------------------------

@app.route("/health/live")
@app.route("/health")
def health_live():
    """Liveness probe: verifies process responsiveness."""
    return jsonify({"status": "alive", "service": "kmie-booking-system"}), 200


@app.route("/health/ready")
def health_ready():
    """Readiness probe: verifies database accessibility and external services."""
    db_ok = False
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1 FROM leads LIMIT 1")
        conn.close()
        db_ok = True
    except Exception as exc:
        logger.warning("Readiness probe DB check warning: %s", exc)

    return jsonify({
        "status": "ready" if db_ok else "degraded",
        "database": "ok" if db_ok else "error",
        "google_sheets_configured": is_sheets_configured(),
    }), 200 if db_ok else 503


# ---------------------------------------------------------------------------
# Public Portal Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Public portal: student enquiry form, booking form, and records."""
    db_status = "connected"
    error_message = None
    enquiries = []
    bookings = []

    try:
        enquiries = get_all_enquiries()
        bookings = get_all_bookings()
    except Exception as exc:
        db_status = "error"
        error_message = f"Database read failure: {exc}"
        logger.error("Error reading database: %s", exc)

    stats = _compute_stats(enquiries, bookings)

    return render_template(
        "index.html",
        enquiries=enquiries,
        bookings=bookings,
        stats=stats,
        db_status=db_status,
        error_message=error_message,
    )


@app.route("/enquiry/submit", methods=["POST"])
def submit_enquiry_route():
    """Handle public student enquiry form submission."""
    # Honeypot spam check
    if request.form.get("website_url", "").strip():
        logger.warning("Spam submission blocked by honeypot field.")
        return redirect(url_for("index") + "#enquiry-form")

    form_data = {
        "student_name": request.form.get("student_name", ""),
        "phone": request.form.get("phone", ""),
        "email": request.form.get("email", ""),
        "class_level": request.form.get("class_level", ""),
        "student_class": request.form.get("class_level", ""),
        "exam_goal": request.form.get("exam_goal", ""),
        "interested_course": request.form.get("interested_course", ""),
        "course": request.form.get("interested_course", ""),
    }

    result = submit_enquiry(form_data)

    if result.get("success"):
        lead = result["lead"]
        sync_note = " (Synced to Google Sheets)" if result.get("sheet_synced") else " (Google Sheets sync pending)"
        flash(
            f"✅ Enquiry submitted successfully! "
            f"Lead ID: #{lead['id']} — Welcome, {lead['student_name']}!{sync_note}",
            "success",
        )
    elif result.get("duplicate"):
        flash(result["message"], "warning")
    elif result.get("errors"):
        for field, msg in result["errors"].items():
            flash(msg, "error")
        for key, val in form_data.items():
            flash(f"__field__{key}={val}", "field")
    elif result.get("db_error"):
        flash(result["message"], "error")
    else:
        flash("An unexpected error occurred. Please try again.", "error")

    return redirect(url_for("index") + "#enquiry-form")


@app.route("/booking/create", methods=["POST"])
@app.route("/booking/schedule", methods=["POST"])
def create_booking_route():
    """Handle demo booking submission or rescheduling."""
    form_data = {
        "lead_id": request.form.get("lead_id", ""),
        "demo_date": request.form.get("demo_date", ""),
        "slot_time": request.form.get("slot_time", ""),
        "demo_time": request.form.get("slot_time", ""),
    }

    result = create_or_reschedule_booking(form_data)

    if result.get("success"):
        flash(result["confirmation"], "booking_success")
    elif result.get("errors"):
        for field, msg in result["errors"].items():
            flash(msg, "error")
    elif result.get("db_error"):
        flash(result["message"], "error")
    else:
        flash("An unexpected error occurred while scheduling the demo.", "error")

    return redirect(url_for("index") + "#booking-form")


@app.route("/booking/update-status", methods=["POST"])
def update_status_route():
    """Allow quick public status updates for existing bookings."""
    booking_id = request.form.get("booking_id", "").strip()
    new_status = request.form.get("status", "").strip()

    if not booking_id:
        flash("Booking ID is required.", "error")
        return redirect(url_for("index") + "#bookings-table")

    result = update_booking_status(booking_id, new_status)

    if result.get("success"):
        flash(f"✅ Booking status updated to '{new_status}'.", "success")
    else:
        flash(result.get("message", "Failed to update status."), "error")

    return redirect(url_for("index") + "#bookings-table")


@app.route("/api/enquiries")
def api_enquiries():
    """JSON endpoint returning all registered student leads."""
    try:
        leads = get_all_enquiries()
        return jsonify({"success": True, "data": leads})
    except Exception as exc:
        logger.error("API error fetching leads: %s", exc)
        return jsonify({"success": False, "message": "Database error."}), 500


# ---------------------------------------------------------------------------
# Protected Administrator Routes
# ---------------------------------------------------------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page and authentication."""
    if session.get("is_admin"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if verify_admin_login(username, password):
            session["is_admin"] = True
            session["admin_user"] = username.strip()
            flash("Welcome to the Admin Management Console.", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid administrator username or password.", "error")

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    """Terminate admin session."""
    session.pop("is_admin", None)
    session.pop("admin_user", None)
    flash("You have been logged out safely.", "success")
    return redirect(url_for("admin_login"))


@app.route("/admin")
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """Protected admin dashboard with search, filtering, and status controls."""
    search_query = request.args.get("search", "").strip()
    class_filter = request.args.get("class_filter", "").strip()
    goal_filter = request.args.get("goal_filter", "").strip()

    leads = get_all_enquiries(
        search=search_query or None,
        class_filter=class_filter or None,
        goal_filter=goal_filter or None,
    )
    all_bookings = get_all_bookings()
    all_leads = get_all_enquiries()

    # Map bookings by lead_id for table row alignment
    bookings_by_lead = {b["lead_id"]: b for b in all_bookings}

    stats = _compute_stats(all_leads, all_bookings)

    return render_template(
        "admin_dashboard.html",
        leads=leads,
        bookings_by_lead=bookings_by_lead,
        stats=stats,
        search_query=search_query,
        class_filter=class_filter,
        goal_filter=goal_filter,
    )


@app.route("/admin/booking/update-status", methods=["POST"])
@admin_required
def admin_update_booking_status():
    """Admin action to update a booking status."""
    booking_id = request.form.get("booking_id", "").strip()
    new_status = request.form.get("status", "").strip()

    result = update_booking_status(booking_id, new_status)
    if result.get("success"):
        flash(f"✅ Booking #{booking_id} status updated to '{new_status}'.", "success")
    else:
        flash(result.get("message", "Failed to update booking status."), "error")

    return redirect(url_for("admin_dashboard"))


@app.route("/admin/booking/schedule", methods=["POST"])
@admin_required
def admin_schedule_booking():
    """Admin action to schedule or reschedule a booking."""
    form_data = {
        "lead_id": request.form.get("lead_id", ""),
        "demo_date": request.form.get("demo_date", ""),
        "slot_time": request.form.get("slot_time", ""),
    }

    result = create_or_reschedule_booking(form_data)
    if result.get("success"):
        action_word = "rescheduled" if result.get("rescheduled") else "scheduled"
        flash(f"✅ Demo booking {action_word} successfully.", "success")
    elif result.get("errors"):
        for field, msg in result["errors"].items():
            flash(msg, "error")
    else:
        flash(result.get("message", "Failed to schedule booking."), "error")

    return redirect(url_for("admin_dashboard"))


@app.route("/admin/sync/retry", methods=["POST"])
@admin_required
def admin_retry_sync():
    """Admin trigger to retry pending or failed Google Sheets synchronizations."""
    if not is_sheets_configured():
        flash("⚠️ Google Sheets integration is unconfigured in your environment variables.", "warning")
        return redirect(url_for("admin_dashboard"))

    synced, failed = retry_all_pending_syncs()
    if failed == 0 and synced > 0:
        flash(f"✅ Google Sheets sync complete! Synced {synced} record(s).", "success")
    elif failed > 0:
        flash(f"Synced {synced} record(s), but {failed} record(s) failed. Check logs.", "warning")
    else:
        flash("All records are already up to date in Google Sheets.", "success")

    return redirect(url_for("admin_dashboard"))


# ---------------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    enquiries = get_all_enquiries()
    bookings = get_all_bookings()
    stats = _compute_stats(enquiries, bookings)
    return render_template(
        "index.html",
        enquiries=enquiries,
        bookings=bookings,
        stats=stats,
        error_message="Page not found.",
        db_status="connected",
    ), 404


@app.errorhandler(500)
def server_error(e):
    logger.error("Internal Server Error (500): %s", e)
    enquiries = get_all_enquiries()
    bookings = get_all_bookings()
    stats = _compute_stats(enquiries, bookings)
    return render_template(
        "index.html",
        enquiries=enquiries,
        bookings=bookings,
        stats=stats,
        error_message="Internal server error occurred.",
        db_status="error",
    ), 500


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=Config.DEBUG, host="127.0.0.1", port=5000)
