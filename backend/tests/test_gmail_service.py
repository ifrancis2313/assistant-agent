import pytest
from unittest.mock import patch, MagicMock


def make_gmail_message(msg_id="msg1", sender="boss@work.com",
                        subject="Action required", snippet="Please submit by Friday"):
    return {
        "id": msg_id,
        "payload": {
            "headers": [
                {"name": "From", "value": sender},
                {"name": "Subject", "value": subject},
            ]
        },
        "snippet": snippet,
    }


def make_list_response(message_ids):
    return {"messages": [{"id": mid} for mid in message_ids]}


def test_fetch_emails_returns_correct_fields():
    from app.services.gmail_service import fetch_emails

    mock_creds = MagicMock()
    mock_service = MagicMock()
    mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = \
        make_list_response(["msg1"])
    mock_service.users.return_value.messages.return_value.get.return_value.execute.return_value = \
        make_gmail_message("msg1", "boss@work.com", "Submit report", "Please submit by Friday")

    with patch("app.services.gmail_service.get_credentials", return_value=mock_creds), \
         patch("app.services.gmail_service.build", return_value=mock_service):
        result = fetch_emails("test@gmail.com", days=7, limit=25)

    assert len(result) == 1
    assert result[0]["id"] == "msg1"
    assert result[0]["from"] == "boss@work.com"
    assert result[0]["subject"] == "Submit report"
    assert result[0]["snippet"] == "Please submit by Friday"


def test_fetch_emails_returns_empty_when_no_credentials():
    from app.services.gmail_service import fetch_emails

    with patch("app.services.gmail_service.get_credentials", return_value=None):
        result = fetch_emails("nobody@gmail.com", days=7, limit=25)

    assert result == []


def test_fetch_emails_returns_empty_when_no_messages():
    from app.services.gmail_service import fetch_emails

    mock_creds = MagicMock()
    mock_service = MagicMock()
    mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {}

    with patch("app.services.gmail_service.get_credentials", return_value=mock_creds), \
         patch("app.services.gmail_service.build", return_value=mock_service):
        result = fetch_emails("test@gmail.com", days=7, limit=25)

    assert result == []


def test_fetch_emails_respects_limit():
    from app.services.gmail_service import fetch_emails

    mock_creds = MagicMock()
    mock_service = MagicMock()
    mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = \
        make_list_response([f"msg{i}" for i in range(30)])
    mock_service.users.return_value.messages.return_value.get.return_value.execute.return_value = \
        make_gmail_message()

    with patch("app.services.gmail_service.get_credentials", return_value=mock_creds), \
         patch("app.services.gmail_service.build", return_value=mock_service):
        result = fetch_emails("test@gmail.com", days=7, limit=25)

    assert len(result) <= 25


def test_fetch_emails_passes_date_filter_to_api():
    from app.services.gmail_service import fetch_emails

    mock_creds = MagicMock()
    mock_service = MagicMock()
    mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {}

    with patch("app.services.gmail_service.get_credentials", return_value=mock_creds), \
         patch("app.services.gmail_service.build", return_value=mock_service):
        fetch_emails("test@gmail.com", days=7, limit=25)

    list_call = mock_service.users.return_value.messages.return_value.list.call_args
    query = list_call.kwargs.get("q", "")
    assert "after:" in query
