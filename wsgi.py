"""
wsgi.py — WSGI Entry point for Gunicorn production deployment.
Usage:
    gunicorn wsgi:app --workers 2 --bind 0.0.0.0:5000
"""
from app import app

if __name__ == "__main__":
    app.run()
