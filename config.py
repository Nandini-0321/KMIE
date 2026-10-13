"""
config.py — Application configuration for KMIE Student Enquiry & Demo Booking.
Loads environment variables and sets up local SQLite database parameters.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from database.db import get_db_path, init_db

load_dotenv()


class Config:
    """Central application configuration."""

    ENV: str = os.getenv("APP_ENV") or os.getenv("FLASK_ENV", "development")
    DEBUG: bool = ENV == "development"

    SECRET_KEY: str = (
        os.getenv("APP_SECRET_KEY")
        or os.getenv("FLASK_SECRET_KEY", "kmie-assessment-local-secret-2026")
    )

    DATABASE_PATH: Path = get_db_path()
    DEMO_MEETING_URL: str = os.getenv(
        "DEMO_MEETING_URL", "https://zoom.us/j/DEMO-PLACEHOLDER"
    )


def initialize_app_database():
    """Ensure database directory, tables, and default seed data are ready."""
    init_db(seed_samples=True)
