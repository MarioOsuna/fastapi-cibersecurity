from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_event import EventType, SecurityEvent, SeverityLevel
from app.models.threat_indicator import IndicatorType, ThreatIndicator
from app.repositories.event_repository import EventRepository
from app.repositories.indicator_repository import IndicatorRepository
from app.services.scoring import SEVERITY_WEIGHTS, ScoringService


def _make_event(
    source_ip: str = "10.0.0.1",
    severity: SeverityLevel = SeverityLevel.LOW,
    event_type: EventType = EventType.LOGIN_FAILURE,
    occurred_at: datetime | None = None,
) -> SecurityEvent:
    return SecurityEvent(
        source_ip=source_ip,
        event_type=event_type,
        severity=severity,
        raw_payload={},
        occurred_at=occurred_at or datetime.now(UTC),
    )


def _make_indicator(
    value: str = "10.0.0.1",
    risk_score: float = 50.0,
) -> ThreatIndicator:
    now = datetime.now(UTC)
    return ThreatIndicator(
        indicator_value=value,
        indicator_type=IndicatorType.IP,
        source="test-feed",
        risk_score=risk_score,
        is_active=True,
        first_seen=now,
        last_seen=now,
    )


async def test_score_zero_when_no_events(db_session: AsyncSession) -> None:
    service = ScoringService(EventRepository(db_session), IndicatorRepository(db_session))
    result = await service.calculate_risk("192.168.99.99")
    assert result.total == 0.0
    assert result.event_count == 0
    assert result.ioc_match is False


async def test_score_from_severity_weights(db_session: AsyncSession) -> None:
    event_repo = EventRepository(db_session)
    await event_repo.create(_make_event(severity=SeverityLevel.HIGH))
    await event_repo.create(_make_event(severity=SeverityLevel.LOW))

    service = ScoringService(event_repo, IndicatorRepository(db_session))
    result = await service.calculate_risk("10.0.0.1")

    expected = SEVERITY_WEIGHTS[SeverityLevel.HIGH] + SEVERITY_WEIGHTS[SeverityLevel.LOW]
    assert result.severity_points == expected
    assert result.total == expected
    assert result.event_count == 2


async def test_ioc_match_adds_points(db_session: AsyncSession) -> None:
    event_repo = EventRepository(db_session)
    indicator_repo = IndicatorRepository(db_session)

    await event_repo.create(_make_event(severity=SeverityLevel.LOW))
    await indicator_repo.create(_make_indicator("10.0.0.1", risk_score=30.0))

    service = ScoringService(event_repo, indicator_repo)
    result = await service.calculate_risk("10.0.0.1")

    assert result.ioc_match is True
    assert result.ioc_points == 30.0
    assert result.total == SEVERITY_WEIGHTS[SeverityLevel.LOW] + 30.0


async def test_score_capped_at_100(db_session: AsyncSession) -> None:
    event_repo = EventRepository(db_session)
    indicator_repo = IndicatorRepository(db_session)

    for _ in range(5):
        await event_repo.create(_make_event(severity=SeverityLevel.CRITICAL))
    await indicator_repo.create(_make_indicator("10.0.0.1", risk_score=80.0))

    service = ScoringService(event_repo, indicator_repo)
    result = await service.calculate_risk("10.0.0.1")

    assert result.total == 100.0


async def test_old_events_excluded(db_session: AsyncSession) -> None:
    event_repo = EventRepository(db_session)
    old_time = datetime.now(UTC) - timedelta(hours=48)
    await event_repo.create(_make_event(occurred_at=old_time))

    service = ScoringService(event_repo, IndicatorRepository(db_session))
    result = await service.calculate_risk("10.0.0.1")

    assert result.event_count == 0
    assert result.total == 0.0
