from __future__ import annotations

"""Application logging configuration.

Provides a single entrypoint `configure_logging()` used by `create_app()`.

Features:
- Adds `request_id` to log records via a filter (see middleware/request_context).
- Supports either human-readable text logs or structured JSON logs.
"""

import json
import logging
import sys
from logging.config import dictConfig

from app.settings import get_settings
from app.middleware.request_context import request_id_ctx


class _RequestIdFilter(logging.Filter):
    """Inject `request_id` into every log record."""
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get() or "-"
        return True


def _json_formatter() -> logging.Formatter:
    """Build a JSON formatter implementation."""
    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            payload = {
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            if getattr(record, "request_id", None):
                payload["request_id"] = record.request_id
            if record.exc_info:
                payload["exc_info"] = self.formatException(record.exc_info)
            return json.dumps(payload, ensure_ascii=False)

    return JsonFormatter()


def configure_logging() -> None:
    """Configure process-wide logging based on Settings.

    - `EMMO_LOG_JSON=true` enables JSON logs.
    - `EMMO_LOG_LEVEL` controls verbosity.
    """
    settings = get_settings()
    level = settings.log_level.upper()

    if settings.log_json:
        handler = {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "json",
        }
        formatters = {
            "json": {
                "()": "app.logging_config._json_formatter",
            }
        }
    else:
        handler = {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "default",
        }
        formatters = {
            "default": {
                "format": "%(asctime)s %(levelname)s %(name)s [request_id=%(request_id)s] %(message)s",
            }
        }

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": formatters,
            "handlers": {
                "stdout": {
                    **handler,
                    "filters": ["request_id"],
                },
            },
            "filters": {
                "request_id": {"()": "app.logging_config._RequestIdFilter"},
            },
            "root": {
                "handlers": ["stdout"],
                "level": level,
            },
        }
    )


__all__ = ["configure_logging"]
