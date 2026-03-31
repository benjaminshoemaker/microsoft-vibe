import uuid

import pytest
from httpx import AsyncClient

RUN_ID = str(uuid.uuid4())
AGENT_NAME = "test-agent"


def make_event(**overrides):
    base = {
        "run_id": RUN_ID,
        "agent_name": AGENT_NAME,
        "step_type": "tool_call",
        "step_name": "test_step",
        "status": "success",
        "timestamp": "2026-03-30T14:00:00Z",
        "input": {"key": "value"},
        "output": {"result": "ok"},
        "metadata": {"env": "test"},
    }
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_ingest_single_event(client: AsyncClient):
    event = make_event(step_type="run_start")
    resp = await client.post("/api/v1/ingest", json=event)
    assert resp.status_code == 201
    data = resp.json()
    assert data["accepted"] == 1
    assert data["errors"] == []


@pytest.mark.asyncio
async def test_ingest_batch(client: AsyncClient):
    events = [
        make_event(step_type="run_start", run_id=str(uuid.uuid4())),
        make_event(step_type="tool_call", run_id=str(uuid.uuid4())),
    ]
    resp = await client.post("/api/v1/ingest", json={"events": events})
    assert resp.status_code == 201
    data = resp.json()
    assert data["accepted"] == 2


@pytest.mark.asyncio
async def test_ingest_invalid_step_type(client: AsyncClient):
    event = make_event(step_type="invalid_type")
    resp = await client.post("/api/v1/ingest", json=event)
    assert resp.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_ingest_metadata(client: AsyncClient):
    event = make_event(
        run_id=str(uuid.uuid4()),
        step_type="run_start",
        metadata={"version": "1.0", "environment": "production"},
    )
    resp = await client.post("/api/v1/ingest", json=event)
    assert resp.status_code == 201
    assert resp.json()["accepted"] == 1


@pytest.mark.asyncio
async def test_ingest_run_start_creates_run(client: AsyncClient):
    rid = str(uuid.uuid4())
    event = make_event(run_id=rid, step_type="run_start")
    resp = await client.post("/api/v1/ingest", json=event)
    assert resp.status_code == 201
    assert resp.json()["accepted"] == 1


@pytest.mark.asyncio
async def test_ingest_run_end_finalizes_run(client: AsyncClient):
    rid = str(uuid.uuid4())
    start = make_event(run_id=rid, step_type="run_start", timestamp="2026-03-30T14:00:00Z")
    end = make_event(run_id=rid, step_type="run_end", timestamp="2026-03-30T14:00:30Z")

    await client.post("/api/v1/ingest", json=start)
    resp = await client.post("/api/v1/ingest", json=end)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_ingest_duplicate_idempotent(client: AsyncClient):
    step_id = str(uuid.uuid4())
    rid = str(uuid.uuid4())
    event = make_event(run_id=rid, step_type="run_start", step_id=step_id)

    resp1 = await client.post("/api/v1/ingest", json=event)
    assert resp1.status_code == 201
    assert resp1.json()["accepted"] == 1

    resp2 = await client.post("/api/v1/ingest", json=event)
    assert resp2.status_code == 201
    # Second attempt is idempotent — accepted count is still 1 (no error, no duplicate)


@pytest.mark.asyncio
async def test_ingest_error_event_updates_run(client: AsyncClient):
    rid = str(uuid.uuid4())
    start = make_event(run_id=rid, step_type="run_start")
    error = make_event(
        run_id=rid,
        step_type="error",
        status="error",
        error_message="Something went wrong",
    )

    await client.post("/api/v1/ingest", json=start)
    resp = await client.post("/api/v1/ingest", json=error)
    assert resp.status_code == 201
