"""Slack bot using Socket Mode with PydanticAI agent integration."""

from __future__ import annotations

import logging

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from chatter.config import settings

logger = logging.getLogger(__name__)


def create_slack_app() -> AsyncApp:
    """Create and configure the Slack Bolt app."""
    app = AsyncApp(
        token=settings.slack_bot_token,
        # Socket Mode doesn't need signing_secret, but we keep it for webhook fallback
    )

    # Register event handlers
    from chatter.slack.events import register_handlers

    register_handlers(app)

    return app


async def start_slack_bot():
    """Start the Slack bot in Socket Mode."""
    app = create_slack_app()
    handler = AsyncSocketModeHandler(app, settings.slack_app_token)
    logger.info("Starting Slack bot in Socket Mode...")
    await handler.start_async()
