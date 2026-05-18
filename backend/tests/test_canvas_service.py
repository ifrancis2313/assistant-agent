import pytest
from unittest.mock import patch, MagicMock


def make_todo_item(assignment_id=1, name="Essay", due_at="2026-05-20T23:59:00Z",
                   course_name="ECON 101", submitted=False):
    return {
        "type": "submitting",
        "context_name": course_name,
        "assignment": {
            "id": assignment_id,
            "name": name,
            "due_at": due_at,
            "submission": {"workflow_state": "submitted" if submitted else "unsubmitted"},
        }
    }


def test_fetch_unsubmitted_returns_unsubmitted_only():
    from app.services.canvas_service import fetch_unsubmitted_assignments

    items = [
        make_todo_item(1, "Essay", submitted=False),
        make_todo_item(2, "Quiz", submitted=True),
        make_todo_item(3, "Lab Report", submitted=False),
    ]
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = items

    with patch("app.services.canvas_service.httpx.get", return_value=mock_resp), \
         patch("app.services.canvas_service.get_token", return_value={"access_token": "tok"}):
        result = fetch_unsubmitted_assignments()

    assert len(result) == 2
    assert result[0]["name"] == "Essay"
    assert result[1]["name"] == "Lab Report"


def test_fetch_unsubmitted_includes_correct_fields():
    from app.services.canvas_service import fetch_unsubmitted_assignments

    items = [make_todo_item(99, "Final Paper", "2026-06-01T23:59:00Z", "CS 101")]
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = items

    with patch("app.services.canvas_service.httpx.get", return_value=mock_resp), \
         patch("app.services.canvas_service.get_token", return_value={"access_token": "tok"}):
        result = fetch_unsubmitted_assignments()

    assert result[0]["id"] == 99
    assert result[0]["name"] == "Final Paper"
    assert result[0]["due_at"] == "2026-06-01T23:59:00Z"
    assert result[0]["course_name"] == "CS 101"


def test_fetch_unsubmitted_returns_empty_when_no_token():
    from app.services.canvas_service import fetch_unsubmitted_assignments

    with patch("app.services.canvas_service.get_token", return_value=None):
        result = fetch_unsubmitted_assignments()

    assert result == []


def test_fetch_unsubmitted_returns_empty_when_all_submitted():
    from app.services.canvas_service import fetch_unsubmitted_assignments

    items = [make_todo_item(1, submitted=True), make_todo_item(2, submitted=True)]
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = items

    with patch("app.services.canvas_service.httpx.get", return_value=mock_resp), \
         patch("app.services.canvas_service.get_token", return_value={"access_token": "tok"}):
        result = fetch_unsubmitted_assignments()

    assert result == []
