"""Shared test fixtures."""

import os
import tempfile

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Override settings before importing anything else
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["CHROMADB_PATH"] = tempfile.mkdtemp()
os.environ["LLM_API_KEY"] = "test-key"
os.environ["SLACK_BOT_TOKEN"] = "xoxb-test"
os.environ["SLACK_APP_TOKEN"] = "xapp-test"

from chatter.db.models import Base


@pytest_asyncio.fixture
async def db_session():
    """Create a fresh in-memory database for each test."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def memory_store():
    """Create a temporary memory store."""
    from chatter.memory.store import MemoryStore

    with tempfile.TemporaryDirectory() as tmpdir:
        store = MemoryStore(path=tmpdir)
        yield store
