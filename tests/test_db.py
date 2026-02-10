"""Tests for database models and repositories."""

import pytest

from chatter.db.repositories import ConversationRepository, SoulRepository, MCPServerRepository


@pytest.mark.asyncio
async def test_conversation_create_and_retrieve(db_session):
    repo = ConversationRepository(db_session)
    convo = await repo.get_or_create("thread-123", source="slack")
    assert convo.external_id == "thread-123"
    assert convo.source == "slack"

    # Retrieving again returns the same one
    same = await repo.get_or_create("thread-123")
    assert same.id == convo.id


@pytest.mark.asyncio
async def test_conversation_messages(db_session):
    repo = ConversationRepository(db_session)
    convo = await repo.get_or_create("thread-456")

    await repo.add_message(convo, role="user", content="Hello!", user_name="alice")
    await repo.add_message(convo, role="assistant", content="Hi there!")

    full = await repo.get_by_external_id("thread-456")
    assert len(full.messages) == 2
    assert full.messages[0].role == "user"
    assert full.messages[0].content == "Hello!"
    assert full.messages[0].user_name == "alice"
    assert full.messages[1].role == "assistant"


@pytest.mark.asyncio
async def test_conversation_list_recent(db_session):
    repo = ConversationRepository(db_session)
    await repo.get_or_create("t1")
    await repo.get_or_create("t2")
    await repo.get_or_create("t3")

    recent = await repo.list_recent(limit=2)
    assert len(recent) == 2


@pytest.mark.asyncio
async def test_soul_upsert_and_activate(db_session):
    repo = SoulRepository(db_session)

    await repo.upsert("default", "You are helpful.", is_active=True)
    await repo.upsert("creative", "You are creative.", is_active=False)

    active = await repo.get_active()
    assert active.name == "default"

    # Activate creative
    await repo.upsert("creative", "You are creative.", is_active=True)
    active = await repo.get_active()
    assert active.name == "creative"

    all_souls = await repo.list_all()
    assert len(all_souls) == 2


@pytest.mark.asyncio
async def test_mcp_server_crud(db_session):
    repo = MCPServerRepository(db_session)

    await repo.upsert(
        name="fetch",
        server_type="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-fetch"],
        enabled=True,
    )

    servers = await repo.list_all()
    assert len(servers) == 1
    assert servers[0].name == "fetch"

    enabled = await repo.list_enabled()
    assert len(enabled) == 1

    deleted = await repo.delete("fetch")
    assert deleted is True

    servers = await repo.list_all()
    assert len(servers) == 0
