import httpx
from app.services.token_service import get_token

CANVAS_BASE_URL = "https://usfca.instructure.com/api/v1"


def fetch_unsubmitted_assignments() -> list[dict]:
    token_row = get_token("canvas", "canvas")
    if not token_row:
        return []

    headers = {"Authorization": f"Bearer {token_row['access_token']}"}
    response = httpx.get(
        f"{CANVAS_BASE_URL}/users/self/todo",
        headers=headers,
        params={"per_page": 100},
    )

    assignments = []
    for item in response.json():
        assignment = item.get("assignment", {})
        if not assignment:
            continue
        submission = assignment.get("submission", {}) or {}
        if submission.get("workflow_state") == "submitted":
            continue
        assignments.append({
            "id": assignment["id"],
            "name": assignment["name"],
            "due_at": assignment.get("due_at"),
            "course_name": item.get("context_name", "Unknown Course"),
        })

    return assignments
