from typing import Optional
from app.services.supabase_client import get_client


def get_defaults(sync_type: str) -> Optional[dict]:
    result = (
        get_client()
        .table("user_defaults")
        .select("sync_type,accounts,days")
        .eq("sync_type", sync_type)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def set_defaults(sync_type: str, accounts: list[str], days: int) -> None:
    get_client().table("user_defaults").upsert(
        {
            "sync_type": sync_type,
            "accounts": accounts,
            "days": days,
        },
        on_conflict="sync_type",
    ).execute()
