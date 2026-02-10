"""Memory browser routes."""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from chatter.memory.store import get_memory_store

router = APIRouter()


@router.get("/")
async def memory_page(request: Request):
    templates = request.app.state.templates
    store = get_memory_store()
    stats = store.get_stats()
    facts = store.list_facts(limit=50)
    episodes = store.list_episodes(limit=50)
    return templates.TemplateResponse("memory.html", {
        "request": request,
        "page": "memory",
        "stats": stats,
        "facts": facts,
        "episodes": episodes,
    })


@router.post("/search")
async def search_memory(request: Request, query: str = Form(...)):
    templates = request.app.state.templates
    store = get_memory_store()
    results = store.search_all(query, n_results=20)
    return templates.TemplateResponse("partials/memory_results.html", {
        "request": request,
        "results": results,
        "query": query,
    })


@router.delete("/{collection}/{memory_id}")
async def delete_memory(collection: str, memory_id: str):
    store = get_memory_store()
    store.delete_memory(collection, memory_id)
    return HTMLResponse("")
