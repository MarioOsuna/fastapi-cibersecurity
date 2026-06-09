from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
    environment: str
    timestamp: datetime


class ReadinessResponse(BaseModel):
    status: Literal["ok", "degraded"]
    checks: dict[str, str]
