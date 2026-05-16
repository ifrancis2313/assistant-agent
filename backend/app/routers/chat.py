import anthropic
from datetime import date
from fastapi import APIRouter
from pydantic import BaseModel
from app.config import ANTHROPIC_API_KEY, MODEL, BUCKETS
from app.services.message_service import fetch_window, persist_message
from app.services.task_service import TaskCreate, TaskUpdate
from app.routers.tasks import create_task, get_tasks
from app.routers.tasks import complete_task as svc_complete_task
from app.routers.tasks import delete_task as svc_delete_task
from app.routers.tasks import update_task as svc_update_task

router = APIRouter(tags=["chat"])

anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a personal AI assistant and planner. You help manage tasks and brainstorm ideas.

You have access to five tools:
- create_task: use when the user mentions a task, deadline, reminder, or anything they need to do
- get_tasks: use when the user asks about their schedule, priorities, or existing tasks
- complete_task: use when the user says a task is done or wants to mark it complete
- delete_task: use when the user wants to remove a task entirely
- update_task: use when the user wants to reschedule, reprioritize, or edit a task

When completing, deleting, or updating a task, first call get_tasks to find the correct task ID, then call the action tool with that ID.

Priority scale (0-10):
- 9-10: needs attention within hours, deadline today
- 7-8: deadline tonight or tomorrow
- 5-6: deadline in a few days
- 3-4: deadline this week
- 0-2: deadline weeks away, low importance

Buckets:
- SIC: Student Investment Club
- BC: Brother Connections
- School: academics, homework, classes
- Options: Options and Futures club
- Lab: Investment Lab / Silk analyst work
- Personal: everything else

For dates use yyyy-mm-dd format. For reminders use yyyy-mm-dd HH:MM.
When no deadline is given, make a reasonable estimate based on context.

IMPORTANT — Auto-assignment rules:
- ALWAYS assign bucket and priority yourself. Never ask the user to confirm or clarify a bucket or priority.
- Infer the bucket from context: mentions of investment club/SIC → SIC, brother connections/BC → BC, homework/class/exam → School, futures/options club → Options, investment lab/silk → Lab, everything else → Personal.
- If uncertain between two buckets, pick the most likely one and proceed. The user will correct if needed.
- For general questions or brainstorming, respond conversationally without using tools."""

TOOLS = [
    {
        "name": "create_task",
        "description": "Add a task to the planner",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Task description"},
                "date": {"type": "string", "description": "Due date (yyyy-mm-dd)"},
                "priority": {"type": "number", "description": "Priority 0.0-10.0"},
                "bucket": {"type": "string", "enum": BUCKETS, "description": "Category"},
                "reminders": {"type": "string", "description": "Reminder datetime (yyyy-mm-dd HH:MM), optional"},
            },
            "required": ["task", "date", "priority", "bucket"],
        },
    },
    {
        "name": "get_tasks",
        "description": "Retrieve tasks from the planner, optionally filtered by bucket",
        "input_schema": {
            "type": "object",
            "properties": {
                "bucket": {"type": "string", "enum": BUCKETS, "description": "Filter by bucket (optional)"},
            },
        },
    },
    {
        "name": "complete_task",
        "description": "Mark a task as complete",
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Task ID"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "delete_task",
        "description": "Delete a task permanently",
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Task ID"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "update_task",
        "description": "Update fields of an existing task (reschedule, reprioritize, rename, change bucket)",
        "input_schema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Task ID"},
                "task": {"type": "string", "description": "New task description"},
                "date": {"type": "string", "description": "New due date (yyyy-mm-dd)"},
                "priority": {"type": "number", "description": "New priority 0.0-10.0"},
                "bucket": {"type": "string", "enum": BUCKETS, "description": "New bucket"},
                "reminders": {"type": "string", "description": "New reminder (yyyy-mm-dd HH:MM)"},
            },
            "required": ["id"],
        },
    },
]


def handle_tool_call(name: str, inputs: dict) -> str:
    if name == "create_task":
        task = create_task(TaskCreate(**inputs))
        return f"Task created with task_id={task.id}: {task.task} (priority {task.priority}, due {task.date})"
    if name == "get_tasks":
        tasks = get_tasks(bucket=inputs.get("bucket"))
        if not tasks:
            return "No tasks found"
        return "\n".join(
            f"- task_id={t.id} | priority={t.priority} | due={t.date} | bucket={t.bucket} | name={t.task}" for t in tasks
        )
    if name == "complete_task":
        task = svc_complete_task(inputs["id"])
        if task is None:
            return "Task not found"
        return f"Task completed: {task.task}"
    if name == "delete_task":
        success = svc_delete_task(inputs["id"])
        if not success:
            return "Task not found"
        return "Task deleted successfully"
    if name == "update_task":
        task_id = inputs.get("id")
        if not task_id:
            return "Missing task ID"
        update_fields = {k: v for k, v in inputs.items() if k != "id"}
        task = svc_update_task(task_id, TaskUpdate.model_validate(update_fields))
        if task is None:
            return "Task not found"
        return f"Task updated: {task.task} (priority {task.priority}, due {task.date})"
    return f"Unknown tool: {name}"


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    history = fetch_window()
    persist_message("user", req.message)

    messages = history + [{"role": "user", "content": req.message}]

    while True:
        api_response = anthropic_client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=[
                {"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}},
                {"type": "text", "text": f"Today's date is {date.today().isoformat()}."},
            ],
            tools=TOOLS,
            messages=messages,
        )

        if api_response.stop_reason == "end_turn":
            text = next(b.text for b in api_response.content if b.type == "text")
            persist_message("assistant", text)
            return ChatResponse(response=text)

        tool_results = []
        for block in api_response.content:
            if block.type == "tool_use":
                result = handle_tool_call(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "assistant", "content": api_response.content})
        messages.append({"role": "user", "content": tool_results})
