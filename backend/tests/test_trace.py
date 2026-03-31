import uuid

import pytest
from httpx import AsyncClient


async def _seed_run_with_trace(client: AsyncClient) -> str:
    rid = str(uuid.uuid4())
    parent_step = str(uuid.uuid4())
    child_step = str(uuid.uuid4())

    events = [
        {
            "run_id": rid, "agent_name": "trace-agent", "step_type": "run_start",
            "status": "success", "timestamp": "2026-03-30T14:00:00Z",
        },
        {
            "run_id": rid, "agent_name": "trace-agent", "step_type": "decision",
            "step_id": parent_step, "step_name": "route_request",
            "status": "success", "timestamp": "2026-03-30T14:00:01Z",
            "input": {"intent": "reset"}, "output": {"handler": "reset_flow"},
        },
        {
            "run_id": rid, "agent_name": "trace-agent", "step_type": "tool_call",
            "step_id": child_step, "parent_step_id": parent_step,
            "step_name": "lookup_user", "status": "success",
            "timestamp": "2026-03-30T14:00:02Z",
            "input": {"user": "jane"}, "output": {"found": True},
        },
        {
            "run_id": rid, "agent_name": "trace-agent", "step_type": "error",
            "step_name": "send_email", "status": "failure",
            "error_message": "SMTP timeout after 5s",
            "timestamp": "2026-03-30T14:00:05Z",
        },
        {
            "run_id": rid, "agent_name": "trace-agent", "step_type": "run_end",
            "status": "failure", "timestamp": "2026-03-30T14:00:06Z",
        },
    ]

    for evt in events:
        resp = await client.post("/api/v1/ingest", json=evt)
        assert resp.status_code == 201

    return rid


@pytest.mark.asyncio
async def test_get_run_detail(client: AsyncClient):
    rid = await _seed_run_with_trace(client)
    resp = await client.get(f"/api/v1/runs/{rid}")
    assert resp.status_code == 200
    data = resp.json()
    assert "run" in data
    assert "events" in data
    assert data["run"]["agent_name"] == "trace-agent"
    assert data["run"]["status"] == "failure"


@pytest.mark.asyncio
async def test_nested_events(client: AsyncClient):
    rid = await _seed_run_with_trace(client)
    resp = await client.get(f"/api/v1/runs/{rid}")
    events = resp.json()["events"]

    # Find the decision event (parent)
    decision = next((e for e in events if e["step_name"] == "route_request"), None)
    assert decision is not None
    assert len(decision["children"]) == 1
    assert decision["children"][0]["step_name"] == "lookup_user"


@pytest.mark.asyncio
async def test_event_duration_computed(client: AsyncClient):
    rid = await _seed_run_with_trace(client)
    resp = await client.get(f"/api/v1/runs/{rid}")
    events = resp.json()["events"]

    # At least one event should have a non-null duration
    durations = [e["duration_ms"] for e in events if e["duration_ms"] is not None]
    assert len(durations) > 0


@pytest.mark.asyncio
async def test_run_not_found(client: AsyncClient):
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/runs/{fake_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_events_ordered_by_timestamp(client: AsyncClient):
    rid = await _seed_run_with_trace(client)
    resp = await client.get(f"/api/v1/runs/{rid}")
    events = resp.json()["events"]

    timestamps = [e["timestamp"] for e in events]
    assert timestamps == sorted(timestamps)
