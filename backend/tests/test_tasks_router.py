import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.services.task_service import Task
from datetime import date, datetime

client = TestClient(app)

MOCK_TASK = Task(
    id="abc-123",
    task="Submit SIC report",
    date=date(2026, 5, 20),
    priority=7.5,
    bucket="SIC",
    completed=False,
    created_at=datetime(2026, 5, 15, 10, 0, 0),
)


def test_create_task_returns_201():
    with patch("app.routers.tasks.create_task", return_value=MOCK_TASK):
        response = client.post("/tasks", json={
            "task": "Submit SIC report",
            "date": "2026-05-20",
            "priority": 7.5,
            "bucket": "SIC",
        })
    assert response.status_code == 201
    assert response.json()["id"] == "abc-123"
    assert response.json()["task"] == "Submit SIC report"


def test_create_task_rejects_invalid_priority():
    response = client.post("/tasks", json={
        "task": "test",
        "date": "2026-05-20",
        "priority": 99.0,
        "bucket": "SIC",
    })
    assert response.status_code == 422


def test_create_task_rejects_invalid_bucket():
    response = client.post("/tasks", json={
        "task": "test",
        "date": "2026-05-20",
        "priority": 5.0,
        "bucket": "INVALID",
    })
    assert response.status_code == 422


def test_get_tasks_returns_list():
    with patch("app.routers.tasks.get_tasks", return_value=[MOCK_TASK]):
        response = client.get("/tasks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]["bucket"] == "SIC"


def test_get_tasks_filters_by_bucket():
    with patch("app.routers.tasks.get_tasks", return_value=[MOCK_TASK]) as mock:
        response = client.get("/tasks?bucket=SIC")
    assert response.status_code == 200
    mock.assert_called_once_with(bucket="SIC")


def test_update_task_returns_200():
    updated = MOCK_TASK.model_copy(update={"priority": 3.0})
    with patch("app.routers.tasks.update_task", return_value=updated):
        response = client.patch("/tasks/abc-123", json={"priority": 3.0})
    assert response.status_code == 200
    assert response.json()["priority"] == 3.0


def test_update_task_returns_404_for_unknown_id():
    with patch("app.routers.tasks.update_task", return_value=None):
        response = client.patch("/tasks/bad-id", json={"priority": 3.0})
    assert response.status_code == 404


def test_complete_task_returns_200():
    completed = MOCK_TASK.model_copy(update={"completed": True})
    with patch("app.routers.tasks.complete_task", return_value=completed):
        response = client.post("/tasks/abc-123/complete")
    assert response.status_code == 200
    assert response.json()["completed"] is True


def test_complete_task_returns_404_for_unknown_id():
    with patch("app.routers.tasks.complete_task", return_value=None):
        response = client.post("/tasks/bad-id/complete")
    assert response.status_code == 404


def test_delete_task_returns_204():
    with patch("app.routers.tasks.delete_task", return_value=True):
        response = client.delete("/tasks/abc-123")
    assert response.status_code == 204


def test_delete_task_returns_404_for_unknown_id():
    with patch("app.routers.tasks.delete_task", return_value=False):
        response = client.delete("/tasks/bad-id")
    assert response.status_code == 404


def test_create_task_triggers_reminder_event_when_reminders_set():
    task_with_reminder = MOCK_TASK.model_copy(update={"reminders": datetime(2026, 5, 20, 13, 0, 0)})
    with patch("app.routers.tasks.create_task", return_value=task_with_reminder), \
         patch("app.routers.tasks.create_reminder_event") as mock_reminder:
        client.post("/tasks", json={
            "task": "Submit SIC report",
            "date": "2026-05-20",
            "priority": 7.5,
            "bucket": "SIC",
            "reminders": "2026-05-20T13:00:00",
        })
    mock_reminder.assert_called_once()


def test_create_task_does_not_trigger_reminder_when_no_reminders():
    with patch("app.routers.tasks.create_task", return_value=MOCK_TASK), \
         patch("app.routers.tasks.create_reminder_event") as mock_reminder:
        client.post("/tasks", json={
            "task": "Submit SIC report",
            "date": "2026-05-20",
            "priority": 7.5,
            "bucket": "SIC",
        })
    mock_reminder.assert_not_called()


def test_create_task_succeeds_even_if_reminder_event_fails():
    task_with_reminder = MOCK_TASK.model_copy(update={"reminders": datetime(2026, 5, 20, 13, 0, 0)})
    with patch("app.routers.tasks.create_task", return_value=task_with_reminder), \
         patch("app.routers.tasks.create_reminder_event", side_effect=Exception("Calendar API down")):
        response = client.post("/tasks", json={
            "task": "Submit SIC report",
            "date": "2026-05-20",
            "priority": 7.5,
            "bucket": "SIC",
            "reminders": "2026-05-20T13:00:00",
        })
    assert response.status_code == 201
