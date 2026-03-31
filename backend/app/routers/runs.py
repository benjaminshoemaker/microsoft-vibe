import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Run, Event
from app.schemas import (
    RunResponse,
    RunListResponse,
    RunStatsResponse,
    RunDetailResponse,
    EventResponse,
)

router = APIRouter(prefix="/api/v1", tags=["runs"])


def _run_to_response(run: Run) -> RunResponse:
    return RunResponse(
        id=run.id,
        agent_name=run.agent_name,
        status=run.status,
        started_at=run.started_at,
        ended_at=run.ended_at,
        duration_ms=run.duration_ms,
        step_count=run.step_count,
        error_message=run.error_message,
        metadata=run.metadata_ or {},
    )


@router.get("/runs", response_model=RunListResponse)
async def get_runs(
    agent_name: str | None = None,
    status: str | None = None,
    time_start: datetime | None = None,
    time_end: datetime | None = None,
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    sort: str = "-started_at",
    db: AsyncSession = Depends(get_db),
) -> RunListResponse:
    query = select(Run)
    count_query = select(func.count()).select_from(Run)

    # Filters
    if agent_name:
        query = query.where(Run.agent_name == agent_name)
        count_query = count_query.where(Run.agent_name == agent_name)
    if status:
        query = query.where(Run.status == status)
        count_query = count_query.where(Run.status == status)
    if time_start:
        query = query.where(Run.started_at >= time_start)
        count_query = count_query.where(Run.started_at >= time_start)
    if time_end:
        query = query.where(Run.started_at <= time_end)
        count_query = count_query.where(Run.started_at <= time_end)
    if search:
        pattern = f"%{search}%"
        search_filter = Run.search_vector.ilike(pattern) | Run.error_message.ilike(pattern)
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Sorting
    if sort.startswith("-"):
        col = getattr(Run, sort[1:], Run.started_at)
        query = query.order_by(desc(col))
    else:
        col = getattr(Run, sort, Run.started_at)
        query = query.order_by(asc(col))

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    runs = result.scalars().all()
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    return RunListResponse(
        runs=[_run_to_response(r) for r in runs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/runs/stats", response_model=RunStatsResponse)
async def get_run_stats(
    agent_name: str | None = None,
    status: str | None = None,
    time_start: datetime | None = None,
    time_end: datetime | None = None,
    db: AsyncSession = Depends(get_db),
) -> RunStatsResponse:
    if not time_start:
        time_start = datetime.now(timezone.utc) - timedelta(hours=24)
    if not time_end:
        time_end = datetime.now(timezone.utc)

    base = select(Run).where(Run.started_at >= time_start, Run.started_at <= time_end)
    if agent_name:
        base = base.where(Run.agent_name == agent_name)

    result = await db.execute(base)
    runs = result.scalars().all()

    total = len(runs)
    success = sum(1 for r in runs if r.status == "success")
    failures = sum(1 for r in runs if r.status in ("failure", "error"))
    durations = [r.duration_ms for r in runs if r.duration_ms is not None]

    return RunStatsResponse(
        total_runs=total,
        success_count=success,
        failure_count=failures,
        failure_rate=round(failures / total * 100, 1) if total > 0 else 0,
        avg_duration_ms=round(sum(durations) / len(durations)) if durations else 0,
        time_window={"start": time_start.isoformat(), "end": time_end.isoformat()},
    )


def _build_event_tree(events: list[Event], run: Run) -> list[EventResponse]:
    """Build nested event tree from flat list using parent_step_id."""
    event_map: dict[uuid.UUID, EventResponse] = {}
    roots: list[EventResponse] = []

    # Sort by timestamp
    sorted_events = sorted(events, key=lambda e: e.timestamp)

    # First pass: create EventResponse objects
    for evt in sorted_events:
        resp = EventResponse(
            id=evt.id,
            step_id=evt.step_id,
            parent_step_id=evt.parent_step_id,
            step_type=evt.step_type,
            step_name=evt.step_name,
            input=evt.input or {},
            output=evt.output or {},
            status=evt.status,
            error_message=evt.error_message,
            timestamp=evt.timestamp,
            duration_ms=None,
            metadata=evt.metadata_ or {},
            children=[],
        )
        event_map[evt.step_id] = resp

    # Second pass: compute durations and build tree
    for i, evt in enumerate(sorted_events):
        resp = event_map[evt.step_id]

        # Compute duration_ms
        if evt.step_id in event_map:
            children = [e for e in sorted_events if e.parent_step_id == evt.step_id]
            if children:
                last_child = max(children, key=lambda c: c.timestamp)
                delta = last_child.timestamp - evt.timestamp
                resp.duration_ms = int(delta.total_seconds() * 1000)
            elif i + 1 < len(sorted_events) and sorted_events[i + 1].parent_step_id == evt.parent_step_id:
                delta = sorted_events[i + 1].timestamp - evt.timestamp
                resp.duration_ms = int(delta.total_seconds() * 1000)
            elif run.ended_at:
                delta = run.ended_at - evt.timestamp
                resp.duration_ms = int(delta.total_seconds() * 1000)

        if evt.parent_step_id and evt.parent_step_id in event_map:
            event_map[evt.parent_step_id].children.append(resp)
        else:
            roots.append(resp)

    return roots


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
async def get_run_detail(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> RunDetailResponse:
    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    events_result = await db.execute(
        select(Event).where(Event.run_id == run_id).order_by(Event.timestamp)
    )
    events = events_result.scalars().all()

    return RunDetailResponse(
        run=_run_to_response(run),
        events=_build_event_tree(list(events), run),
    )
