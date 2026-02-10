"""Application configuration via pydantic-settings."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    llm_model: str = "openai:gpt-4o"
    llm_api_key: str = ""

    # Slack
    slack_bot_token: str = ""
    slack_app_token: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///chatter.db"

    # Memory
    chromadb_path: Path = Path("./chroma_data")

    # MCP
    brave_search_api_key: str = ""

    # Web UI
    web_host: str = "0.0.0.0"
    web_port: int = 8080
    secret_key: str = Field(default="change-me-in-production")

    # Logging
    log_level: str = "INFO"


settings = Settings()
