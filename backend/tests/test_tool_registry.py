import pytest
from unittest.mock import patch, MagicMock
from datetime import date, datetime
from app.routers.chat import handle_tool_call, TOOLS
from app.services.task_service import Task

MOCK_TASK = Task(
    id="abc-123",
    task="Options meeting prep",
    date=date(2026, 5, 17),
    priority=9.0,
    bucket="Options",
    completed=False,
    created_at=datetime(2026, 5, 16, 10, 0, 0),
)


# --- Tool registry completeness ---

def test_all_five_tools_defined():
    names = {t["name"] for t in TOOLS}
    assert names == {"create_task", "get_tasks", "update_task", "complete_task", "delete_task"}


def test_each_tool_has_required_schema_fields():
    for tool in TOOLS:
        assert "name" in tool
        assert "description" in tool
        assert "input_schema" in tool


# --- Unknown tool ---

def test_unknown_tool_returns_error_string_not_exception():
    result = handle_tool_call("nonexistent_tool", {})
    assert "Unknown tool" in result
    assert "nonexistent_tool" in result


# --- complete_task ---

def test_handle_complete_task_returns_confirmation():
    completed = MOCK_TASK.model_copy(update={"completed": True})
    with patch("app.routers.chat.svc_complete_task", return_value=completed):
        result = handle_tool_call("complete_task", {"id": "abc-123"})
    assert "completed" in result.lower()
    assert "Options meeting prep" in result


def test_handle_complete_task_returns_not_found_for_missing_id():
    with patch("app.routers.chat.svc_complete_task", return_value=None):
        result = handle_tool_call("complete_task", {"id": "bad-id"})
    assert "not found" in result.lower()


# --- delete_task ---

def test_handle_delete_task_returns_confirmation():
    with patch("app.routers.chat.svc_delete_task", return_value=True):
        result = handle_tool_call("delete_task", {"id": "abc-123"})
    assert "deleted" in result.lower()


def test_handle_delete_task_returns_not_found_for_missing_id():
    with patch("app.routers.chat.svc_delete_task", return_value=False):
        result = handle_tool_call("delete_task", {"id": "bad-id"})
    assert "not found" in result.lower()


# --- update_task ---

def test_handle_update_task_returns_confirmation():
    updated = MOCK_TASK.model_copy(update={"priority": 3.0})
    with patch("app.routers.chat.svc_update_task", return_value=updated):
        result = handle_tool_call("update_task", {"id": "abc-123", "priority": 3.0})
    assert "updated" in result.lower()
    assert "Options meeting prep" in result


def test_handle_update_task_returns_not_found_for_missing_id():
    with patch("app.routers.chat.svc_update_task", return_value=None):
        result = handle_tool_call("update_task", {"id": "bad-id", "priority": 3.0})
    assert "not found" in result.lower()
