import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class IndicatorType(enum.StrEnum):
    IP = "ip"
    DOMAIN = "domain"
    HASH = "hash"


class ThreatIndicator(Base):
    __tablename__ = "threat_indicators"
    __table_args__ = (Index("ix_threat_indicators_value", "indicator_value"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    indicator_value: Mapped[str] = mapped_column(String(512), unique=True)
    indicator_type: Mapped[IndicatorType] = mapped_column(
        Enum(IndicatorType, name="indicator_type_enum")
    )
    source: Mapped[str] = mapped_column(String(255))
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
