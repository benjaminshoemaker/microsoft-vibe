import logging

from app.config import settings

logger = logging.getLogger(__name__)


async def send_alert_email(
    agent_name: str,
    metric: str,
    threshold_value: float,
    metric_value: float,
    window_minutes: int,
) -> bool:
    """Send alert email via SMTP. Returns True if sent, False if skipped/failed."""
    if not settings.SMTP_HOST:
        logger.warning("SMTP not configured — alert logged to console only")
        logger.info(
            f"ALERT: {agent_name} — {metric} breached "
            f"(threshold: {threshold_value}, current: {metric_value}, window: {window_minutes}m)"
        )
        return False

    if not settings.ALERT_RECIPIENTS:
        logger.warning("No ALERT_RECIPIENTS configured — skipping email")
        return False

    try:
        import aiosmtplib
        from email.message import EmailMessage

        recipients = [r.strip() for r in settings.ALERT_RECIPIENTS.split(",")]
        dashboard_link = f"{settings.BASE_URL}/?agent_name={agent_name}"

        msg = EmailMessage()
        msg["Subject"] = f"[Agent Alert] {agent_name} — {metric} threshold breached"
        msg["From"] = settings.SMTP_FROM
        msg["To"] = ", ".join(recipients)
        msg.set_content(
            f"Agent: {agent_name}\n"
            f"Metric: {metric}\n"
            f"Threshold: {threshold_value}\n"
            f"Current Value: {metric_value}\n"
            f"Window: Last {window_minutes} minutes\n\n"
            f"View dashboard: {dashboard_link}\n"
        )

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER or None,
            password=settings.SMTP_PASSWORD or None,
            start_tls=True,
        )
        logger.info(f"Alert email sent for {agent_name} — {metric}")
        return True

    except Exception as e:
        logger.error(f"Failed to send alert email: {e}")
        return False
