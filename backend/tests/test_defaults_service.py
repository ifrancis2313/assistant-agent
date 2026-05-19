import pytest
from unittest.mock import patch, MagicMock
from app.services.defaults_service import get_defaults, set_defaults


def make_defaults_row(sync_type="gmail", accounts=None, days=7):
    return {
        "id": "abc-123",
        "sync_type": sync_type,
        "accounts": accounts or ["test@gmail.com"],
        "days": days,
    }


def test_get_defaults_returns_row_when_exists():
    mock_result = MagicMock()
    mock_result.data = [make_defaults_row("gmail", ["a@gmail.com", "b@gmail.com"], 7)]

    with patch("app.services.defaults_service.get_client") as mock_client:
        mock_client.return_value.table.return_value \
            .select.return_value \
            .eq.return_value \
            .limit.return_value \
            .execute.return_value = mock_result

        result = get_defaults("gmail")

    assert result is not None
    assert result["accounts"] == ["a@gmail.com", "b@gmail.com"]
    assert result["days"] == 7


def test_get_defaults_returns_none_when_not_set():
    mock_result = MagicMock()
    mock_result.data = []

    with patch("app.services.defaults_service.get_client") as mock_client:
        mock_client.return_value.table.return_value \
            .select.return_value \
            .eq.return_value \
            .limit.return_value \
            .execute.return_value = mock_result

        result = get_defaults("gmail")

    assert result is None


def test_get_defaults_works_for_each_sync_type():
    mock_result = MagicMock()
    mock_result.data = [make_defaults_row("google_calendar", days=14)]

    with patch("app.services.defaults_service.get_client") as mock_client:
        mock_client.return_value.table.return_value \
            .select.return_value \
            .eq.return_value \
            .limit.return_value \
            .execute.return_value = mock_result

        result = get_defaults("google_calendar")

    assert result["days"] == 14


def test_set_defaults_upserts_row():
    mock_result = MagicMock()
    mock_result.data = [make_defaults_row()]

    with patch("app.services.defaults_service.get_client") as mock_client:
        mock_client.return_value.table.return_value \
            .upsert.return_value \
            .execute.return_value = mock_result

        set_defaults("gmail", ["a@gmail.com"], 7)

        call_args = mock_client.return_value.table.return_value.upsert.call_args[0][0]
        assert call_args["sync_type"] == "gmail"
        assert call_args["accounts"] == ["a@gmail.com"]
        assert call_args["days"] == 7


def test_set_defaults_uses_upsert_not_insert():
    mock_result = MagicMock()
    mock_result.data = [make_defaults_row()]

    with patch("app.services.defaults_service.get_client") as mock_client:
        mock_client.return_value.table.return_value \
            .upsert.return_value \
            .execute.return_value = mock_result

        set_defaults("gmail", ["a@gmail.com"], 7)
        set_defaults("gmail", ["b@gmail.com"], 14)

        assert mock_client.return_value.table.return_value.upsert.call_count == 2
        assert mock_client.return_value.table.return_value.insert.call_count == 0 \
            if hasattr(mock_client.return_value.table.return_value, 'insert') else True
