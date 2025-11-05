"""Structured logging configuration for the Threat Hunting Playbooks stack."""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog


def _get_structlog_processors(json_logs: bool) -> list[Any]:
    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    return processors


def configure_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    """Configure standard logging and structlog for API and worker processes."""

    structlog.configure(
        processors=_get_structlog_processors(json_logs),
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(message)s",
        stream=sys.stdout,
    )

    structlog.get_logger(__name__).bind(component="logging").info(
        "logging configured",
        json_logs=json_logs,
        level=log_level.upper(),
    )
