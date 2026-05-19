import anthropic
from datetime import date
from fastapi import APIRouter
from pydantic import BaseModel
from app.config import ANTHROPIC_API_KEY, MODEL, BUCKETS
from app.services.message_service import fetch_window, persist_message
from app.services.task_service import TaskCreate, TaskUpdate
from app.routers.tasks import create_task, get_tasks, task_exists_for_external_id
from app.routers.tasks import complete_task as svc_complete_task
from app.routers.tasks import delete_task as svc_delete_task
from app.routers.tasks import update_task as svc_update_task
from app.services.google_calendar_service import fetch_events, get_all_tokens as gcal_get_all_tokens
from app.services.canvas_service import fetch_unsubmitted_assignments
from app.services.token_service import upsert_token, get_all_tokens
from app.services.defaults_service import get_defaults, set_defaults
from app.services.gmail_service import fetch_emails

router = APIRouter(tags=["chat"])

anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a personal AI assistant and planner. You help manage tasks and brainstorm ideas.

You have access to eleven tools:
- create_task: use when the user mentions a task, deadline, reminder, or anything they need to do
- get_tasks: use when the user asks about their schedule, priorities, or existing tasks
- complete_task: use when the user says a task is done or wants to mark it complete
- delete_task: use when the user wants to remove a task entirely
- update_task: use when the user wants to reschedule, reprioritize, or edit a task
- sync_google_calendar: import calendar events. Accepts optional accounts (list of emails) and days_ahead. Falls back to stored defaults, then all connected accounts / 14 days.
- sync_canvas: import Canvas assignments. Accepts optional accounts parameter.
- set_canvas_token: use when the user provides a Canvas API token.
- sync_gmail: import actionable emails as tasks. Accepts optional accounts (list of emails) and days. Falls back to stored defaults, then all connected accounts / 7 days. Use when user says "check my email", "sync my email", or similar.
- set_defaults: store default sync preferences. Use when user says "set my default email accounts to..." or "make X my default calendar". Accepts sync_type (gmail/google_calendar/canvas), accounts (list), days.
- list_connected_accounts: show which Google accounts are connected. Use when user asks about connected accounts.

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
    {
        "name": "sync_google_calendar",
        "description": "Import upcoming Google Calendar events as tasks",
        "input_schema": {
            "type": "object",
            "properties": {
                "accounts": {"type": "array", "items": {"type": "string"}, "description": "Email addresses to sync (optional, uses defaults if omitted)"},
                "days_ahead": {"type": "integer", "description": "Days ahead to sync (optional, uses defaults if omitted)"},
            },
        },
    },
    {
        "name": "sync_canvas",
        "description": "Import unsubmitted Canvas assignments as tasks",
        "input_schema": {
            "type": "object",
            "properties": {
                "accounts": {"type": "array", "items": {"type": "string"}, "description": "Canvas accounts to sync (optional)"},
            },
        },
    },
    {
        "name": "set_canvas_token",
        "description": "Store a Canvas API token to connect Canvas",
        "input_schema": {
            "type": "object",
            "properties": {
                "token": {"type": "string", "description": "Canvas personal access token"},
            },
            "required": ["token"],
        },
    },
    {
        "name": "sync_gmail",
        "description": "Import actionable emails as tasks from Gmail",
        "input_schema": {
            "type": "object",
            "properties": {
                "accounts": {"type": "array", "items": {"type": "string"}, "description": "Gmail addresses to sync (optional, uses defaults if omitted)"},
                "days": {"type": "integer", "description": "Days back to look for emails (optional, uses defaults if omitted)"},
            },
        },
    },
    {
        "name": "set_defaults",
        "description": "Store default sync preferences for a sync type",
        "input_schema": {
            "type": "object",
            "properties": {
                "sync_type": {"type": "string", "enum": ["gmail", "google_calendar", "canvas"], "description": "Which sync to set defaults for"},
                "accounts": {"type": "array", "items": {"type": "string"}, "description": "Default email accounts"},
                "days": {"type": "integer", "description": "Default day window"},
            },
            "required": ["sync_type"],
        },
    },
    {
        "name": "list_connected_accounts",
        "description": "List all connected Google accounts",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def _resolve_accounts_and_days(inputs: dict, sync_type: str, default_days: int) -> tuple[list[str], int]:
    accounts = inputs.get("accounts")
    days = inputs.get("days") or inputs.get("days_ahead")
    if not accounts or not days:
        stored = get_defaults(sync_type)
        if stored:
            accounts = accounts or stored.get("accounts")
            days = days or stored.get("days")
    if not accounts:
        accounts = [t["account_email"] for t in get_all_tokens("google")]
    if not days:
        days = default_days
    return accounts, days


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
    if name == "sync_google_calendar":
        accounts, days = _resolve_accounts_and_days(inputs, "google_calendar", 14)
        return _handle_sync_google_calendar(accounts, days)
    if name == "sync_canvas":
        return _handle_sync_canvas()
    if name == "set_canvas_token":
        upsert_token("canvas", "canvas", inputs["token"])
        return "Canvas token saved. You can now sync your Canvas assignments."
    if name == "sync_gmail":
        accounts, days = _resolve_accounts_and_days(inputs, "gmail", 7)
        return _handle_sync_gmail(accounts, days)
    if name == "set_defaults":
        accounts = inputs.get("accounts", [])
        days = inputs.get("days", 7)
        set_defaults(inputs["sync_type"], accounts, days)
        return f"Defaults saved for {inputs['sync_type']}: accounts={accounts}, days={days}"
    if name == "list_connected_accounts":
        tokens = get_all_tokens("google")
        if not tokens:
            return "No Google accounts connected."
        return "Connected accounts:\n" + "\n".join(f"- {t['account_email']}" for t in tokens)
    return f"Unknown tool: {name}"


def _handle_sync_google_calendar(accounts: list[str], days_ahead: int) -> str:
    if not accounts:
        return "No Google accounts connected. Visit /auth/google to connect your calendar."

    imported, skipped = 0, 0
    for account_email in accounts:
        events = fetch_events(account_email, days_ahead=days_ahead)
        for event in events:
            external_id = event["id"]
            if task_exists_for_external_id("google_calendar", external_id):
                skipped += 1
                continue
            summary = event.get("summary", "Untitled event")
            start_dt = event["start"]["dateTime"]
            event_date = start_dt[:10]
            create_task(TaskCreate(
                task=summary,
                date=event_date,
                priority=5.0,
                bucket="Personal",
                source="google_calendar",
                external_id=external_id,
            ))
            imported += 1

    if imported == 0:
        return f"No new events in the next {days_ahead} days across {len(accounts)} account(s). {skipped} already imported."
    return f"Imported {imported} new event(s) from {len(accounts)} Google account(s). {skipped} already existed."


def _handle_sync_canvas() -> str:
    assignments = fetch_unsubmitted_assignments()
    if assignments is None:
        return "Canvas is not connected. Provide your Canvas token with: set my Canvas token to <token>"
    if not assignments:
        return "No unsubmitted Canvas assignments found."

    imported, skipped = 0, 0
    for assignment in assignments:
        external_id = str(assignment["id"])
        if task_exists_for_external_id("canvas", external_id):
            skipped += 1
            continue
        due_date = assignment["due_at"][:10] if assignment.get("due_at") else str(date.today())
        task_name = f"{assignment['name']} — {assignment['course_name']}"
        create_task(TaskCreate(
            task=task_name,
            date=due_date,
            priority=5.0,
            bucket="School",
            source="canvas",
            external_id=external_id,
        ))
        imported += 1

    if imported == 0:
        return f"No new assignments found. {skipped} already imported."
    return f"Imported {imported} Canvas assignment(s). {skipped} already existed."


def _handle_sync_gmail(accounts: list[str], days: int) -> str:
    if not accounts:
        return "No Gmail accounts available. Visit /auth/google to connect."

    all_emails = []
    for account_email in accounts:
        emails = fetch_emails(account_email, days=days, limit=25)
        for email in emails:
            if not task_exists_for_external_id("gmail", email["id"]):
                all_emails.append(email)

    if not all_emails:
        return f"No new emails found in the last {days} day(s) across {len(accounts)} account(s)."

    formatted = "\n".join(
        f"- email_id={e['id']} | from={e['from']} | subject={e['subject']} | snippet={e['snippet']}"
        for e in all_emails
    )
    return (
        f"Found {len(all_emails)} email(s) from the last {days} day(s). "
        f"Review each and call create_task for any that require action "
        f"(use source='gmail' and external_id=<email_id>):\n{formatted}"
    )


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
