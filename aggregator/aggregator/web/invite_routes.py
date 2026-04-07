"""Invite code entry routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from aggregator.auth import (
    SESSION_COOKIE,
    create_session_token,
    is_public_mode,
)
from aggregator.auth_db import validate_invite_code, record_code_use, add_to_waitlist
from aggregator.config import STORES
from aggregator.db import query_deals
from aggregator.web.rate_limit import SlidingWindowRateLimiter, client_key

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

invite_router = APIRouter()
INVITE_SUBMIT_LIMIT = 10
INVITE_WINDOW_SECONDS = 300
invite_submit_limiter = SlidingWindowRateLimiter(window_seconds=INVITE_WINDOW_SECONDS)


async def _landing_context(error: str | None = None) -> dict:
    try:
        deal_count = await query_deals(count_only=True)
    except Exception:
        deal_count = 0
    # Fetch a handful of top deals for the preview cards
    try:
        sample_deals = await query_deals(
            min_discount=25, min_price=100, sort_by="discount_pct", limit=6,
        )
    except Exception:
        sample_deals = []
    return {
        "error": error,
        "deal_count": deal_count or 0,
        "store_count": len(STORES),
        "sample_deals": sample_deals,
    }


@invite_router.get("/invite", response_class=HTMLResponse)
async def invite_page(request: Request):
    if is_public_mode():
        return RedirectResponse(url="/", status_code=302)
    ctx = await _landing_context()
    return templates.TemplateResponse(
        request=request, name="invite.html", context=ctx,
    )


@invite_router.post("/invite", response_class=HTMLResponse)
async def invite_submit(request: Request, code: str = Form(...)):
    if is_public_mode():
        return RedirectResponse(url="/", status_code=302)
    if not invite_submit_limiter.allow(
        client_key(request, "invite-submit"), INVITE_SUBMIT_LIMIT
    ):
        ctx = await _landing_context(error="Too many invite attempts. Please wait a few minutes and try again.")
        return templates.TemplateResponse(
            request=request, name="invite.html", context=ctx, status_code=429,
        )
    code = code.strip().upper()
    valid = await validate_invite_code(code)
    if not valid:
        ctx = await _landing_context(error="Invalid or exhausted invite code.")
        return templates.TemplateResponse(
            request=request, name="invite.html", context=ctx,
        )
    # Record the use for tracking, then issue a JWT
    await record_code_use(code)
    token = create_session_token(code)
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(SESSION_COOKIE, token, httponly=True, max_age=86400 * 365)
    return response


@invite_router.post("/waitlist")
async def waitlist_submit(request: Request, email: str = Form(...)):
    """Add an email to the waitlist."""
    from fastapi.responses import JSONResponse
    try:
        await add_to_waitlist(email)
    except Exception:
        pass  # silently swallow DB errors — UX shows success regardless
    return JSONResponse({"ok": True})
