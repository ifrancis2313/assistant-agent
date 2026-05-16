from app.services.supabase_client import get_client
from app.config import MESSAGE_WINDOW


def persist_message(role: str, content: str) -> None:
    get_client().table("messages").insert({"role": role, "content": content}).execute()


def fetch_window(n: int = MESSAGE_WINDOW) -> list[dict]:
    rows = (
        get_client()
        .table("messages")
        .select("role,content,created_at")
        .order("created_at", desc=False)
        .limit(n)
        .execute()
    )
    return [{"role": r["role"], "content": r["content"]} for r in rows.data]
