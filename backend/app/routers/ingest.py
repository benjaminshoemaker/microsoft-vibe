from fastapi import APIRouter, Depends
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import IngestEvent, IngestBatchRequest, IngestResponse, IngestError
from app.services.ingest import process_event

router = APIRouter(prefix="/api/v1", tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse, status_code=201)
async def ingest(
    payload: IngestEvent | IngestBatchRequest,
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    if isinstance(payload, IngestEvent):
        events = [payload]
    else:
        events = payload.events

    accepted = 0
    errors: list[IngestError] = []

    for i, event in enumerate(events):
        try:
            await process_event(db, event)
            accepted += 1
        except Exception as e:
            errors.append(IngestError(index=i, field="", message=str(e)))

    await db.commit()
    return IngestResponse(accepted=accepted, errors=errors)
