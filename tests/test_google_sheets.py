"""
tests/test_google_sheets.py — Tests for Google Sheets synchronization and retry logic.
Mocks Google Sheets API calls so tests run isolated offline without external credentials.
"""
from unittest.mock import MagicMock, patch
from services.google_sheets_service import (
    sync_lead_to_sheet,
    sync_booking_to_sheet,
    retry_all_pending_syncs,
    is_configured,
)


def test_is_configured_logic(monkeypatch):
    monkeypatch.delenv("GOOGLE_SHEET_ID", raising=False)
    monkeypatch.delenv("GOOGLE_SERVICE_ACCOUNT_JSON_BASE64", raising=False)
    assert is_configured() is False

    monkeypatch.setenv("GOOGLE_SHEET_ID", "sheet-id")
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON_BASE64", "base64-json")
    assert is_configured() is True


def test_sheets_graceful_handling_when_unconfigured(temp_db):
    temp_db.execute(
        """
        INSERT INTO leads (
            id, student_name, phone, phone_e164, email, class_level,
            exam_goal, interested_course, created_at, updated_at, sheet_sync_status
        ) VALUES (1, 'Test Lead', '9876543210', '+919876543210', 't@test.com', 11, 'NEET', 'Course', 'now', 'now', 'pending')
        """
    )
    temp_db.commit()

    with patch("services.google_sheets_service.is_configured", return_value=False):
        success = sync_lead_to_sheet({"id": 1, "student_name": "Test Lead"}, temp_db)
        assert success is False

        # Lead must remain safely in SQLite with status 'pending'
        row = temp_db.execute("SELECT sheet_sync_status, sheet_sync_error FROM leads WHERE id = 1").fetchone()
        assert row["sheet_sync_status"] == "pending"
        assert "unconfigured" in row["sheet_sync_error"].lower()


def test_sync_lead_to_sheet_success(monkeypatch, temp_db):
    monkeypatch.setenv("GOOGLE_SHEET_ID", "mock-sheet-123")
    monkeypatch.setenv("GOOGLE_SERVICE_ACCOUNT_JSON_BASE64", "mock-b64")

    mock_client = MagicMock()
    mock_sh = MagicMock()
    mock_ws = MagicMock()

    mock_client.open_by_key.return_value = mock_sh
    mock_sh.worksheet.return_value = mock_ws
    mock_ws.find.return_value = None  # No existing row, should append
    mock_ws.row_values.return_value = ["Lead ID"]  # Headers already present

    temp_db.execute(
        """
        INSERT INTO leads (
            id, student_name, phone, phone_e164, email, class_level,
            exam_goal, interested_course, created_at, updated_at, sheet_sync_status
        ) VALUES (10, 'Aarav Sharma', '9876543210', '+919876543210', 'aarav@test.com', 11, 'NEET', 'Course', 'now', 'now', 'pending')
        """
    )
    temp_db.commit()

    with patch("services.google_sheets_service.get_sheets_client", return_value=mock_client):
        lead_data = {
            "id": 10,
            "student_name": "Aarav Sharma",
            "phone_e164": "+919876543210",
            "email": "aarav@test.com",
            "class_level": 11,
            "exam_goal": "NEET",
            "interested_course": "Course",
            "created_at": "2026-10-13T10:00:00",
        }
        success = sync_lead_to_sheet(lead_data, temp_db)
        assert success is True
        mock_ws.append_row.assert_called_once()

        # Verify SQLite row was marked as 'synced'
        row = temp_db.execute("SELECT sheet_sync_status, sheet_synced_at FROM leads WHERE id = 10").fetchone()
        assert row["sheet_sync_status"] == "synced"
        assert row["sheet_synced_at"] is not None


def test_retry_without_duplicate_rows(monkeypatch, temp_db):
    """Verify that updating an already present lead updates the cell rather than appending a duplicate row."""
    monkeypatch.setenv("GOOGLE_SHEET_ID", "mock-sheet-123")

    mock_client = MagicMock()
    mock_sh = MagicMock()
    mock_ws = MagicMock()

    mock_client.open_by_key.return_value = mock_sh
    mock_sh.worksheet.return_value = mock_ws
    mock_ws.row_values.return_value = ["Lead ID"]

    # Simulate that Lead ID 10 is found at row 4
    mock_cell = MagicMock()
    mock_cell.row = 4
    mock_ws.find.return_value = mock_cell

    temp_db.execute(
        """
        INSERT INTO leads (
            id, student_name, phone, phone_e164, email, class_level,
            exam_goal, interested_course, created_at, updated_at, sheet_sync_status
        ) VALUES (10, 'Aarav Sharma', '9876543210', '+919876543210', 'aarav@test.com', 11, 'NEET', 'Course', 'now', 'now', 'failed')
        """
    )
    temp_db.commit()

    with patch("services.google_sheets_service.is_configured", return_value=True):
        with patch("services.google_sheets_service.get_sheets_client", return_value=mock_client):
            lead_data = {
                "id": 10,
                "student_name": "Aarav Sharma",
                "phone_e164": "+919876543210",
                "email": "aarav@test.com",
                "class_level": 11,
                "exam_goal": "NEET",
                "interested_course": "Course",
            }
            success = sync_lead_to_sheet(lead_data, temp_db)
            assert success is True

            # Must call update on row 4, NOT append_row
            mock_ws.update.assert_called_once()
            mock_ws.append_row.assert_not_called()
