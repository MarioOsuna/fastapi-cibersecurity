import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Enum, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.database import Base


class EventType(enum.StrEnum):
    LOGIN_FAILURE = "login_failure"
    PORT_SCAN = "port_scan"
    BRUTE_FORCE = "brute_force"
    SUSPICIOUS_REQUEST = "suspicious_request"
    MALWARE_DETECTED = "malware_detected"


class SeverityLevel(enum.StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEvent(Base):
    __tablename__ = "security_events"
    __table_args__ = (
        Index("ix_security_events_source_ip", "source_ip"),
        Index("ix_security_events_occurred_at", "occurred_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_ip: Mapped[str] = mapped_column(String(45))  # max IPv6 length
    event_type: Mapped[EventType] = mapped_column(Enum(EventType, name="event_type_enum"))
    severity: Mapped[SeverityLevel] = mapped_column(Enum(SeverityLevel, name="severity_level_enum"))
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSON().with_variant(JSONB, "postgresql"))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
