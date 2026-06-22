import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_event import EventType, SeverityLevel
from app.repositories.event_repository import EventRepository
from app.schemas.events import EventCreate
from app.services.event_service import EventService


async def test_register_event_persists_and_returns(db_session: AsyncSession) -> None:
    service = EventService(EventRepository(db_session))
    data = EventCreate(
        source_ip="10.0.0.5",
        event_type=EventType.PORT_SCAN,
        severity=SeverityLevel.MEDIUM,
        raw_payload={"port": 22},
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    event = await service.register_event(data)

    assert isinstance(event.id, uuid.UUID)
    assert event.source_ip == "10.0.0.5"
    assert event.event_type == EventType.PORT_SCAN
    assert event.severity == SeverityLevel.MEDIUM
    assert event.raw_payload == {"port": 22}


async def test_register_event_defaults_occurred_at(db_session: AsyncSession) -> None:
    service = EventService(EventRepository(db_session))
    data = EventCreate(
        source_ip="10.0.0.6",
        event_type=EventType.LOGIN_FAILURE,
        severity=SeverityLevel.LOW,
    )
    event = await service.register_event(data)
    assert event.occurred_at is not None
