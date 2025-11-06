"""Alert notification dispatchers."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Iterable

import httpx

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def notify_slack(payload: dict[str, str]) -> None:
    if not settings.alert_slack_webhook_url:
        return
    try:
        httpx.post(settings.alert_slack_webhook_url, json=payload, timeout=10.0)
    except httpx.HTTPError as exc:  # pragma: no cover - network dependent
        logger.warning("alert.slack_failed", error=str(exc))


def notify_teams(payload: dict[str, str]) -> None:
    if not settings.alert_teams_webhook_url:
        return
    try:
        httpx.post(settings.alert_teams_webhook_url, json=payload, timeout=10.0)
    except httpx.HTTPError as exc:  # pragma: no cover - network dependent
        logger.warning("alert.teams_failed", error=str(exc))


def notify_pagerduty(summary: str, severity: str, source: str) -> None:
    if not settings.alert_pagerduty_routing_key:
        return
    body = {
        "routing_key": settings.alert_pagerduty_routing_key,
        "event_action": "trigger",
        "payload": {
            "summary": summary,
            "severity": severity,
            "source": source,
        },
    }
    try:
        httpx.post(settings.alert_pagerduty_api_url, json=body, timeout=10.0)
    except httpx.HTTPError as exc:  # pragma: no cover - network dependent
        logger.warning("alert.pagerduty_failed", error=str(exc))


def _build_email(subject: str, body: str, to_addresses: Iterable[str]) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.alert_email_from
    message["To"] = ", ".join(to_addresses)
    message.set_content(body)
    return message


def notify_email(subject: str, body: str) -> None:
    if not (settings.alert_email_host and settings.alert_email_from and settings.alert_email_to):
        return

    recipients = [addr.strip() for addr in settings.alert_email_to.split(",") if addr.strip()]
    if not recipients:
        return

    message = _build_email(subject, body, recipients)

    context = smtplib.SMTP(settings.alert_email_host, settings.alert_email_port, timeout=10)
    try:
        if settings.alert_email_use_tls:
            context.starttls()
        if settings.alert_email_username and settings.alert_email_password:
            context.login(settings.alert_email_username, settings.alert_email_password)
        context.send_message(message)
    finally:
        context.quit()
