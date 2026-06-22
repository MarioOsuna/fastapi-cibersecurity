from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.events import router as events_router
from app.api.v1.health import router as health_router
from app.api.v1.threats import router as threats_router
from app.core.config import get_settings
from app.core.database import create_db_engine, create_session_factory
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:  # pragma: no cover
    settings = get_settings()
    setup_logging(settings.log_level)

    engine = create_db_engine(settings.database_url, echo=settings.debug)
    _app.state.engine = engine
    _app.state.session_factory = create_session_factory(engine)

    redis_client = aioredis.from_url(settings.redis_url)
    _app.state.redis = redis_client

    yield

    await engine.dispose()
    await redis_client.aclose()  # type: ignore[attr-defined]


def create_app() -> FastAPI:
    settings = get_settings()
    _app = FastAPI(title="Threat Analysis API", version="0.1.0", lifespan=lifespan)
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    _app.include_router(health_router)
    _app.include_router(events_router)
    _app.include_router(threats_router)
    return _app


app = create_app()
