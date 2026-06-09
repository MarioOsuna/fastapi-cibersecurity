import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.threat_indicator import IndicatorType, ThreatIndicator


def _make_indicator(
    value: str = "192.168.1.100",
    indicator_type: IndicatorType = IndicatorType.IP,
    risk_score: float = 75.0,
) -> ThreatIndicator:
    now = datetime.now(UTC)
    return ThreatIndicator(
        indicator_value=value,
        indicator_type=indicator_type,
        source="threat-feed-alpha",
        risk_score=risk_score,
        first_seen=now,
        last_seen=now,
    )


async def test_threat_indicator_create(db_session: AsyncSession) -> None:
    indicator = _make_indicator()
    db_session.add(indicator)
    await db_session.flush()

    assert isinstance(indicator.id, uuid.UUID)
    assert indicator.indicator_value == "192.168.1.100"
    assert indicator.indicator_type == IndicatorType.IP
    assert indicator.risk_score == 75.0
    assert indicator.is_active is True
    assert indicator.created_at is not None


async def test_threat_indicator_defaults(db_session: AsyncSession) -> None:
    indicator = _make_indicator(risk_score=0.0)
    db_session.add(indicator)
    await db_session.flush()

    assert indicator.is_active is True
    assert indicator.risk_score == 0.0


async def test_threat_indicator_unique_value(db_session: AsyncSession) -> None:
    db_session.add(_make_indicator("evil.example.com", IndicatorType.DOMAIN))
    await db_session.flush()

    # Use a savepoint so the outer transaction stays valid after the expected error.
    with pytest.raises(Exception):  # noqa: B017
        async with db_session.begin_nested():
            db_session.add(_make_indicator("evil.example.com", IndicatorType.DOMAIN))
            await db_session.flush()


@pytest.mark.parametrize("itype", list(IndicatorType))
async def test_all_indicator_types(db_session: AsyncSession, itype: IndicatorType) -> None:
    indicator = _make_indicator(f"test-value-{itype.value}", itype)
    db_session.add(indicator)
    await db_session.flush()
    assert indicator.indicator_type == itype
