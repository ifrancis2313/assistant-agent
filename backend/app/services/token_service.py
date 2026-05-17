from typing import Optional
from datetime import datetime
from app.services.supabase_client import get_client


def get_token(provider: str, account_email: str) -> Optional[dict]:
    result = (
        get_client()
        .table("user_tokens")
        .select("*")
        .eq("provider", provider)
        .eq("account_email", account_email)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def get_all_tokens(provider: str) -> list[dict]:
    result = (
        get_client()
        .table("user_tokens")
        .select("*")
        .eq("provider", provider)
        .execute()
    )
    return result.data


def upsert_token(
    provider: str,
    account_email: str,
    access_token: str,
    refresh_token: Optional[str] = None,
    token_expiry: Optional[datetime] = None,
) -> None:
    get_client().table("user_tokens").upsert(
        {
            "provider": provider,
            "account_email": account_email,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_expiry": token_expiry.isoformat() if token_expiry else None,
            "updated_at": datetime.utcnow().isoformat(),
        },
        on_conflict="provider,account_email",
    ).execute()
