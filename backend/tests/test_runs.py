import uuid

import pytest
from httpx import AsyncClient


async def _seed_run(client: AsyncClient, agent_name: str = "test-agent", status: str = "success") -> str:
    rid = str(uuid.uuid4())
    start = {
        "run_id": rid,
        "agent_name": agent_name,
        "step_type": "run_start",
        "status": "success",
        "timestamp": "2026-03-30T14:00:00Z",
    }
    await client.post("/api/v1/ingest", json=start)

    # Add a tool call step
    step = {
        "run_id": rid,
        "agent_name": agent_name,
        "step_type": "tool_call",
        "step_name": "do_thing",
        "status": "success",
        "timestamp": "2026-03-30T14:00:05Z",
        "input": {"x": 1},
        "output": {"y": 2},
    }
    await client.post("/api/v1/ingest", json=step)

    end_status = status if status != "running" else "success"
    if status != "running":
        end = {
            "run_id": rid,
            "agent_name": agent_name,
            "step_type": "run_end",
            "status": end_status,
            "timestamp": "2026-03-30T14:00:30Z",
        }
        await client.post("/api/v1/ingest", json=end)

    return rid


@pytest.mark.asyncio
async def test_list_runs_paginated(client: AsyncClient):
    await _seed_run(client)
    await _seed_run(client)

    resp = await client.get("/api/v1/runs")
    assert resp.status_code == 200
    data = resp.json()
    assert "runs" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert data["total"] >= 2


@pytest.mark.asyncio
async def test_list_runs_filter_agent(client: AsyncClient):
    await _seed_run(client, agent_name="agent-a")
    await _seed_run(client, agent_name="agent-b")

    resp = await client.get("/api/v1/runs?agent_name=agent-a")
    assert resp.status_code == 200
    runs = resp.json()["runs"]
    assert all(r["agent_name"] == "agent-a" for r in runs)


@pytest.mark.asyncio
async def test_list_runs_filter_status(client: AsyncClient):
    await _seed_run(client, status="success")
    await _seed_run(client, status="failure")

    resp = await client.get("/api/v1/runs?status=failure")
    assert resp.status_code == 200
    runs = resp.json()["runs"]
    assert all(r["status"] == "failure" for r in runs)


@pytest.mark.asyncio
async def test_run_stats(client: AsyncClient):
    await _seed_run(client, status="success")
    await _seed_run(client, status="failure")

    resp = await client.get("/api/v1/runs/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_runs" in data
    assert "success_count" in data
    assert "failure_count" in data
    assert "failure_rate" in data
    assert "avg_duration_ms" in data


@pytest.mark.asyncio
async def test_list_agents(client: AsyncClient):
    await _seed_run(client, agent_name="alpha")
    await _seed_run(client, agent_name="beta")

    resp = await client.get("/api/v1/agents")
    assert resp.status_code == 200
    agents = resp.json()["agents"]
    names = [a["name"] for a in agents]
    assert "alpha" in names
    assert "beta" in names
    for a in agents:
        assert "first_seen_at" in a
        assert "last_seen_at" in a
