from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.threat_indicator import IndicatorType, ThreatIndicator


class IndicatorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, indicator: ThreatIndicator) -> ThreatIndicator:
        self.session.add(indicator)
        await self.session.flush()
        return indicator

    async def get_by_id(self, indicator_id: uuid.UUID) -> ThreatIndicator | None:
        return await self.session.get(ThreatIndicator, indicator_id)

    async def get_by_value(self, value: str) -> ThreatIndicator | None:
        result = await self.session.execute(
            select(ThreatIndicator).where(ThreatIndicator.indicator_value == value)
        )
        return result.scalar_one_or_none()

    async def list_active(
        self,
        *,
        indicator_type: IndicatorType | None = None,
        limit: int = 100,
    ) -> list[ThreatIndicator]:
        stmt = select(ThreatIndicator).where(ThreatIndicator.is_active.is_(True))
        if indicator_type is not None:
            stmt = stmt.where(ThreatIndicator.indicator_type == indicator_type)
        stmt = stmt.order_by(ThreatIndicator.risk_score.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
