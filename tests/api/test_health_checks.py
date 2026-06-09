from unittest.mock import AsyncMock, patch

from app.api.v1.health import check_database, check_redis


async def test_check_database_success() -> None:
    result = await check_database("sqlite+aiosqlite:///:memory:")
    assert result == "ok"


async def test_check_database_failure_bad_url() -> None:
    result = await check_database("invalid://not-a-database")
    assert result.startswith("error:")


async def test_check_redis_success() -> None:
    mock_r = AsyncMock()
    with patch("app.api.v1.health.aioredis.from_url", return_value=mock_r):
        result = await check_redis("redis://localhost:6379")
    assert result == "ok"
    mock_r.ping.assert_called_once()
    mock_r.aclose.assert_called_once()


async def test_check_redis_failure_connection_refused() -> None:
    with patch(
        "app.api.v1.health.aioredis.from_url",
        side_effect=ConnectionRefusedError("Connection refused"),
    ):
        result = await check_redis("redis://localhost:9999")
    assert result.startswith("error:")
