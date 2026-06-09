from datetime import UTC, datetime

from app.schemas.health import HealthResponse, ReadinessResponse


def test_health_response_fields() -> None:
    resp = HealthResponse(
        status="ok",
        version="0.1.0",
        environment="development",
        timestamp=datetime.now(UTC),
    )
    assert resp.status == "ok"
    assert resp.version == "0.1.0"
    assert resp.environment == "development"


def test_readiness_response_ok() -> None:
    resp = ReadinessResponse(
        status="ok",
        checks={"database": "ok", "redis": "ok"},
    )
    assert resp.status == "ok"
    assert resp.checks["database"] == "ok"
    assert resp.checks["redis"] == "ok"


def test_readiness_response_degraded() -> None:
    resp = ReadinessResponse(
        status="degraded",
        checks={"database": "ok", "redis": "error: Connection refused"},
    )
    assert resp.status == "degraded"
    assert resp.checks["redis"].startswith("error:")
