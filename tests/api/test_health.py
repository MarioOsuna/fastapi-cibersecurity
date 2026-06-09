from unittest.mock import AsyncMock, patch

from httpx import AsyncClient


async def test_liveness_returns_200(async_client: AsyncClient) -> None:
    response = await async_client.get("/health")
    assert response.status_code == 200


async def test_liveness_body(async_client: AsyncClient) -> None:
    response = await async_client.get("/health")
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "0.1.0"
    assert body["environment"] == "development"
    assert "timestamp" in body


async def test_readiness_ok_returns_200(async_client: AsyncClient) -> None:
    with (
        patch("app.api.v1.health.check_database", new=AsyncMock(return_value="ok")),
        patch("app.api.v1.health.check_redis", new=AsyncMock(return_value="ok")),
    ):
        response = await async_client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["redis"] == "ok"


async def test_readiness_503_when_redis_down(async_client: AsyncClient) -> None:
    with (
        patch("app.api.v1.health.check_database", new=AsyncMock(return_value="ok")),
        patch(
            "app.api.v1.health.check_redis",
            new=AsyncMock(return_value="error: Connection refused"),
        ),
    ):
        response = await async_client.get("/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["redis"].startswith("error:")


async def test_readiness_503_when_database_down(async_client: AsyncClient) -> None:
    with (
        patch(
            "app.api.v1.health.check_database",
            new=AsyncMock(return_value="error: unable to open database"),
        ),
        patch("app.api.v1.health.check_redis", new=AsyncMock(return_value="ok")),
    ):
        response = await async_client.get("/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"].startswith("error:")
    assert body["checks"]["redis"] == "ok"
