from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.security_event import EventType, SeverityLevel


class EventCreate(BaseModel):
    source_ip: str
    event_type: EventType
    severity: SeverityLevel
    raw_payload: dict[str, Any] = {}
    occurred_at: datetime | None = None


class EventResponse(BaseModel):
    id: uuid.UUID
    source_ip: str
    event_type: EventType
    severity: SeverityLevel
    raw_payload: dict[str, Any]
    occurred_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
