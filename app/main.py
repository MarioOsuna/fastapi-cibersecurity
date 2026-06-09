from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    setup_logging(settings.log_level)
    # Phase 2: init DB engine and Redis client here
    yield
    # Phase 2: close DB engine and Redis client here


def create_app() -> FastAPI:
    _app = FastAPI(
        title="Threat Analysis API",
        version="0.1.0",
        lifespan=lifespan,
    )
    # Phase 4: register exception handlers here
    # Phase 5: register middleware here
    return _app


app = create_app()
