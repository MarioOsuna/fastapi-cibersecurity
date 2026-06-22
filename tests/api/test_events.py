from httpx import AsyncClient


async def test_ingest_event_returns_201(async_client: AsyncClient) -> None:
    payload = {
        "source_ip": "10.0.0.1",
        "event_type": "port_scan",
        "severity": "high",
        "raw_payload": {"port": 443},
        "occurred_at": "2026-06-15T12:00:00Z",
    }
    response = await async_client.post("/api/v1/events", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["source_ip"] == "10.0.0.1"
    assert body["event_type"] == "port_scan"
    assert body["severity"] == "high"
    assert "id" in body
    assert "created_at" in body


async def test_ingest_event_defaults_occurred_at(async_client: AsyncClient) -> None:
    payload = {
        "source_ip": "10.0.0.2",
        "event_type": "login_failure",
        "severity": "low",
    }
    response = await async_client.post("/api/v1/events", json=payload)
    assert response.status_code == 201
    assert response.json()["occurred_at"] is not None


async def test_ingest_event_invalid_type_returns_422(async_client: AsyncClient) -> None:
    payload = {
        "source_ip": "10.0.0.1",
        "event_type": "not_a_real_type",
        "severity": "low",
    }
    response = await async_client.post("/api/v1/events", json=payload)
    assert response.status_code == 422
