"""Slack message formatting utilities."""

from __future__ import annotations


def truncate_for_slack(text: str, max_length: int = 3000) -> str:
    """Truncate text to fit Slack's message limits."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def format_error(error: str) -> str:
    """Format an error message for Slack."""
    return f":warning: {error}"


def format_thinking(text: str) -> str:
    """Format a thinking/reasoning step for Slack."""
    return f"_Thinking: {text}_"
