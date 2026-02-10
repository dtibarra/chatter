"""Slack event handlers."""

from __future__ import annotations

import logging
import re

from slack_bolt.async_app import AsyncApp

from chatter.agent.core import process_message
from chatter.agent.prompts import DEFAULT_SOUL
from chatter.db.engine import async_session
from chatter.db.repositories import ConversationRepository, SoulRepository

logger = logging.getLogger(__name__)

# Regex to strip Slack user mentions like <@U1234ABC>
MENTION_RE = re.compile(r"<@[A-Z0-9]+>")


def _clean_text(text: str) -> str:
    """Remove Slack mention tags from message text."""
    return MENTION_RE.sub("", text).strip()


def register_handlers(app: AsyncApp):
    """Register all Slack event handlers on the app."""

    bot_user_id: str | None = None

    @app.middleware
    async def capture_bot_id(body, next):
        nonlocal bot_user_id
        if bot_user_id is None and "authorizations" in body:
            bot_user_id = body["authorizations"][0]["user_id"]
        await next()

    @app.event("app_mention")
    async def handle_mention(body, say):
        """Handle when the bot is @mentioned in a channel."""
        event = body["event"]

        # If it's a threaded reply, let the message handler deal with it
        if "thread_ts" in event:
            return

        text = _clean_text(event.get("text", ""))
        user_id = event.get("user", "unknown")
        channel = event.get("channel")
        ts = event.get("ts")

        if not text:
            return

        try:
            response = await _process_and_store(
                text=text,
                thread_id=ts,
                user_name=user_id,
            )
            await say(text=response, thread_ts=ts)
        except Exception:
            logger.exception("Error processing mention")
            await say(
                text="Sorry, I ran into an error processing that. Please try again.",
                thread_ts=ts,
            )

    @app.event("message")
    async def handle_message(body, say):
        """Handle messages in threads the bot is part of."""
        event = body["event"]

        # Ignore bot's own messages
        if event.get("user") == bot_user_id:
            return

        # Only handle threaded replies
        thread_ts = event.get("thread_ts")
        if not thread_ts:
            return

        text = _clean_text(event.get("text", ""))
        user_id = event.get("user", "unknown")

        if not text:
            return

        # Check if we have a conversation for this thread
        async with async_session() as session:
            repo = ConversationRepository(session)
            convo = await repo.get_by_external_id(thread_ts)
            if convo is None:
                # We weren't part of this thread
                return

        try:
            response = await _process_and_store(
                text=text,
                thread_id=thread_ts,
                user_name=user_id,
            )
            await say(text=response, thread_ts=thread_ts)
        except Exception:
            logger.exception("Error processing thread message")
            await say(
                text="Sorry, I ran into an error processing that. Please try again.",
                thread_ts=thread_ts,
            )


async def _process_and_store(
    text: str,
    thread_id: str,
    user_name: str | None = None,
) -> str:
    """Process a message through the agent and persist the conversation."""
    async with async_session() as session:
        convo_repo = ConversationRepository(session)
        soul_repo = SoulRepository(session)

        # Get or create conversation
        convo = await convo_repo.get_or_create(external_id=thread_id)

        # Get the active soul
        soul = await soul_repo.get_active()
        soul_text = soul.system_prompt if soul else DEFAULT_SOUL

        # Build conversation history from DB
        convo_with_messages = await convo_repo.get_by_external_id(thread_id)
        history = []
        if convo_with_messages and convo_with_messages.messages:
            for msg in convo_with_messages.messages[-20:]:  # Last 20 messages
                history.append({"role": msg.role, "content": msg.content})

        # Store the user message
        await convo_repo.add_message(convo, role="user", content=text, user_name=user_name)

        # Process through the agent
        response = await process_message(
            message=text,
            conversation_id=thread_id,
            soul_text=soul_text,
            user_name=user_name,
            conversation_history=history,
        )

        # Store the assistant response
        await convo_repo.add_message(convo, role="assistant", content=response)

        await session.commit()

    return response
