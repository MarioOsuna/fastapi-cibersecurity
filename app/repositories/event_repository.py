from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_event import SecurityEvent


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, event: SecurityEvent) -> SecurityEvent:
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_by_id(self, event_id: uuid.UUID) -> SecurityEvent | None:
        return await self.session.get(SecurityEvent, event_id)

    async def list_by_source_ip(self, source_ip: str) -> list[SecurityEvent]:
        result = await self.session.execute(
            select(SecurityEvent).where(SecurityEvent.source_ip == source_ip)
        )
        return list(result.scalars().all())

    async def list_recent(
        self,
        *,
        limit: int = 100,
        since: datetime | None = None,
    ) -> list[SecurityEvent]:
        if since is None:
            since = datetime.now(UTC) - timedelta(hours=24)
        result = await self.session.execute(
            select(SecurityEvent)
            .where(SecurityEvent.occurred_at >= since)
            .order_by(SecurityEvent.occurred_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
