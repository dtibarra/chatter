"""Data access layer."""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from chatter.db.models import Conversation, MCPServerConfig, Message, Soul, ToolCall


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, external_id: str, source: str = "slack") -> Conversation:
        result = await self.session.execute(
            select(Conversation).where(Conversation.external_id == external_id)
        )
        convo = result.scalar_one_or_none()
        if convo is None:
            convo = Conversation(external_id=external_id, source=source)
            self.session.add(convo)
            await self.session.flush()
        return convo

    async def get_by_external_id(self, external_id: str) -> Conversation | None:
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.external_id == external_id)
            .options(selectinload(Conversation.messages))
        )
        return result.scalar_one_or_none()

    async def list_recent(self, limit: int = 50) -> list[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def add_message(
        self,
        conversation: Conversation,
        role: str,
        content: str,
        user_name: str | None = None,
    ) -> Message:
        msg = Message(
            conversation_id=conversation.id,
            role=role,
            content=content,
            user_name=user_name,
        )
        self.session.add(msg)
        await self.session.flush()
        return msg

    async def add_tool_call(
        self,
        message: Message,
        tool_name: str,
        tool_input: dict,
        tool_output: str | None = None,
        duration_ms: int | None = None,
    ) -> ToolCall:
        tc = ToolCall(
            message_id=message.id,
            tool_name=tool_name,
            tool_input=json.dumps(tool_input),
            tool_output=tool_output,
            duration_ms=duration_ms,
        )
        self.session.add(tc)
        await self.session.flush()
        return tc


class SoulRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active(self) -> Soul | None:
        result = await self.session.execute(
            select(Soul).where(Soul.is_active.is_(True)).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Soul | None:
        result = await self.session.execute(
            select(Soul).where(Soul.name == name)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Soul]:
        result = await self.session.execute(select(Soul).order_by(Soul.name))
        return list(result.scalars().all())

    async def upsert(self, name: str, system_prompt: str, is_active: bool = True) -> Soul:
        soul = await self.get_by_name(name)
        if soul is None:
            soul = Soul(name=name, system_prompt=system_prompt, is_active=is_active)
            self.session.add(soul)
        else:
            soul.system_prompt = system_prompt
            soul.is_active = is_active
        if is_active:
            # Deactivate all others
            await self.session.execute(
                Soul.__table__.update()
                .where(Soul.name != name)
                .values(is_active=False)
            )
        await self.session.flush()
        return soul


class MCPServerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_enabled(self) -> list[MCPServerConfig]:
        result = await self.session.execute(
            select(MCPServerConfig).where(MCPServerConfig.enabled.is_(True))
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[MCPServerConfig]:
        result = await self.session.execute(
            select(MCPServerConfig).order_by(MCPServerConfig.name)
        )
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> MCPServerConfig | None:
        result = await self.session.execute(
            select(MCPServerConfig).where(MCPServerConfig.name == name)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        name: str,
        server_type: str,
        command: str | None = None,
        args: list[str] | None = None,
        url: str | None = None,
        env_vars: dict | None = None,
        enabled: bool = True,
    ) -> MCPServerConfig:
        config = await self.get_by_name(name)
        if config is None:
            config = MCPServerConfig(name=name, server_type=server_type)
            self.session.add(config)
        config.server_type = server_type
        config.command = command
        config.args = json.dumps(args) if args else None
        config.url = url
        config.env_vars = json.dumps(env_vars) if env_vars else None
        config.enabled = enabled
        await self.session.flush()
        return config

    async def delete(self, name: str) -> bool:
        config = await self.get_by_name(name)
        if config:
            await self.session.delete(config)
            await self.session.flush()
            return True
        return False
