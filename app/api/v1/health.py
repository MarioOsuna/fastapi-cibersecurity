from datetime import UTC, datetime
from typing import Annotated, Any

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings, get_settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


async def check_database(database_url: str) -> str:
    try:
        engine = create_async_engine(database_url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        return "ok"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


async def check_redis(redis_url: str) -> str:
    try:
        r = aioredis.from_url(redis_url)
        await r.ping()
        await r.aclose()  # type: ignore[attr-defined]  # aclose = close, stubs lag
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
    settings: Annotated[Settings, Depends(get_settings)],
) -> JSONResponse:
    db_status = await check_database(settings.database_url)
    redis_status = await check_redis(settings.redis_url)

    checks = {"database": db_status, "redis": redis_status}
    all_ok = all(v == "ok" for v in checks.values())

    body: dict[str, Any] = {
        "status": "ok" if all_ok else "degraded",
        "checks": checks,
    }
    return JSONResponse(content=body, status_code=200 if all_ok else 503)
