import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_event import EventType, SecurityEvent, SeverityLevel


async def test_security_event_create(db_session: AsyncSession) -> None:
    now = datetime.now(UTC)
    event = SecurityEvent(
        source_ip="192.168.1.1",
        event_type=EventType.LOGIN_FAILURE,
        severity=SeverityLevel.HIGH,
        raw_payload={"attempts": 5},
        occurred_at=now,
    )
    db_session.add(event)
    await db_session.flush()

    assert isinstance(event.id, uuid.UUID)
    assert event.source_ip == "192.168.1.1"
    assert event.event_type == EventType.LOGIN_FAILURE
    assert event.severity == SeverityLevel.HIGH
    assert event.raw_payload == {"attempts": 5}
    assert event.occurred_at == now
    assert event.created_at is not None


async def test_security_event_occurred_at_independent_of_created_at(
    db_session: AsyncSession,
) -> None:
    past = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    event = SecurityEvent(
        source_ip="10.0.0.1",
        event_type=EventType.PORT_SCAN,
        severity=SeverityLevel.MEDIUM,
        raw_payload={},
        occurred_at=past,
    )
    db_session.add(event)
    await db_session.flush()

    assert event.occurred_at == past
    assert event.created_at > past


async def test_security_event_query_by_id(db_session: AsyncSession) -> None:
    event = SecurityEvent(
        source_ip="172.16.0.1",
        event_type=EventType.BRUTE_FORCE,
        severity=SeverityLevel.CRITICAL,
        raw_payload={},
        occurred_at=datetime.now(UTC),
    )
    db_session.add(event)
    await db_session.flush()

    fetched = await db_session.get(SecurityEvent, event.id)
    assert fetched is not None
    assert fetched.id == event.id


@pytest.mark.parametrize("event_type", list(EventType))
async def test_all_event_types_are_valid(db_session: AsyncSession, event_type: EventType) -> None:
    event = SecurityEvent(
        source_ip="1.2.3.4",
        event_type=event_type,
        severity=SeverityLevel.LOW,
        raw_payload={},
        occurred_at=datetime.now(UTC),
    )
    db_session.add(event)
    await db_session.flush()
    assert event.event_type == event_type
