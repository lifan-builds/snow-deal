"""Event tracking routes — lightweight analytics."""

from __future__ import annotations

from pathlib import Path
import json
import re
import secrets
from urllib.parse import urlsplit, urlunsplit

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from aggregator.auth import auth_redirect_path, require_invite
from aggregator.auth_db import log_event, get_click_stats
from aggregator.web.rate_limit import SlidingWindowRateLimiter, client_key

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

event_router = APIRouter()
EVENT_POST_LIMIT = 120
EVENT_POST_WINDOW_SECONDS = 60
event_post_limiter = SlidingWindowRateLimiter(window_seconds=EVENT_POST_WINDOW_SECONDS)


ANALYTICS_COOKIE = "fp_analytics"
SOURCES = {"direct", "google", "bing", "x", "portfolio", "club", "youtube", "reddit", "other"}
PUBLIC_PAGE = re.compile(r"^/(?:products(?:/[a-z0-9-]+)?|brands/[a-z0-9-]+|gear/[a-z0-9-]+|guides(?:/[a-z0-9-]+)?|how-it-works|about|status|alerts|privacy)?$")


class EventPayload(BaseModel):
    event_type: str = Field(max_length=20)
    deal_url: str | None = Field(default=None, max_length=2048)
    deal_name: str | None = Field(default=None, max_length=300)
    store: str | None = Field(default=None, max_length=100)
    category: str | None = Field(default=None, max_length=50)
    metadata: str | None = Field(default=None, max_length=1000)


def safe_metadata(raw: str | None) -> str:
    """Store only bounded shopping context, never raw queries or referrers."""
    try:
        data = json.loads(raw or "{}")
    except (ValueError, TypeError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    clean = {"version": 2}
    if isinstance(data.get("page"), str) and PUBLIC_PAGE.fullmatch(data["page"]):
        clean["page"] = data["page"]
    if isinstance(data.get("source"), str) and data["source"] in SOURCES:
        clean["source"] = data["source"]
    if isinstance(data.get("campaign"), str) and data["campaign"] in {"2026_winter", "2026_launch", "club_pilot"}:
        clean["campaign"] = data["campaign"]
    if isinstance(data.get("currency"), str) and data["currency"] in {"USD", "CAD"}:
        clean["currency"] = data["currency"]
    if isinstance(data.get("size"), str) and re.fullmatch(r"(?:1\d{2}|2[01]\d|220)W?", data["size"]):
        clean["size"] = data["size"]
    return json.dumps(clean, sort_keys=True)


@event_router.post("/api/event")
async def track_event(request: Request, payload: EventPayload):
    """Anonymous, short-session telemetry; auth cookies are never persisted."""
    if payload.event_type not in {"click", "page_view", "filter", "search"}:
        return JSONResponse({"ok": False}, status_code=400)
    origin = request.headers.get("origin")
    if origin and origin != str(request.base_url).rstrip("/"):
        return JSONResponse({"ok": False}, status_code=403)
    if not event_post_limiter.allow(client_key(request, "event-post"), EVENT_POST_LIMIT):
        return JSONResponse({"ok": False, "error": "rate_limited"}, status_code=429)
    if (request.headers.get("dnt") == "1" or request.headers.get("sec-gpc") == "1"
            or request.cookies.get("admin_key")):
        return JSONResponse({"ok": True, "recorded": False})
    url = None
    if payload.deal_url:
        try:
            parsed = urlsplit(payload.deal_url)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
                return JSONResponse({"ok": False}, status_code=400)
            url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
        except ValueError:
            return JSONResponse({"ok": False}, status_code=400)
    token = request.cookies.get(ANALYTICS_COOKIE, "")
    if not re.fullmatch(r"[a-f0-9]{32}", token):
        token = secrets.token_hex(16)
    await log_event(
        event_type=payload.event_type, session="anon:" + token,
        deal_url=url, deal_name=payload.deal_name, store=payload.store,
        category=payload.category, metadata=safe_metadata(payload.metadata),
    )
    response = JSONResponse({"ok": True})
    response.headers["Cache-Control"] = "no-store"
    response.set_cookie(ANALYTICS_COOKIE, token, max_age=1800, httponly=True,
                        secure=request.url.scheme == "https", samesite="lax")
    return response


@event_router.get("/admin/stats", response_class=HTMLResponse)
async def admin_stats_page(request: Request, days: int = Query(7, ge=1, le=90)):
    """Admin dashboard showing user analytics."""
    session = await require_invite(request)
    if session != "admin":
        return RedirectResponse(url=auth_redirect_path(), status_code=302)

    stats = await get_click_stats(days=days)
    return templates.TemplateResponse(
        request=request, name="admin_stats.html", context={"stats": stats},
    )
