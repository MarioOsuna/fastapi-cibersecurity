from httpx import AsyncClient


async def test_risk_score_zero_for_unknown_ip(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/threats/192.168.99.99/score")
    assert response.status_code == 200
    body = response.json()
    assert body["source_ip"] == "192.168.99.99"
    assert body["risk_score"] == 0.0
    assert body["event_count"] == 0
    assert body["ioc_match"] is False


async def test_risk_score_after_event(async_client: AsyncClient) -> None:
    await async_client.post(
        "/api/v1/events",
        json={
            "source_ip": "10.20.30.40",
            "event_type": "brute_force",
            "severity": "critical",
        },
    )
    response = await async_client.get("/api/v1/threats/10.20.30.40/score")
    assert response.status_code == 200
    body = response.json()
    assert body["risk_score"] > 0
    assert body["event_count"] == 1


async def test_list_indicators_empty(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/threats/indicators")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["count"] == 0


async def test_list_indicators_with_type_filter(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/threats/indicators?indicator_type=ip")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["items"], list)
    assert isinstance(body["count"], int)
