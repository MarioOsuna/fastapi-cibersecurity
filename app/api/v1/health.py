from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import Settings, get_settings
from app.core.dependencies import get_engine, get_redis_client
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


async def check_database(engine: AsyncEngine) -> str:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "ok"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


async def check_redis(redis_client: Redis) -> str:  # type: ignore[type-arg]
    try:
        await redis_client.ping()
        return "ok"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


@router.get("/health", response_model=HealthResponse)
async def liveness(
    settings: Annotated[Settings, Depends(get_settings)],
) -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(UTC),
    )


@router.get("/health/ready")
async def readiness(
    engine: Annotated[AsyncEngine, Depends(get_engine)],
    redis_client: Annotated[Redis, Depends(get_redis_client)],  # type: ignore[type-arg]
) -> JSONResponse:
    db_status = await check_database(engine)
    redis_status = await check_redis(redis_client)

    checks = {"database": db_status, "redis": redis_status}
    all_ok = all(v == "ok" for v in checks.values())

    body: dict[str, Any] = {
        "status": "ok" if all_ok else "degraded",
        "checks": checks,
    }
    return JSONResponse(content=body, status_code=200 if all_ok else 503)
