from fastapi import APIRouter
from fastapi.responses import RedirectResponse, HTMLResponse
from app.services.google_calendar_service import get_auth_url, exchange_code

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google")
def google_auth():
    return RedirectResponse(url=get_auth_url())


@router.get("/google/callback")
def google_callback(code: str):
    account_email = exchange_code(code)
    return HTMLResponse(content=f"""
    <html><body style="font-family:sans-serif;padding:40px;text-align:center">
        <h2>Connected</h2>
        <p>Google Calendar authorized for <strong>{account_email}</strong></p>
        <p>You can close this tab and return to the app.</p>
        <p>To connect another account, visit <a href="/auth/google">/auth/google</a> again.</p>
    </body></html>
    """)
