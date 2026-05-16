from pydantic import BaseModel, field_validator
from datetime import date as DateType, datetime
from typing import Optional
from app.config import BUCKETS, PRIORITY_MIN, PRIORITY_MAX


class TaskCreate(BaseModel):
    task: str
    date: DateType
    priority: float
    bucket: str
    reminders: Optional[datetime] = None

    @field_validator("priority")
    @classmethod
    def priority_in_range(cls, v):
        if v < PRIORITY_MIN or v > PRIORITY_MAX:
            raise ValueError(f"priority must be between {PRIORITY_MIN} and {PRIORITY_MAX}")
        return v

    @field_validator("bucket")
    @classmethod
    def bucket_valid(cls, v):
        if v not in BUCKETS:
            raise ValueError(f"bucket must be one of {BUCKETS}")
        return v


class TaskUpdate(BaseModel):
    task: Optional[str] = None
    date: Optional[DateType] = None
    priority: Optional[float] = None
    bucket: Optional[str] = None
    reminders: Optional[datetime] = None

    @field_validator("priority")
    @classmethod
    def priority_in_range(cls, v):
        if v is not None and (v < PRIORITY_MIN or v > PRIORITY_MAX):
            raise ValueError(f"priority must be between {PRIORITY_MIN} and {PRIORITY_MAX}")
        return v

    @field_validator("bucket")
    @classmethod
    def bucket_valid(cls, v):
        if v is not None and v not in BUCKETS:
            raise ValueError(f"bucket must be one of {BUCKETS}")
        return v


class Task(BaseModel):
    id: str
    user_id: Optional[str] = None
    task: str
    date: DateType
    priority: float
    bucket: str
    reminders: Optional[datetime] = None
    completed: bool
    created_at: datetime
