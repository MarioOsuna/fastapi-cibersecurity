from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models as _models  # noqa: F401 — populates Base.metadata before create_all
from app.core.config import Settings, get_settings
from app.core.database import Base
from app.core.dependencies import get_engine, get_redis_client
from app.main import create_app

_TEST_SETTINGS = Settings(
    database_url="sqlite+aiosqlite:///./test.db",
    redis_url="redis://localhost:6379",
)

# Shared SQLite engine for HTTP-layer tests (lifespan doesn't run with ASGITransport).
_HTTP_TEST_ENGINE = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_HTTP_TEST_REDIS: MagicMock = MagicMock()

# ── HTTP client fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def app() -> FastAPI:
    application = create_app()
    application.dependency_overrides[get_settings] = lambda: _TEST_SETTINGS
    application.dependency_overrides[get_engine] = lambda: _HTTP_TEST_ENGINE
    application.dependency_overrides[get_redis_client] = lambda: _HTTP_TEST_REDIS
    return application


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


# ── Database fixtures (rollback pattern) ──────────────────────────────────────


@pytest.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Session-scoped in-memory engine. Tables created once; each test rolls back."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Function-scoped session bound to a connection-level transaction.

    The transaction is rolled back after each test — no DROP/CREATE per test.
    Repositories must use flush() not commit() to stay within this transaction.
    """
    connection = await test_engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()
