from __future__ import annotations

import json
import logging
import sys
from logging.config import dictConfig

from app.settings import get_settings


def _json_formatter() -> logging.Formatter:
    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            payload = {
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            if record.exc_info:
                payload["exc_info"] = self.formatException(record.exc_info)
            return json.dumps(payload, ensure_ascii=False)

    return JsonFormatter()


def configure_logging() -> None:
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
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            }
        }

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": formatters,
            "handlers": {
                "stdout": handler,
            },
            "root": {
                "handlers": ["stdout"],
                "level": level,
            },
        }
    )


__all__ = ["configure_logging"]
