"""FastAPI web application for the Chatter admin UI."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from chatter.db.engine import init_db
from chatter.db.engine import async_session
from chatter.db.repositories import SoulRepository
from chatter.agent.prompts import DEFAULT_SOUL

WEB_DIR = Path(__file__).parent
TEMPLATE_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App startup/shutdown."""
    await init_db()
    # Seed default soul if none exists
    async with async_session() as session:
        repo = SoulRepository(session)
        existing = await repo.get_active()
        if existing is None:
            await repo.upsert("default", DEFAULT_SOUL, is_active=True)
            await session.commit()
    yield


def create_web_app() -> FastAPI:
    """Create the FastAPI web application."""
    app = FastAPI(title="Chatter Admin", lifespan=lifespan)

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
    # Make templates available to route modules
    app.state.templates = templates

    # Register routes
    from chatter.web.routes import dashboard, memory, soul, tools, conversations, settings

    app.include_router(dashboard.router)
    app.include_router(memory.router, prefix="/memory", tags=["memory"])
    app.include_router(soul.router, prefix="/soul", tags=["soul"])
    app.include_router(tools.router, prefix="/tools", tags=["tools"])
    app.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
    app.include_router(settings.router, prefix="/settings", tags=["settings"])

    return app
