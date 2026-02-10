"""Tests for the agent module."""

from chatter.agent.prompts import DEFAULT_SOUL
from chatter.agent.core import build_system_prompt


def test_default_soul_is_not_empty():
    assert len(DEFAULT_SOUL) > 50
    assert "Chatter" in DEFAULT_SOUL


def test_build_system_prompt_no_memories():
    prompt = build_system_prompt("You are a bot.", [])
    assert prompt == "You are a bot."


def test_build_system_prompt_with_memories():
    memories = [
        {"content": "User likes Python"},
        {"content": "User works at Acme Corp"},
    ]
    prompt = build_system_prompt("You are a bot.", memories)
    assert "User likes Python" in prompt
    assert "User works at Acme Corp" in prompt
    assert "Relevant memories" in prompt
