"""Tests for configuration."""

from chatter.config import Settings


def test_default_settings():
    s = Settings(
        llm_api_key="test",
        slack_bot_token="xoxb-test",
        slack_app_token="xapp-test",
    )
    assert s.llm_model == "openai:gpt-4o"
    assert s.web_port == 8080
    assert s.log_level == "INFO"


def test_custom_settings():
    s = Settings(
        llm_model="anthropic:claude-sonnet-4-20250514",
        llm_api_key="sk-test",
        slack_bot_token="xoxb-test",
        slack_app_token="xapp-test",
        web_port=9090,
        log_level="DEBUG",
    )
    assert s.llm_model == "anthropic:claude-sonnet-4-20250514"
    assert s.web_port == 9090
    assert s.log_level == "DEBUG"
