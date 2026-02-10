"""Soul (system prompt) management routes."""

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

from chatter.db.engine import async_session
from chatter.db.repositories import SoulRepository

router = APIRouter()


@router.get("/")
async def soul_page(request: Request):
    templates = request.app.state.templates
    async with async_session() as session:
        repo = SoulRepository(session)
        souls = await repo.list_all()
        active = await repo.get_active()
    return templates.TemplateResponse("soul.html", {
        "request": request,
        "page": "soul",
        "souls": souls,
        "active_soul": active,
    })


@router.post("/save")
async def save_soul(
    request: Request,
    name: str = Form(...),
    system_prompt: str = Form(...),
    is_active: bool = Form(default=False),
):
    async with async_session() as session:
        repo = SoulRepository(session)
        await repo.upsert(name, system_prompt, is_active)
        await session.commit()
    return RedirectResponse(url="/soul", status_code=303)
