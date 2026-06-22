from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.models.security_event import SeverityLevel
from app.repositories.event_repository import EventRepository
from app.repositories.indicator_repository import IndicatorRepository

SEVERITY_WEIGHTS: dict[SeverityLevel, float] = {
    SeverityLevel.LOW: 5.0,
    SeverityLevel.MEDIUM: 10.0,
    SeverityLevel.HIGH: 25.0,
    SeverityLevel.CRITICAL: 40.0,
}

WINDOW_HOURS = 24


@dataclass(frozen=True)
class RiskScore:
    total: float
    severity_points: float
    ioc_points: float
    event_count: int
    ioc_match: bool


class ScoringService:
    def __init__(
        self,
        event_repo: EventRepository,
        indicator_repo: IndicatorRepository,
    ) -> None:
        self._event_repo = event_repo
        self._indicator_repo = indicator_repo

    async def calculate_risk(self, source_ip: str) -> RiskScore:
        since = datetime.now(UTC) - timedelta(hours=WINDOW_HOURS)
        events = await self._event_repo.list_by_source_ip_since(source_ip, since=since)

        severity_points = sum(SEVERITY_WEIGHTS[e.severity] for e in events)

        ioc = await self._indicator_repo.get_by_value(source_ip)
        ioc_points = ioc.risk_score if ioc else 0.0

        total = min(severity_points + ioc_points, 100.0)

        return RiskScore(
            total=total,
            severity_points=min(severity_points, 100.0),
            ioc_points=ioc_points,
            event_count=len(events),
            ioc_match=ioc is not None,
        )
