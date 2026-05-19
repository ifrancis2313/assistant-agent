from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
from app.services.google_calendar_service import get_credentials


def fetch_emails(account_email: str, days: int = 7, limit: int = 25) -> list[dict]:
    creds = get_credentials(account_email)
    if not creds:
        return []

    service = build("gmail", "v1", credentials=creds)
    after = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
    query = f"is:unread after:{after}"

    response = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=limit,
    ).execute()

    message_refs = response.get("messages", [])
    if not message_refs:
        return []

    emails = []
    for ref in message_refs[:limit]:
        msg = service.users().messages().get(
            userId="me",
            id=ref["id"],
            format="metadata",
            metadataHeaders=["From", "Subject"],
        ).execute()

        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        emails.append({
            "id": msg["id"],
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", "(no subject)"),
            "snippet": msg.get("snippet", ""),
        })

    return emails
