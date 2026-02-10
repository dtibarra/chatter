"""PydanticAI agent definition - the brain of Chatter."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from chatter.config import settings
from chatter.memory.store import get_memory_store

logger = logging.getLogger(__name__)


@dataclass
class AgentDeps:
    """Dependencies injected into the agent at runtime."""

    conversation_id: str
    user_name: str | None = None
    conversation_history: list[dict] | None = None


def build_system_prompt(soul_text: str, memories: list[dict]) -> str:
    """Build the full system prompt with soul + relevant memories."""
    parts = [soul_text]
    if memories:
        parts.append("\n## Relevant memories from past interactions:\n")
        for mem in memories:
            parts.append(f"- {mem['content']}")
    return "\n".join(parts)


def create_agent(system_prompt: str) -> Agent[AgentDeps, str]:
    """Create a PydanticAI agent with the given system prompt."""

    agent = Agent(
        settings.llm_model,
        system_prompt=system_prompt,
        result_type=str,
        deps_type=AgentDeps,
    )

    @agent.tool
    async def recall_memories(ctx: RunContext[AgentDeps], query: str) -> str:
        """Search long-term memory for relevant past information.

        Args:
            query: What to search for in memory.
        """
        store = get_memory_store()
        results = store.search_all(query, n_results=5)

        parts = []
        if results["episodes"]:
            parts.append("**Past conversations:**")
            for ep in results["episodes"]:
                parts.append(f"- {ep['content']}")
        if results["facts"]:
            parts.append("**Known facts:**")
            for fact in results["facts"]:
                parts.append(f"- {fact['content']}")

        return "\n".join(parts) if parts else "No relevant memories found."

    @agent.tool
    async def store_fact(ctx: RunContext[AgentDeps], fact: str) -> str:
        """Store an important fact in long-term memory for future reference.

        Args:
            fact: The fact to remember.
        """
        store = get_memory_store()
        store.store_fact(fact, source="agent", metadata={"user": ctx.deps.user_name or "unknown"})
        return f"Stored: {fact}"

    return agent


async def process_message(
    message: str,
    conversation_id: str,
    soul_text: str,
    user_name: str | None = None,
    conversation_history: list[dict] | None = None,
) -> str:
    """Process a user message through the agent and return a response.

    This is the main entry point for the agent. It:
    1. Retrieves relevant memories
    2. Builds the system prompt with context
    3. Runs the PydanticAI agent (which may call tools, reason, etc.)
    4. Stores the exchange in episodic memory
    5. Returns the response text
    """
    store = get_memory_store()

    # Retrieve relevant memories for context
    memories = store.search_all(message, n_results=3)
    all_memories = memories.get("facts", []) + memories.get("episodes", [])

    # Build the prompt
    full_prompt = build_system_prompt(soul_text, all_memories)

    # Create and run the agent
    agent = create_agent(full_prompt)
    deps = AgentDeps(
        conversation_id=conversation_id,
        user_name=user_name,
        conversation_history=conversation_history,
    )

    # Build message history for multi-turn
    messages = []
    if conversation_history:
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})

    result = await agent.run(message, deps=deps, message_history=messages or None)
    response_text = result.data

    # Store the exchange in episodic memory
    store.store_episode(
        content=f"User ({user_name or 'unknown'}): {message}",
        conversation_id=conversation_id,
        role="user",
    )
    store.store_episode(
        content=f"Assistant: {response_text}",
        conversation_id=conversation_id,
        role="assistant",
    )

    return response_text
