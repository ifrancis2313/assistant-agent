import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone


def make_event(event_id="evt1", summary="Test Event", start_dt="2026-05-20T10:00:00Z", all_day=False):
    start = {"date": "2026-05-20"} if all_day else {"dateTime": start_dt}
    return {"id": event_id, "summary": summary, "start": start, "description": ""}


def test_fetch_events_returns_list_of_events():
    from app.services.google_calendar_service import fetch_events

    mock_creds = MagicMock()
    mock_service = MagicMock()
    mock_service.events.return_value.list.return_value.execute.return_value = {
        "items": [make_event("evt1", "SIC Meeting"), make_event("evt2", "ECON Exam")]
    }

    with patch("app.services.google_calendar_service.get_credentials", return_value=mock_creds), \
         patch("app.services.google_calendar_service.build", return_value=mock_service):
        result = fetch_events("test@gmail.com", days_ahead=14)

    assert len(result) == 2
    assert result[0]["id"] == "evt1"
    assert result[0]["summary"] == "SIC Meeting"


def test_fetch_events_skips_all_day_events():
    from app.services.google_calendar_service import fetch_events

    mock_creds = MagicMock()
    mock_service = MagicMock()
    mock_service.events.return_value.list.return_value.execute.return_value = {
        "items": [
            make_event("evt1", "Timed Event", all_day=False),
            make_event("evt2", "All Day Event", all_day=True),
        ]
    }

    with patch("app.services.google_calendar_service.get_credentials", return_value=mock_creds), \
         patch("app.services.google_calendar_service.build", return_value=mock_service):
        result = fetch_events("test@gmail.com", days_ahead=14)

    assert len(result) == 1
    assert result[0]["summary"] == "Timed Event"


def test_fetch_events_returns_empty_list_when_no_credentials():
    from app.services.google_calendar_service import fetch_events

    with patch("app.services.google_calendar_service.get_credentials", return_value=None):
        result = fetch_events("nobody@gmail.com", days_ahead=14)

    assert result == []


def test_create_reminder_event_calls_calendar_api_with_correct_payload():
    from app.services.google_calendar_service import create_reminder_event

    mock_creds = MagicMock()
    mock_service = MagicMock()
    mock_service.events.return_value.insert.return_value.execute.return_value = {"id": "evt_new"}

    reminder_dt = datetime(2026, 5, 20, 14, 0, 0, tzinfo=timezone.utc)

    with patch("app.services.google_calendar_service.get_credentials", return_value=mock_creds), \
         patch("app.services.google_calendar_service.build", return_value=mock_service), \
         patch("app.services.google_calendar_service.get_all_tokens", return_value=[{"account_email": "test@gmail.com"}]):
        create_reminder_event("Submit SIC report", reminder_dt)

    insert_call = mock_service.events.return_value.insert.call_args
    body = insert_call.kwargs["body"]
    assert "Submit SIC report" in body["summary"]
    assert body["reminders"]["overrides"][0]["method"] == "popup"
    assert body["reminders"]["overrides"][0]["minutes"] == 0


def test_create_reminder_event_does_nothing_when_no_google_accounts():
    from app.services.google_calendar_service import create_reminder_event

    reminder_dt = datetime(2026, 5, 20, 14, 0, 0, tzinfo=timezone.utc)

    with patch("app.services.google_calendar_service.get_all_tokens", return_value=[]) as mock_tokens, \
         patch("app.services.google_calendar_service.build") as mock_build:
        create_reminder_event("Some task", reminder_dt)

    mock_build.assert_not_called()


def test_fetch_events_returns_empty_when_calendar_has_no_items():
    from app.services.google_calendar_service import fetch_events

    mock_creds = MagicMock()
    mock_service = MagicMock()
    mock_service.events.return_value.list.return_value.execute.return_value = {"items": []}

    with patch("app.services.google_calendar_service.get_credentials", return_value=mock_creds), \
         patch("app.services.google_calendar_service.build", return_value=mock_service):
        result = fetch_events("test@gmail.com", days_ahead=14)

    assert result == []
