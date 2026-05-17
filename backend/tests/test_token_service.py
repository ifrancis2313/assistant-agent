import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from app.services.token_service import get_token, get_all_tokens, upsert_token


def make_token_row(provider="google", account_email="test@gmail.com", access_token="access123"):
    return {
        "id": "abc-123",
        "provider": provider,
        "account_email": account_email,
        "access_token": access_token,
        "refresh_token": "refresh123",
        "token_expiry": "2026-05-17T10:00:00Z",
        "created_at": "2026-05-16T10:00:00Z",
        "updated_at": "2026-05-16T10:00:00Z",
    }


def test_get_token_returns_token_when_exists():
    mock_result = MagicMock()
    mock_result.data = [make_token_row()]

    with patch("app.services.token_service.get_client") as mock_client:
        mock_client.return_value.table.return_value \
            .select.return_value \
            .eq.return_value \
            .eq.return_value \
            .limit.return_value \
            .execute.return_value = mock_result

        result = get_token("google", "test@gmail.com")

    assert result is not None
    assert result["access_token"] == "access123"
    assert result["account_email"] == "test@gmail.com"


def test_get_token_returns_none_when_not_found():
    mock_result = MagicMock()
    mock_result.data = []

    with patch("app.services.token_service.get_client") as mock_client:
        mock_client.return_value.table.return_value \
            .select.return_value \
            .eq.return_value \
            .eq.return_value \
            .limit.return_value \
            .execute.return_value = mock_result

        result = get_token("google", "nobody@gmail.com")

    assert result is None


def test_get_all_tokens_returns_all_for_provider():
    rows = [
        make_token_row(account_email="personal@gmail.com"),
        make_token_row(account_email="school@usfca.edu"),
    ]
    mock_result = MagicMock()
    mock_result.data = rows

    with patch("app.services.token_service.get_client") as mock_client:
        mock_client.return_value.table.return_value \
            .select.return_value \
            .eq.return_value \
            .execute.return_value = mock_result

        result = get_all_tokens("google")

    assert len(result) == 2
    assert result[0]["account_email"] == "personal@gmail.com"
    assert result[1]["account_email"] == "school@usfca.edu"


def test_get_all_tokens_returns_empty_list_when_none():
    mock_result = MagicMock()
    mock_result.data = []

    with patch("app.services.token_service.get_client") as mock_client:
        mock_client.return_value.table.return_value \
            .select.return_value \
            .eq.return_value \
            .execute.return_value = mock_result

        result = get_all_tokens("google")

    assert result == []


def test_upsert_token_calls_supabase_upsert():
    mock_result = MagicMock()
    mock_result.data = [make_token_row()]

    with patch("app.services.token_service.get_client") as mock_client:
        mock_upsert = mock_client.return_value.table.return_value.upsert.return_value
        mock_upsert.execute.return_value = mock_result

        upsert_token("google", "test@gmail.com", "new_access", "new_refresh")

        mock_client.return_value.table.return_value.upsert.assert_called_once()
        call_args = mock_client.return_value.table.return_value.upsert.call_args[0][0]
        assert call_args["provider"] == "google"
        assert call_args["account_email"] == "test@gmail.com"
        assert call_args["access_token"] == "new_access"
        assert call_args["refresh_token"] == "new_refresh"


def test_upsert_token_works_without_refresh_token():
    mock_result = MagicMock()
    mock_result.data = [make_token_row()]

    with patch("app.services.token_service.get_client") as mock_client:
        mock_client.return_value.table.return_value \
            .upsert.return_value \
            .execute.return_value = mock_result

        upsert_token("canvas", "canvas", "canvas_api_token")

        call_args = mock_client.return_value.table.return_value.upsert.call_args[0][0]
        assert call_args["refresh_token"] is None
        assert call_args["token_expiry"] is None
