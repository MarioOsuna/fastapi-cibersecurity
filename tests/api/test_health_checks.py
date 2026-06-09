from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.asyncio import create_async_engine

from app.api.v1.health import check_database, check_redis


async def test_check_database_success() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    result = await check_database(engine)
    await engine.dispose()
    assert result == "ok"


async def test_check_database_failure() -> None:
    engine = create_async_engine("sqlite+aiosqlite:////nonexistent/path/db.sqlite")
    result = await check_database(engine)
    await engine.dispose()
    assert result.startswith("error:")


async def test_check_redis_success() -> None:
    mock_client: MagicMock = MagicMock()
    mock_client.ping = AsyncMock(return_value=True)
    result = await check_redis(mock_client)
    assert result == "ok"
    mock_client.ping.assert_called_once()


async def test_check_redis_failure() -> None:
    mock_client: MagicMock = MagicMock()
    mock_client.ping = AsyncMock(side_effect=ConnectionRefusedError("refused"))
    result = await check_redis(mock_client)
    assert result.startswith("error:")
