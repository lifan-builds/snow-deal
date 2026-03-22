"""FastAPI application factory."""

from __future__ import annotations

from pathlib import Path
from contextlib import asynccontextmanager

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from aggregator.auth import auth_middleware
from aggregator.db import init_db
from aggregator.web.routes import router
from aggregator.web.invite_routes import invite_router

STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="snow-deals aggregator", lifespan=lifespan)
    app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.include_router(invite_router)
    app.include_router(router)
    return app
