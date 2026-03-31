import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, Event, Run
from app.schemas import IngestEvent


async def upsert_agent(db: AsyncSession, agent_name: str, event_time: datetime) -> None:
    result = await db.execute(select(Agent).where(Agent.name == agent_name))
    agent = result.scalar_one_or_none()
    if agent is None:
        agent = Agent(name=agent_name, first_seen_at=event_time, last_seen_at=event_time)
        db.add(agent)
    else:
        agent.last_seen_at = event_time


async def get_or_create_run(db: AsyncSession, run_id: uuid.UUID, agent_name: str, event_time: datetime) -> Run:
    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        run = Run(
            id=run_id,
            agent_name=agent_name,
            status="running",
            started_at=event_time,
            step_count=0,
            metadata_={},
            created_at=datetime.now(timezone.utc),
        )
        db.add(run)
    return run


async def process_event(db: AsyncSession, payload: IngestEvent) -> None:
    await upsert_agent(db, payload.agent_name, payload.timestamp)

    run = await get_or_create_run(db, payload.run_id, payload.agent_name, payload.timestamp)

    step_id = payload.step_id or uuid.uuid4()

    # Check for duplicate step_id
    existing = await db.execute(select(Event).where(Event.step_id == step_id))
    if existing.scalar_one_or_none() is not None:
        return  # Idempotent — skip duplicate

    event = Event(
        id=uuid.uuid4(),
        run_id=payload.run_id,
        step_id=step_id,
        parent_step_id=payload.parent_step_id,
        agent_name=payload.agent_name,
        step_type=payload.step_type.value,
        step_name=payload.step_name,
        input=payload.input,
        output=payload.output,
        status=payload.status.value,
        error_message=payload.error_message,
        timestamp=payload.timestamp,
        metadata_=payload.metadata,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)

    # Run materialization
    if payload.step_type.value == "run_start":
        run.started_at = payload.timestamp
        run.status = "running"
    elif payload.step_type.value == "run_end":
        run.ended_at = payload.timestamp
        run.status = payload.status.value
        if run.started_at and run.ended_at:
            delta = run.ended_at - run.started_at
            run.duration_ms = int(delta.total_seconds() * 1000)
    elif payload.step_type.value == "error":
        run.error_message = payload.error_message
        if payload.status.value in ("failure", "error"):
            run.status = payload.status.value

    if payload.step_type.value not in ("run_start", "run_end"):
        run.step_count += 1

    # Merge metadata
    if payload.metadata:
        merged = {**run.metadata_, **payload.metadata}
        run.metadata_ = merged

    # Update search vector (simple text concatenation for now)
    search_parts = [run.agent_name or ""]
    if run.error_message:
        search_parts.append(run.error_message)
    run.search_vector = " ".join(search_parts)
