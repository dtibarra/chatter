"""Dashboard route - main landing page."""

from fastapi import APIRouter, Request

from chatter.db.engine import async_session
from chatter.db.repositories import ConversationRepository, SoulRepository
from chatter.memory.store import get_memory_store

router = APIRouter()


@router.get("/")
async def dashboard(request: Request):
    templates = request.app.state.templates
    store = get_memory_store()
    stats = store.get_stats()

    async with async_session() as session:
        convo_repo = ConversationRepository(session)
        recent_convos = await convo_repo.list_recent(limit=10)

        soul_repo = SoulRepository(session)
        active_soul = await soul_repo.get_active()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "page": "dashboard",
        "memory_stats": stats,
        "recent_conversations": recent_convos,
        "active_soul": active_soul,
    })
