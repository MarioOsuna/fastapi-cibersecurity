from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.repositories.event_repository import EventRepository
from app.repositories.indicator_repository import IndicatorRepository
from app.services.event_service import EventService
from app.services.scoring import ScoringService


def get_engine(request: Request) -> AsyncEngine:
    return request.app.state.engine  # type: ignore[no-any-return]


def get_session_factory(
    request: Request,
) -> async_sessionmaker[AsyncSession]:
    return request.app.state.session_factory  # type: ignore[no-any-return]


async def get_db_session(
    session_factory: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_factory)],
) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session
        await session.commit()


def get_redis_client(request: Request) -> Redis:  # type: ignore[type-arg]
    return request.app.state.redis  # type: ignore[no-any-return]


def get_indicator_repo(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IndicatorRepository:
    return IndicatorRepository(session)


def get_event_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> EventService:
    return EventService(EventRepository(session))


def get_scoring_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ScoringService:
    return ScoringService(EventRepository(session), IndicatorRepository(session))
