import secrets
import hashlib
import base64
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from datetime import datetime, timezone, timedelta
from typing import Optional
from app.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
from app.services.token_service import get_token, get_all_tokens, upsert_token

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

CLIENT_CONFIG = {
    "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uris": [GOOGLE_REDIRECT_URI],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

# Single-user: store code_verifier between auth URL generation and callback
_pending_code_verifier: Optional[str] = None


def _make_code_verifier() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(96)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge


def get_auth_url() -> str:
    global _pending_code_verifier
    verifier, challenge = _make_code_verifier()
    _pending_code_verifier = verifier

    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES)
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        code_challenge=challenge,
        code_challenge_method="S256",
    )
    return auth_url


def exchange_code(code: str) -> str:
    global _pending_code_verifier
    flow = Flow.from_client_config(CLIENT_CONFIG, scopes=SCOPES)
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    flow.fetch_token(code=code, code_verifier=_pending_code_verifier)
    _pending_code_verifier = None

    credentials = flow.credentials
    account_email = _get_account_email(credentials)

    expiry = credentials.expiry.replace(tzinfo=timezone.utc) if credentials.expiry else None
    upsert_token(
        provider="google",
        account_email=account_email,
        access_token=credentials.token,
        refresh_token=credentials.refresh_token,
        token_expiry=expiry,
    )
    return account_email


def get_credentials(account_email: str) -> Optional[Credentials]:
    token_row = get_token("google", account_email)
    if not token_row:
        return None

    expiry = None
    if token_row.get("token_expiry"):
        expiry = datetime.fromisoformat(
            token_row["token_expiry"].replace("Z", "+00:00")
        ).replace(tzinfo=None)  # Google auth library expects naive UTC

    creds = Credentials(
        token=token_row["access_token"],
        refresh_token=token_row["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
        expiry=expiry,
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        new_expiry = creds.expiry.replace(tzinfo=timezone.utc) if creds.expiry else None
        upsert_token(
            provider="google",
            account_email=account_email,
            access_token=creds.token,
            refresh_token=creds.refresh_token,
            token_expiry=new_expiry,
        )

    return creds


def fetch_events(account_email: str, days_ahead: int = 14) -> list[dict]:
    creds = get_credentials(account_email)
    if not creds:
        return []

    service = build("calendar", "v3", credentials=creds)
    now = datetime.now(timezone.utc)
    time_max = now + timedelta(days=days_ahead)

    result = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=time_max.isoformat(),
        singleEvents=True,
        orderBy="startTime",
        maxResults=100,
    ).execute()

    events = []
    for item in result.get("items", []):
        if "dateTime" not in item.get("start", {}):
            continue  # skip all-day events
        events.append(item)
    return events


def is_authenticated() -> bool:
    return len(get_all_tokens("google")) > 0


def _get_account_email(credentials: Credentials) -> str:
    service = build("oauth2", "v2", credentials=credentials)
    user_info = service.userinfo().get().execute()
    return user_info["email"]
