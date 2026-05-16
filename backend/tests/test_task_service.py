import pytest
from datetime import date
from pydantic import ValidationError
from app.services.task_service import TaskCreate, TaskUpdate, Task


# --- Validation tests (no DB needed) ---

def test_create_task_rejects_priority_above_max():
    with pytest.raises(ValidationError):
        TaskCreate(task="test", date=date.today(), priority=11.0, bucket="SIC")


def test_create_task_rejects_priority_below_min():
    with pytest.raises(ValidationError):
        TaskCreate(task="test", date=date.today(), priority=-1.0, bucket="SIC")


def test_create_task_rejects_invalid_bucket():
    with pytest.raises(ValidationError):
        TaskCreate(task="test", date=date.today(), priority=5.0, bucket="INVALID")


def test_create_task_accepts_valid_data():
    t = TaskCreate(task="Submit SIC report", date=date(2026, 5, 20), priority=7.5, bucket="SIC")
    assert t.task == "Submit SIC report"
    assert t.priority == 7.5
    assert t.bucket == "SIC"


def test_update_task_rejects_invalid_priority():
    with pytest.raises(ValidationError):
        TaskUpdate(priority=15.0)


def test_update_task_rejects_invalid_bucket():
    with pytest.raises(ValidationError):
        TaskUpdate(bucket="FAKE")


def test_update_task_allows_partial_fields():
    u = TaskUpdate(priority=3.0)
    assert u.priority == 3.0
    assert u.task is None
    assert u.bucket is None
