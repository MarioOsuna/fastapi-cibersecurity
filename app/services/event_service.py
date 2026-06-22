from __future__ import annotations

from datetime import UTC, datetime

from app.models.security_event import SecurityEvent
from app.repositories.event_repository import EventRepository
from app.schemas.events import EventCreate


class EventService:
    def __init__(self, event_repo: EventRepository) -> None:
        self._event_repo = event_repo

    async def register_event(self, data: EventCreate) -> SecurityEvent:
        event = SecurityEvent(
            source_ip=data.source_ip,
            event_type=data.event_type,
            severity=data.severity,
            raw_payload=data.raw_payload,
            occurred_at=data.occurred_at or datetime.now(UTC),
        )
        return await self._event_repo.create(event)
