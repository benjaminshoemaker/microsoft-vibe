from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AlertRule, AlertHistory
from app.schemas import (
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleResponse,
    AlertHistoryResponse,
)

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


def _rule_to_response(rule: AlertRule) -> AlertRuleResponse:
    return AlertRuleResponse(
        id=rule.id,
        agent_name=rule.agent_name,
        metric=rule.metric,
        threshold_value=rule.threshold_value,
        window_minutes=rule.window_minutes,
        multiplier=rule.multiplier,
        enabled=rule.enabled,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@router.get("/rules")
async def list_rules(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(AlertRule).order_by(AlertRule.id))
    rules = result.scalars().all()
    return {"rules": [_rule_to_response(r) for r in rules]}


@router.post("/rules", status_code=201)
async def create_rule(
    payload: AlertRuleCreate,
    db: AsyncSession = Depends(get_db),
) -> AlertRuleResponse:
    now = datetime.now(timezone.utc)
    rule = AlertRule(
        agent_name=payload.agent_name,
        metric=payload.metric.value,
        threshold_value=payload.threshold_value,
        window_minutes=payload.window_minutes,
        multiplier=payload.multiplier,
        enabled=True,
        created_at=now,
        updated_at=now,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return _rule_to_response(rule)


@router.put("/rules/{rule_id}")
async def update_rule(
    rule_id: int,
    payload: AlertRuleUpdate,
    db: AsyncSession = Depends(get_db),
) -> AlertRuleResponse:
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if rule is None:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "metric" in update_data and update_data["metric"] is not None:
        update_data["metric"] = update_data["metric"].value

    for key, value in update_data.items():
        setattr(rule, key, value)
    rule.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(rule)
    return _rule_to_response(rule)


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if rule is None:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    await db.delete(rule)
    await db.commit()


@router.get("/history")
async def get_alert_history(
    agent_name: str | None = None,
    time_start: datetime | None = None,
    time_end: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    query = select(AlertHistory)
    count_query = select(func.count()).select_from(AlertHistory)

    if agent_name:
        query = query.where(AlertHistory.agent_name == agent_name)
        count_query = count_query.where(AlertHistory.agent_name == agent_name)
    if time_start:
        query = query.where(AlertHistory.triggered_at >= time_start)
        count_query = count_query.where(AlertHistory.triggered_at >= time_start)
    if time_end:
        query = query.where(AlertHistory.triggered_at <= time_end)
        count_query = count_query.where(AlertHistory.triggered_at <= time_end)

    query = query.order_by(desc(AlertHistory.triggered_at))
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    alerts = result.scalars().all()
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    return {
        "alerts": [
            AlertHistoryResponse(
                id=a.id,
                alert_rule_id=a.alert_rule_id,
                agent_name=a.agent_name,
                metric_value=a.metric_value,
                triggered_at=a.triggered_at,
                email_sent=a.email_sent,
            )
            for a in alerts
        ],
        "total": total,
    }
