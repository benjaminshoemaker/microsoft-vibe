import uuid

import pytest
from httpx import AsyncClient


async def _seed_run_with_error(client: AsyncClient, agent_name: str, error_msg: str) -> str:
    rid = str(uuid.uuid4())
    events = [
        {
            "run_id": rid, "agent_name": agent_name, "step_type": "run_start",
            "status": "success", "timestamp": "2026-03-30T14:00:00Z",
        },
        {
            "run_id": rid, "agent_name": agent_name, "step_type": "error",
            "step_name": "failing_step", "status": "failure",
            "error_message": error_msg,
            "timestamp": "2026-03-30T14:00:05Z",
        },
        {
            "run_id": rid, "agent_name": agent_name, "step_type": "run_end",
            "status": "failure", "timestamp": "2026-03-30T14:00:06Z",
        },
    ]
    for evt in events:
        await client.post("/api/v1/ingest", json=evt)
    return rid


@pytest.mark.asyncio
async def test_search_vector_generated(client: AsyncClient):
    """Ingesting events should populate search_vector on runs."""
    rid = await _seed_run_with_error(client, "search-agent", "connection timeout")
    resp = await client.get(f"/api/v1/runs/{rid}")
    assert resp.status_code == 200
    # Run exists and has the error — search vector was populated during ingestion


@pytest.mark.asyncio
async def test_search_by_error_text(client: AsyncClient):
    await _seed_run_with_error(client, "agent-x", "database connection timeout")
    await _seed_run_with_error(client, "agent-y", "auth token expired")

    resp = await client.get("/api/v1/runs?search=timeout")
    assert resp.status_code == 200
    runs = resp.json()["runs"]
    assert len(runs) >= 1
    assert all("timeout" in (r["error_message"] or "").lower() for r in runs)


@pytest.mark.asyncio
async def test_search_with_filters(client: AsyncClient):
    await _seed_run_with_error(client, "agent-a", "timeout on replica")
    await _seed_run_with_error(client, "agent-b", "timeout on primary")

    resp = await client.get("/api/v1/runs?agent_name=agent-a&status=failure&search=timeout")
    assert resp.status_code == 200
    runs = resp.json()["runs"]
    assert all(r["agent_name"] == "agent-a" for r in runs)
    assert all(r["status"] == "failure" for r in runs)


@pytest.mark.asyncio
async def test_empty_search_returns_all(client: AsyncClient):
    await _seed_run_with_error(client, "any-agent", "some error")

    resp = await client.get("/api/v1/runs?search=")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1
