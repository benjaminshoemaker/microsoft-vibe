import logging

from app.database import async_session
from app.services.alerts import evaluate_rules, record_alert
from app.services.email import send_alert_email

logger = logging.getLogger(__name__)


async def check_alerts() -> None:
    """Evaluate all alert rules and send notifications for breaches."""
    async with async_session() as db:
        triggered = await evaluate_rules(db)

        for alert in triggered:
            rule = alert["rule"]
            agent_name = alert["agent_name"]
            metric_value = alert["metric_value"]

            email_sent = await send_alert_email(
                agent_name=agent_name,
                metric=rule.metric,
                threshold_value=rule.threshold_value,
                metric_value=metric_value,
                window_minutes=rule.window_minutes,
            )

            await record_alert(
                db=db,
                rule=rule,
                metric_value=metric_value,
                agent_name=agent_name,
                email_sent=email_sent,
            )

            logger.info(
                f"Alert triggered: {agent_name} — {rule.metric} = {metric_value} "
                f"(threshold: {rule.threshold_value}, email: {email_sent})"
            )
