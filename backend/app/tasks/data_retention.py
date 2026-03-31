import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import delete

from app.config import settings
from app.database import async_session
from app.models import Event, Run, AlertHistory

logger = logging.getLogger(__name__)


async def cleanup_old_data() -> None:
    """Delete events, runs, and alert history older than retention window."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.RETENTION_DAYS)
    logger.info(f"Retention cleanup: deleting data older than {cutoff.isoformat()}")

    async with async_session() as db:
        # Delete events first (FK dependency)
        result = await db.execute(delete(Event).where(Event.created_at < cutoff))
        events_deleted = result.rowcount

        # Delete runs
        result = await db.execute(delete(Run).where(Run.created_at < cutoff))
        runs_deleted = result.rowcount

        # Delete alert history
        result = await db.execute(delete(AlertHistory).where(AlertHistory.triggered_at < cutoff))
        alerts_deleted = result.rowcount

        await db.commit()

    logger.info(
        f"Retention cleanup complete: {events_deleted} events, "
        f"{runs_deleted} runs, {alerts_deleted} alert_history rows deleted"
    )
