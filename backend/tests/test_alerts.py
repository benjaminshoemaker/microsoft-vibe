import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_failure_rate_rule(client: AsyncClient):
    payload = {
        "agent_name": "test-agent",
        "metric": "failure_rate",
        "threshold_value": 10.0,
        "window_minutes": 60,
    }
    resp = await client.post("/api/v1/alerts/rules", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["agent_name"] == "test-agent"
    assert data["metric"] == "failure_rate"
    assert data["threshold_value"] == 10.0
    assert data["enabled"] is True


@pytest.mark.asyncio
async def test_create_stuck_run_rule(client: AsyncClient):
    payload = {
        "agent_name": "pipeline",
        "metric": "stuck_run",
        "multiplier": 3.0,
        "window_minutes": 60,
    }
    resp = await client.post("/api/v1/alerts/rules", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["metric"] == "stuck_run"
    assert data["multiplier"] == 3.0


@pytest.mark.asyncio
async def test_list_rules(client: AsyncClient):
    await client.post("/api/v1/alerts/rules", json={
        "agent_name": "a", "metric": "failure_rate", "threshold_value": 5, "window_minutes": 30,
    })
    resp = await client.get("/api/v1/alerts/rules")
    assert resp.status_code == 200
    assert len(resp.json()["rules"]) >= 1


@pytest.mark.asyncio
async def test_update_rule(client: AsyncClient):
    create_resp = await client.post("/api/v1/alerts/rules", json={
        "agent_name": "upd", "metric": "p95_latency", "threshold_value": 5000, "window_minutes": 60,
    })
    rule_id = create_resp.json()["id"]

    resp = await client.put(f"/api/v1/alerts/rules/{rule_id}", json={
        "threshold_value": 8000.0, "enabled": False,
    })
    assert resp.status_code == 200
    assert resp.json()["threshold_value"] == 8000.0
    assert resp.json()["enabled"] is False


@pytest.mark.asyncio
async def test_delete_rule(client: AsyncClient):
    create_resp = await client.post("/api/v1/alerts/rules", json={
        "agent_name": "del", "metric": "failure_rate", "threshold_value": 50, "window_minutes": 60,
    })
    rule_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/alerts/rules/{rule_id}")
    assert resp.status_code == 204

    # Confirm deleted
    get_resp = await client.get("/api/v1/alerts/rules")
    ids = [r["id"] for r in get_resp.json()["rules"]]
    assert rule_id not in ids


@pytest.mark.asyncio
async def test_alert_history(client: AsyncClient):
    resp = await client.get("/api/v1/alerts/history")
    assert resp.status_code == 200
    assert "alerts" in resp.json()
    assert "total" in resp.json()


@pytest.mark.asyncio
async def test_update_nonexistent_rule(client: AsyncClient):
    resp = await client.put("/api/v1/alerts/rules/99999", json={"enabled": False})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_rule(client: AsyncClient):
    resp = await client.delete("/api/v1/alerts/rules/99999")
    assert resp.status_code == 404
