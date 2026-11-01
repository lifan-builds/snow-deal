"""FastAPI application factory."""

from __future__ import annotations

import logging
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from starlette.exceptions import HTTPException
from aggregator.web.seo import page_context
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import aggregator.auth as auth
from aggregator.auth import auth_middleware
from aggregator.config import env_flag
from aggregator.db import ensure_deals_db_ready, init_db
from aggregator.auth_db import init_auth_db
from aggregator.web.routes import router
from aggregator.web.invite_routes import invite_router
from aggregator.web.admin_routes import admin_router
from aggregator.web.event_routes import event_router
from aggregator.web.signup_routes import signup_router
from aggregator.web.comparison_routes import comparison_router

log = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATE_DIR), context_processors=[page_context])


def _deals_db_read_only_runtime() -> bool:
    """Return True when startup should validate, not mutate, the deal DB."""
    return env_flag("DEALS_DB_READ_ONLY") or bool(os.environ.get("VERCEL"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    auth.ensure_auth_config()
    if _deals_db_read_only_runtime():
        await ensure_deals_db_ready()
    else:
        await init_db()
    await init_auth_db()
    # Auto-generate admin key for local development if not set
    if not auth.get_admin_key():
        admin_key = secrets.token_urlsafe(16)
        os.environ["ADMIN_KEY"] = admin_key
        log.warning(
            "No ADMIN_KEY set — generated one for this session:\n"
            "  http://localhost:8000/?admin_key=%s",
            admin_key,
        )
    yield


def create_app(*, enable_lifespan: bool | None = None) -> FastAPI:
    if enable_lifespan is None:
        enable_lifespan = not env_flag("DISABLE_APP_LIFESPAN")
    app = FastAPI(title="FreshPowder", lifespan=lifespan if enable_lifespan else None)
    @app.exception_handler(HTTPException)
    async def page_error(request: Request, error: HTTPException):
        if 'text/html' not in request.headers.get('accept', '') or request.url.path.startswith(('/api/', '/static/')):
            return await http_exception_handler(request, error)
        message = 'This page could not be found.' if error.status_code == 404 else 'We could not open this page. Check your filters or try again.'
        return templates.TemplateResponse(request=request, name='error.html', status_code=error.status_code,
            context={'error_title': 'Page not found' if error.status_code == 404 else 'Let’s try that again',
                     'message': message, 'noindex': True, 'page_title': 'Page unavailable | FreshPowder'})

    @app.exception_handler(RequestValidationError)
    async def invalid_page(request: Request, error: RequestValidationError):
        if 'text/html' not in request.headers.get('accept', '') or request.url.path.startswith('/api/'):
            return await request_validation_exception_handler(request, error)
        return templates.TemplateResponse(request=request, name='error.html', status_code=422,
            context={'error_title': 'Check your filters', 'message': 'Use valid numbers and a minimum no greater than the maximum. You can start again with all gear.',
                     'noindex': True, 'page_title': 'Check your filters | FreshPowder'})

    app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.include_router(invite_router)
    app.include_router(admin_router)
    app.include_router(event_router)
    app.include_router(signup_router)
    app.include_router(router)
    app.include_router(comparison_router)
    return app
