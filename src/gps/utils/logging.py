"""GPS Utilities: Structured Logging Setup."""

from __future__ import annotations

import logging
import sys
from typing import Any, ClassVar


class _GPSFormatter(logging.Formatter):
    """Custom formatter with color support for terminal output."""

    GREY = "\x1b[38;5;240m"
    CYAN = "\x1b[36m"
    YELLOW = "\x1b[33m"
    RED = "\x1b[31m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"

    FORMATS: ClassVar[dict[int, str]] = {
        logging.DEBUG: GREY + "%(levelname)-8s" + RESET + " %(name)s — %(message)s",
        logging.INFO: CYAN + "%(levelname)-8s" + RESET + " %(message)s",
        logging.WARNING: YELLOW + "%(levelname)-8s" + RESET + " %(message)s",
        logging.ERROR: RED + "%(levelname)-8s" + RESET + " %(name)s — %(message)s",
        logging.CRITICAL: BOLD_RED + "%(levelname)-8s" + RESET + " %(name)s — %(message)s",
    }

    def format(self, record: logging.LogRecord) -> str:
        formatter = logging.Formatter(self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO]))
        return formatter.format(record)


def configure_logging(level: str = "INFO", json_format: bool = False) -> None:
    """
    Configure GPS application logging.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR).
        json_format: If True, emit structured JSON logs (useful in CI).
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(numeric_level)

    if json_format:
        import json

        class _JSONFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                data: dict[str, Any] = {
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }
                if record.exc_info:
                    data["exception"] = self.formatException(record.exc_info)
                return json.dumps(data)

        handler.setFormatter(_JSONFormatter())
    else:
        handler.setFormatter(_GPSFormatter())

    root = logging.getLogger("gps")
    root.setLevel(numeric_level)
    root.handlers.clear()
    root.addHandler(handler)
    root.propagate = False
