import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)


def mock_anthropic_text_response(text: str):
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [block]
    return response


def test_chat_returns_response():
    with patch("app.routers.chat.fetch_window", return_value=[]), \
         patch("app.routers.chat.persist_message"), \
         patch("app.routers.chat.anthropic_client") as mock_client:

        mock_client.messages.create.return_value = mock_anthropic_text_response("Hello!")

        response = client.post("/chat", json={"message": "hi"})

    assert response.status_code == 200
    assert response.json()["response"] == "Hello!"


def test_chat_persists_user_and_assistant_messages():
    with patch("app.routers.chat.fetch_window", return_value=[]) as _, \
         patch("app.routers.chat.persist_message") as mock_persist, \
         patch("app.routers.chat.anthropic_client") as mock_client:

        mock_client.messages.create.return_value = mock_anthropic_text_response("Got it.")

        client.post("/chat", json={"message": "add a task"})

    calls = [(c.args[0], c.args[1]) for c in mock_persist.call_args_list]
    assert ("user", "add a task") in calls
    assert ("assistant", "Got it.") in calls


def test_chat_includes_history_in_request():
    history = [{"role": "user", "content": "previous"}, {"role": "assistant", "content": "reply"}]

    with patch("app.routers.chat.fetch_window", return_value=history), \
         patch("app.routers.chat.persist_message"), \
         patch("app.routers.chat.anthropic_client") as mock_client:

        mock_client.messages.create.return_value = mock_anthropic_text_response("ok")
        client.post("/chat", json={"message": "new message"})

    call_kwargs = mock_client.messages.create.call_args
    messages_sent = call_kwargs.kwargs["messages"]
    assert messages_sent[0] == {"role": "user", "content": "previous"}
    assert messages_sent[1] == {"role": "assistant", "content": "reply"}
    assert messages_sent[-1]["content"] == "new message"


def test_chat_executes_create_task_tool():
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.name = "create_task"
    tool_block.id = "tool_1"
    tool_block.input = {
        "task": "SIC report",
        "date": "2026-05-20",
        "priority": 7.5,
        "bucket": "SIC"
    }

    tool_response = MagicMock()
    tool_response.stop_reason = "tool_use"
    tool_response.content = [tool_block]

    final_response = mock_anthropic_text_response("Task created!")

    with patch("app.routers.chat.fetch_window", return_value=[]), \
         patch("app.routers.chat.persist_message"), \
         patch("app.routers.chat.anthropic_client") as mock_client, \
         patch("app.routers.chat.handle_tool_call", return_value="created") as mock_tool:

        mock_client.messages.create.side_effect = [tool_response, final_response]
        response = client.post("/chat", json={"message": "add SIC report due May 20"})

    assert response.status_code == 200
    mock_tool.assert_called_once_with("create_task", tool_block.input)


def test_chat_missing_message_returns_422():
    response = client.post("/chat", json={})
    assert response.status_code == 422
