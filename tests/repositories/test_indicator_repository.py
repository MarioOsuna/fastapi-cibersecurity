import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.threat_indicator import IndicatorType, ThreatIndicator
from app.repositories.indicator_repository import IndicatorRepository


def _make_indicator(
    value: str = "192.168.1.100",
    indicator_type: IndicatorType = IndicatorType.IP,
    risk_score: float = 50.0,
    is_active: bool = True,
) -> ThreatIndicator:
    now = datetime.now(UTC)
    return ThreatIndicator(
        indicator_value=value,
        indicator_type=indicator_type,
        source="test-feed",
        risk_score=risk_score,
        is_active=is_active,
        first_seen=now,
        last_seen=now,
    )


async def test_create_returns_indicator_with_id(db_session: AsyncSession) -> None:
    repo = IndicatorRepository(db_session)
    indicator = await repo.create(_make_indicator())
    assert isinstance(indicator.id, uuid.UUID)
    assert indicator.indicator_value == "192.168.1.100"


async def test_get_by_id_found(db_session: AsyncSession) -> None:
    repo = IndicatorRepository(db_session)
    created = await repo.create(_make_indicator())
    fetched = await repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id


async def test_get_by_id_not_found(db_session: AsyncSession) -> None:
    repo = IndicatorRepository(db_session)
    result = await repo.get_by_id(uuid.uuid4())
    assert result is None


async def test_get_by_value_found(db_session: AsyncSession) -> None:
    repo = IndicatorRepository(db_session)
    await repo.create(_make_indicator("evil.example.com", IndicatorType.DOMAIN))
    fetched = await repo.get_by_value("evil.example.com")
    assert fetched is not None
    assert fetched.indicator_value == "evil.example.com"


async def test_get_by_value_not_found(db_session: AsyncSession) -> None:
    repo = IndicatorRepository(db_session)
    result = await repo.get_by_value("unknown.host")
    assert result is None


async def test_list_active_excludes_inactive(db_session: AsyncSession) -> None:
    repo = IndicatorRepository(db_session)
    await repo.create(_make_indicator("active.host", is_active=True))
    await repo.create(_make_indicator("inactive.host", is_active=False))

    results = await repo.list_active()
    values = [r.indicator_value for r in results]
    assert "active.host" in values
    assert "inactive.host" not in values


async def test_list_active_ordered_by_risk_score_desc(db_session: AsyncSession) -> None:
    repo = IndicatorRepository(db_session)
    await repo.create(_make_indicator("low.host", risk_score=10.0))
    await repo.create(_make_indicator("high.host", risk_score=90.0))
    await repo.create(_make_indicator("mid.host", risk_score=50.0))

    results = await repo.list_active()
    scores = [r.risk_score for r in results]
    assert scores == sorted(scores, reverse=True)
