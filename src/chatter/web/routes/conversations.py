"""Conversation history viewer routes."""

from fastapi import APIRouter, Request

from chatter.db.engine import async_session
from chatter.db.repositories import ConversationRepository

router = APIRouter()


@router.get("/")
async def conversations_page(request: Request):
    templates = request.app.state.templates
    async with async_session() as session:
        repo = ConversationRepository(session)
        conversations = await repo.list_recent(limit=50)
    return templates.TemplateResponse("conversations.html", {
        "request": request,
        "page": "conversations",
        "conversations": conversations,
    })


@router.get("/{external_id}")
async def conversation_detail(request: Request, external_id: str):
    templates = request.app.state.templates
    async with async_session() as session:
        repo = ConversationRepository(session)
        conversation = await repo.get_by_external_id(external_id)
    return templates.TemplateResponse("conversation_detail.html", {
        "request": request,
        "page": "conversations",
        "conversation": conversation,
    })
