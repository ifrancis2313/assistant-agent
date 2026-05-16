import pytest
from unittest.mock import patch, MagicMock
from app.services.message_service import persist_message, fetch_window


def make_db_messages(n: int) -> list[dict]:
    return [
        {"id": str(i), "role": "user" if i % 2 == 0 else "assistant",
         "content": f"message {i}", "created_at": f"2026-05-16T0{i}:00:00Z"}
        for i in range(n)
    ]


def test_fetch_window_returns_last_n_in_order():
    db_rows = make_db_messages(30)
    mock_execute = MagicMock()
    mock_execute.data = db_rows[-20:]

    with patch("app.services.message_service.get_client") as mock_client:
        mock_client.return_value.table.return_value \
            .select.return_value \
            .order.return_value \
            .limit.return_value \
            .execute.return_value = mock_execute

        result = fetch_window(n=20)

    assert len(result) == 20
    assert result[0]["content"] == "message 10"
    assert result[-1]["content"] == "message 29"


def test_fetch_window_respects_n():
    db_rows = make_db_messages(5)
    mock_execute = MagicMock()
    mock_execute.data = db_rows

    with patch("app.services.message_service.get_client") as mock_client:
        mock_client.return_value.table.return_value \
            .select.return_value \
            .order.return_value \
            .limit.return_value \
            .execute.return_value = mock_execute

        result = fetch_window(n=5)

    assert len(result) == 5


def test_fetch_window_returns_role_and_content_only():
    db_rows = [{"id": "1", "role": "user", "content": "hello", "created_at": "2026-05-16T00:00:00Z"}]
    mock_execute = MagicMock()
    mock_execute.data = db_rows

    with patch("app.services.message_service.get_client") as mock_client:
        mock_client.return_value.table.return_value \
            .select.return_value \
            .order.return_value \
            .limit.return_value \
            .execute.return_value = mock_execute

        result = fetch_window(n=20)

    assert result[0] == {"role": "user", "content": "hello"}
    assert "id" not in result[0]
    assert "created_at" not in result[0]


def test_persist_message_inserts_correct_fields():
    mock_execute = MagicMock()
    mock_execute.data = [{"id": "abc", "role": "user", "content": "hi", "created_at": "now"}]

    with patch("app.services.message_service.get_client") as mock_client:
        mock_insert = mock_client.return_value.table.return_value.insert.return_value
        mock_insert.execute.return_value = mock_execute

        persist_message("user", "hi")

        mock_client.return_value.table.return_value.insert.assert_called_once_with(
            {"role": "user", "content": "hi"}
        )


def test_persist_message_accepts_both_roles():
    mock_execute = MagicMock()
    mock_execute.data = [{}]

    with patch("app.services.message_service.get_client") as mock_client:
        mock_client.return_value.table.return_value \
            .insert.return_value \
            .execute.return_value = mock_execute

        persist_message("user", "hello")
        persist_message("assistant", "hi there")

    assert mock_client.return_value.table.return_value.insert.call_count == 2
