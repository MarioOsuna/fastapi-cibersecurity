from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import create_db_engine, create_session_factory


async def test_create_db_engine_returns_engine() -> None:
    engine = create_db_engine("sqlite+aiosqlite:///:memory:")
    assert engine is not None
    await engine.dispose()


async def test_create_db_engine_echo_flag() -> None:
    engine = create_db_engine("sqlite+aiosqlite:///:memory:", echo=True)
    assert engine.echo is True
    await engine.dispose()


async def test_create_session_factory_returns_sessionmaker() -> None:
    engine = create_db_engine("sqlite+aiosqlite:///:memory:")
    factory = create_session_factory(engine)
    assert isinstance(factory, async_sessionmaker)
    # Verify it produces AsyncSession instances
    async with factory() as session:
        assert isinstance(session, AsyncSession)
    await engine.dispose()
