from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Agent
from app.schemas import AgentResponse

router = APIRouter(prefix="/api/v1", tags=["agents"])


@router.get("/agents")
async def list_agents(
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(Agent).order_by(Agent.name))
    agents = result.scalars().all()
    return {
        "agents": [
            AgentResponse(
                name=a.name,
                first_seen_at=a.first_seen_at,
                last_seen_at=a.last_seen_at,
            )
            for a in agents
        ]
    }
