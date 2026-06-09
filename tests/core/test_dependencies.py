from unittest.mock import MagicMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import create_db_engine, create_session_factory
from app.core.dependencies import get_db_session, get_engine, get_redis_client, get_session_factory


def _make_request(**state_attrs: object) -> MagicMock:
    request = MagicMock()
    for key, value in state_attrs.items():
        setattr(request.app.state, key, value)
    return request


def test_get_engine_returns_from_app_state() -> None:
    engine = create_db_engine("sqlite+aiosqlite:///:memory:")
    request = _make_request(engine=engine)
    assert get_engine(request) is engine


def test_get_session_factory_returns_from_app_state() -> None:
    engine = create_db_engine("sqlite+aiosqlite:///:memory:")
    factory = create_session_factory(engine)
    request = _make_request(session_factory=factory)
    assert get_session_factory(request) is factory


def test_get_redis_client_returns_from_app_state() -> None:
    mock_redis = MagicMock()
    request = _make_request(redis=mock_redis)
    assert get_redis_client(request) is mock_redis


async def test_get_db_session_yields_async_session() -> None:
    engine = create_db_engine("sqlite+aiosqlite:///:memory:")
    factory = create_session_factory(engine)
    gen = get_db_session(factory)
    session = await gen.__anext__()
    assert isinstance(session, AsyncSession)
    import contextlib

    with contextlib.suppress(StopAsyncIteration):
        await gen.__anext__()
    await engine.dispose()
