import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_event import EventType, SecurityEvent, SeverityLevel
from app.repositories.event_repository import EventRepository


def _make_event(**kwargs: object) -> SecurityEvent:
    return SecurityEvent(
        source_ip=kwargs.get("source_ip", "10.0.0.1"),  # type: ignore[arg-type]
        event_type=kwargs.get("event_type", EventType.LOGIN_FAILURE),  # type: ignore[arg-type]
        severity=kwargs.get("severity", SeverityLevel.LOW),  # type: ignore[arg-type]
        raw_payload=kwargs.get("raw_payload", {}),  # type: ignore[arg-type]
        occurred_at=kwargs.get("occurred_at", datetime.now(UTC)),  # type: ignore[arg-type]
    )


async def test_create_returns_event_with_id(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    event = await repo.create(_make_event())
    assert isinstance(event.id, uuid.UUID)
    assert event.source_ip == "10.0.0.1"


async def test_get_by_id_returns_event(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    created = await repo.create(_make_event())
    fetched = await repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id


async def test_get_by_id_returns_none_for_missing(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    result = await repo.get_by_id(uuid.uuid4())
    assert result is None


async def test_list_by_ip_returns_matching_events(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    await repo.create(_make_event(source_ip="1.1.1.1"))
    await repo.create(_make_event(source_ip="1.1.1.1"))
    await repo.create(_make_event(source_ip="2.2.2.2"))

    results = await repo.list_by_source_ip("1.1.1.1")
    assert len(results) == 2
    assert all(e.source_ip == "1.1.1.1" for e in results)


async def test_list_recent_with_explicit_since(db_session: AsyncSession) -> None:
    from datetime import timedelta

    repo = EventRepository(db_session)
    now = datetime.now(UTC)
    await repo.create(_make_event(occurred_at=now - timedelta(hours=1)))
    await repo.create(_make_event(occurred_at=now - timedelta(hours=5)))

    results = await repo.list_recent(limit=10, since=now - timedelta(hours=2))
    assert len(results) == 1


async def test_list_by_ip_empty_when_no_match(db_session: AsyncSession) -> None:
    repo = EventRepository(db_session)
    results = await repo.list_by_source_ip("9.9.9.9")
    assert results == []


async def test_list_recent_returns_ordered_by_occurred_at(db_session: AsyncSession) -> None:
    from datetime import timedelta

    repo = EventRepository(db_session)
    now = datetime.now(UTC)
    t1 = now - timedelta(hours=3)
    t2 = now - timedelta(hours=1)
    t3 = now - timedelta(hours=2)
    await repo.create(_make_event(occurred_at=t1))
    await repo.create(_make_event(occurred_at=t2))
    await repo.create(_make_event(occurred_at=t3))

    results = await repo.list_recent(limit=3)
    assert len(results) == 3
    assert results[0].occurred_at >= results[1].occurred_at >= results[2].occurred_at
