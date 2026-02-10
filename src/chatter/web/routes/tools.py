"""MCP tool management routes."""

import json

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

from chatter.db.engine import async_session
from chatter.db.repositories import MCPServerRepository
from chatter.mcp.manager import get_mcp_manager

router = APIRouter()


@router.get("/")
async def tools_page(request: Request):
    templates = request.app.state.templates
    async with async_session() as session:
        repo = MCPServerRepository(session)
        servers = await repo.list_all()

    # Get live tool info from connected servers
    manager = get_mcp_manager()
    connected_tools = manager.get_all_tools()

    return templates.TemplateResponse("tools.html", {
        "request": request,
        "page": "tools",
        "servers": servers,
        "connected_tools": connected_tools,
    })


@router.post("/save")
async def save_server(
    request: Request,
    name: str = Form(...),
    server_type: str = Form(...),
    command: str = Form(default=""),
    args: str = Form(default=""),
    url: str = Form(default=""),
    env_vars: str = Form(default=""),
    enabled: bool = Form(default=False),
):
    args_list = [a.strip() for a in args.split() if a.strip()] if args else None
    env_dict = json.loads(env_vars) if env_vars.strip() else None

    async with async_session() as session:
        repo = MCPServerRepository(session)
        await repo.upsert(
            name=name,
            server_type=server_type,
            command=command or None,
            args=args_list,
            url=url or None,
            env_vars=env_dict,
            enabled=enabled,
        )
        await session.commit()
    return RedirectResponse(url="/tools", status_code=303)


@router.post("/delete/{name}")
async def delete_server(name: str):
    async with async_session() as session:
        repo = MCPServerRepository(session)
        await repo.delete(name)
        await session.commit()
    return RedirectResponse(url="/tools", status_code=303)
