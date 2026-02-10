"""Settings management routes."""

from fastapi import APIRouter, Request

from chatter.config import settings

router = APIRouter()


@router.get("/")
async def settings_page(request: Request):
    templates = request.app.state.templates
    # Show settings (mask sensitive values)
    display_settings = {
        "llm_model": settings.llm_model,
        "llm_api_key": _mask(settings.llm_api_key),
        "slack_bot_token": _mask(settings.slack_bot_token),
        "slack_app_token": _mask(settings.slack_app_token),
        "database_url": settings.database_url,
        "chromadb_path": str(settings.chromadb_path),
        "brave_search_api_key": _mask(settings.brave_search_api_key),
        "web_host": settings.web_host,
        "web_port": settings.web_port,
        "log_level": settings.log_level,
    }
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "page": "settings",
        "settings": display_settings,
    })


def _mask(value: str) -> str:
    if not value or len(value) < 8:
        return "***" if value else "(not set)"
    return value[:4] + "..." + value[-4:]
