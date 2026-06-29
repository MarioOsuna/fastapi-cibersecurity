from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.threat_indicator import IndicatorType


class IndicatorCreate(BaseModel):
    indicator_value: str
    indicator_type: IndicatorType
    source: str
    risk_score: float = 0.0
    is_active: bool = True


class RiskScoreResponse(BaseModel):
    source_ip: str
    risk_score: float
    event_count: int
    ioc_match: bool
    severity_points: float
    ioc_points: float


class IndicatorResponse(BaseModel):
    id: uuid.UUID
    indicator_value: str
    indicator_type: IndicatorType
    source: str
    risk_score: float
    is_active: bool
    first_seen: datetime
    last_seen: datetime

    model_config = {"from_attributes": True}


class IndicatorListResponse(BaseModel):
    items: list[IndicatorResponse]
    count: int
