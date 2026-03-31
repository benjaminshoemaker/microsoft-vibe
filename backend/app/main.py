import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from app.database import engine
from app.routers import ingest, runs, agents, alerts
from app.tasks.alert_checker import check_alerts
from app.tasks.data_retention import cleanup_old_data

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    scheduler.add_job(check_alerts, "interval", minutes=1, id="alert_checker")
    scheduler.add_job(cleanup_old_data, "cron", hour=2, minute=0, id="data_retention")
    scheduler.start()
    logger.info("Scheduler started: alert_checker (1m), data_retention (daily 02:00)")
    yield
    scheduler.shutdown()
    await engine.dispose()


app = FastAPI(
    title="Agent Observatory",
    description="Production observability for AI agents",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(ingest.router)
app.include_router(runs.router)
app.include_router(agents.router)
app.include_router(alerts.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
