"""Database models."""

import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    """A conversation thread (e.g., a Slack thread)."""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    source: Mapped[str] = mapped_column(String, default="slack")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", order_by="Message.created_at"
    )


class Message(Base):
    """A single message in a conversation."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String)  # user, assistant, system, tool
    content: Mapped[str] = mapped_column(Text)
    user_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    tool_calls: Mapped[list["ToolCall"]] = relationship(back_populates="message")


class ToolCall(Base):
    """A tool/MCP call made during a message."""

    __tablename__ = "tool_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"))
    tool_name: Mapped[str] = mapped_column(String)
    tool_input: Mapped[str] = mapped_column(Text)  # JSON
    tool_output: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    message: Mapped["Message"] = relationship(back_populates="tool_calls")


class Soul(Base):
    """Bot personality / system prompt configuration."""

    __tablename__ = "souls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    system_prompt: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class MCPServerConfig(Base):
    """Configuration for an MCP server."""

    __tablename__ = "mcp_server_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    server_type: Mapped[str] = mapped_column(String)  # stdio, http
    command: Mapped[str | None] = mapped_column(String, nullable=True)
    args: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    env_vars: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON dict
    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
