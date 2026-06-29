from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_indicator_repo, get_scoring_service
from app.models.threat_indicator import IndicatorType, ThreatIndicator
from app.repositories.indicator_repository import IndicatorRepository
from app.schemas.threats import (
    IndicatorCreate,
    IndicatorListResponse,
    IndicatorResponse,
    RiskScoreResponse,
)
from app.services.scoring import ScoringService

router = APIRouter(prefix="/api/v1/threats", tags=["threats"])


@router.get("/{ip}/score", response_model=RiskScoreResponse)
async def get_risk_score(
    ip: str,
    service: Annotated[ScoringService, Depends(get_scoring_service)],
) -> RiskScoreResponse:
    result = await service.calculate_risk(ip)
    return RiskScoreResponse(
        source_ip=ip,
        risk_score=result.total,
        event_count=result.event_count,
        ioc_match=result.ioc_match,
        severity_points=result.severity_points,
        ioc_points=result.ioc_points,
    )


@router.post("/indicators", response_model=IndicatorResponse, status_code=status.HTTP_201_CREATED)
async def create_indicator(
    body: IndicatorCreate,
    repo: Annotated[IndicatorRepository, Depends(get_indicator_repo)],
) -> IndicatorResponse:
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    indicator = ThreatIndicator(
        indicator_value=body.indicator_value,
        indicator_type=body.indicator_type,
        source=body.source,
        risk_score=body.risk_score,
        is_active=body.is_active,
        first_seen=now,
        last_seen=now,
    )
    created = await repo.create(indicator)
    return IndicatorResponse.model_validate(created)


@router.get("/indicators", response_model=IndicatorListResponse)
async def list_indicators(
    repo: Annotated[IndicatorRepository, Depends(get_indicator_repo)],
    indicator_type: Annotated[IndicatorType | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> IndicatorListResponse:
    items = await repo.list_active(indicator_type=indicator_type, limit=limit)
    return IndicatorListResponse(
        items=[IndicatorResponse.model_validate(i) for i in items],
        count=len(items),
    )
