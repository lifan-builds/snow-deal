"""Email-only prelaunch signup; no delivery or implicit waitlist migration."""

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import re
import secrets

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from aggregator.auth_db import alert_signup_db as signup_db, _sync
from aggregator.web.rate_limit import SlidingWindowRateLimiter, client_key
from aggregator.web.seo import page_context

signup_router = APIRouter()
templates = Jinja2Templates(
    directory=str(Path(__file__).parent / "templates"),
    context_processors=[page_context],
)
signup_limiter = SlidingWindowRateLimiter(3600)
CONSENT_VERSION = "rare-deals-prelaunch-v1"


@signup_router.get("/alerts", response_class=HTMLResponse)
async def alerts(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="alerts.html",
        context={
            "page_title": "Rare Ski & Snowboard Deal Alerts — Coming Soon | FreshPowder",
            "page_description": "Join the email list for exceptional ski and snowboard deals. Alerts are coming soon. Free browsing, no account, no routine sale emails.",
        },
    )


@signup_router.post("/alerts/signup")
async def signup(request: Request, email: str = Form(...), website: str = Form("")):
    email = email.strip().lower()
    if website:
        return JSONResponse({"ok": True, "message": "Thanks for your interest."})
    if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return JSONResponse(
            {"ok": False, "error": "Please enter a valid email address."},
            status_code=422,
        )
    if not signup_limiter.allow(client_key(request, "alerts"), 10):
        return JSONResponse(
            {"ok": False, "error": "Please wait before trying again."}, status_code=429
        )
    token = secrets.token_urlsafe(32)
    try:
        conn = signup_db()
        # Never rotate an existing removal token on an unauthenticated repeat signup.
        conn.execute(
            "INSERT OR IGNORE INTO deal_alert_signups VALUES (?, ?, ?, ?)",
            (
                email,
                datetime.now(timezone.utc).isoformat(),
                CONSENT_VERSION,
                sha256(token.encode()).hexdigest(),
            ),
        )
        inserted = conn.execute("SELECT changes()").fetchone()[0] == 1
        conn.commit()
        _sync()
    except Exception:
        return JSONResponse(
            {"ok": False, "error": "We could not save your email. Please try again."},
            status_code=503,
        )
    message = "You’re on the list. Rare-deal alerts are coming soon; no emails are being sent yet."
    context = {
        "message": message,
        "removal_token": token if inserted else None,
        "noindex": True,
    }
    if request.headers.get("accept") == "application/json":
        response = JSONResponse({"ok": True, **context})
    else:
        response = templates.TemplateResponse(
            request=request, name="signup_result.html", context=context
        )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@signup_router.get("/alerts/remove", response_class=HTMLResponse)
async def removal_page(request: Request):
    response = templates.TemplateResponse(
        request=request, name="signup_remove.html", context={"noindex": True}
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@signup_router.post("/alerts/remove")
async def remove_signup(request: Request, token: str = Form(...)):
    if len(token) > 128:
        return JSONResponse({"ok": False}, status_code=422)
    conn = signup_db()
    conn.execute(
        "DELETE FROM deal_alert_signups WHERE removal_hash = ?",
        (sha256(token.encode()).hexdigest(),),
    )
    conn.commit()
    _sync()
    response = templates.TemplateResponse(
        request=request,
        name="signup_result.html",
        context={
            "message": "Your signup has been removed.",
            "noindex": True,
        },
    )
    response.headers["Cache-Control"] = "no-store"
    return response
