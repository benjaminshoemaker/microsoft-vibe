import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AlertRule, AlertHistory, Run

logger = logging.getLogger(__name__)


async def evaluate_rules(db: AsyncSession) -> list[dict]:
    """Evaluate all enabled alert rules. Returns list of triggered alerts."""
    result = await db.execute(select(AlertRule).where(AlertRule.enabled == True))
    rules = result.scalars().all()
    triggered = []

    for rule in rules:
        metric_value = await _compute_metric(db, rule)
        if metric_value is None:
            continue

        breached = _check_threshold(rule, metric_value)
        if not breached:
            continue

        # Dedup: skip if same rule fired within window
        if await _recently_fired(db, rule):
            continue

        triggered.append({
            "rule": rule,
            "metric_value": metric_value,
            "agent_name": rule.agent_name or "all",
        })

    return triggered


async def _compute_metric(db: AsyncSession, rule: AlertRule) -> float | None:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=rule.window_minutes)

    base_query = select(Run).where(Run.started_at >= window_start)
    if rule.agent_name:
        base_query = base_query.where(Run.agent_name == rule.agent_name)

    result = await db.execute(base_query)
    runs = result.scalars().all()

    if not runs:
        return None

    if rule.metric == "failure_rate":
        failures = sum(1 for r in runs if r.status in ("failure", "error"))
        return (failures / len(runs)) * 100

    elif rule.metric == "p95_latency":
        durations = sorted([r.duration_ms for r in runs if r.duration_ms is not None])
        if not durations:
            return None
        idx = int(len(durations) * 0.95)
        return float(durations[min(idx, len(durations) - 1)])

    elif rule.metric == "stuck_run":
        running = [r for r in runs if r.status == "running"]
        if not running:
            return None
        completed = [r for r in runs if r.duration_ms is not None]
        if not completed:
            return None
        avg_duration = sum(r.duration_ms for r in completed) / len(completed)
        multiplier = rule.multiplier or 3.0
        for r in running:
            elapsed = (now - r.started_at).total_seconds() * 1000
            if elapsed > avg_duration * multiplier:
                return elapsed
        return None

    return None


def _check_threshold(rule: AlertRule, metric_value: float) -> bool:
    if rule.metric == "stuck_run":
        return metric_value is not None  # Already checked multiplier in compute
    return metric_value > rule.threshold_value


async def _recently_fired(db: AsyncSession, rule: AlertRule) -> bool:
    window_start = datetime.now(timezone.utc) - timedelta(minutes=rule.window_minutes)
    result = await db.execute(
        select(AlertHistory)
        .where(AlertHistory.alert_rule_id == rule.id)
        .where(AlertHistory.triggered_at >= window_start)
    )
    return result.scalar_one_or_none() is not None


async def record_alert(
    db: AsyncSession,
    rule: AlertRule,
    metric_value: float,
    agent_name: str,
    email_sent: bool,
) -> AlertHistory:
    alert = AlertHistory(
        alert_rule_id=rule.id,
        agent_name=agent_name,
        triggered_at=datetime.now(timezone.utc),
        metric_value=metric_value,
        email_sent=email_sent,
    )
    db.add(alert)
    await db.commit()
    return alert
