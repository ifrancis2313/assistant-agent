from fastapi import APIRouter, HTTPException, Query, Response
from typing import Optional
from app.services.task_service import TaskCreate, TaskUpdate, Task
from app.services.supabase_client import get_client

router = APIRouter(prefix="/tasks", tags=["tasks"])


def create_task(data: TaskCreate) -> Task:
    row = get_client().table("tasks").insert(
        data.model_dump(mode="json")
    ).execute()
    return Task(**row.data[0])


def get_tasks(bucket: Optional[str] = None) -> list[Task]:
    query = get_client().table("tasks").select("*").eq("completed", False).order("priority", desc=True)
    if bucket:
        query = query.eq("bucket", bucket)
    row = query.execute()
    return [Task(**r) for r in row.data]


def update_task(id: str, data: TaskUpdate) -> Optional[Task]:
    payload = {k: v for k, v in data.model_dump(mode="json").items() if v is not None}
    row = get_client().table("tasks").update(payload).eq("id", id).execute()
    if not row.data:
        return None
    return Task(**row.data[0])


def complete_task(id: str) -> Optional[Task]:
    row = get_client().table("tasks").update({"completed": True}).eq("id", id).execute()
    if not row.data:
        return None
    return Task(**row.data[0])


def delete_task(id: str) -> bool:
    row = get_client().table("tasks").delete().eq("id", id).execute()
    return len(row.data) > 0


def task_exists_for_external_id(source: str, external_id: str) -> bool:
    row = get_client().table("tasks") \
        .select("id") \
        .eq("source", source) \
        .eq("external_id", external_id) \
        .limit(1) \
        .execute()
    return len(row.data) > 0


@router.post("", status_code=201, response_model=Task)
def route_create_task(data: TaskCreate):
    return create_task(data)


@router.get("", response_model=list[Task])
def route_get_tasks(bucket: Optional[str] = Query(default=None)):
    return get_tasks(bucket=bucket)


@router.patch("/{id}", response_model=Task)
def route_update_task(id: str, data: TaskUpdate):
    result = update_task(id, data)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.post("/{id}/complete", response_model=Task)
def route_complete_task(id: str):
    result = complete_task(id)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.delete("/{id}", status_code=204)
def route_delete_task(id: str):
    if not delete_task(id):
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=204)
