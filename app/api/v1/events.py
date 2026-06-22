from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_event_service
from app.schemas.events import EventCreate, EventResponse
from app.services.event_service import EventService

router = APIRouter(prefix="/api/v1", tags=["events"])
logger = structlog.get_logger()


@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def ingest_event(
    body: EventCreate,
    service: Annotated[EventService, Depends(get_event_service)],
) -> EventResponse:
    event = await service.register_event(body)
    await logger.ainfo(
        "event_ingested",
        source_ip=event.source_ip,
        event_type=event.event_type,
        severity=event.severity,
    )
    return EventResponse.model_validate(event)
