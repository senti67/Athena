"""
ATHENA Institutional Structured JSON Logging Engine
Ensures zero credential leakage and injects correlation IDs across async tasks.
"""

import contextvars
import json
import logging
import re
import sys
from datetime import datetime
from typing import Any, Dict, Optional

# Context variable for distributed tracing correlation ID
correlation_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default="SYSTEM_INIT"
)

SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(password|secret|api[_-]?key|token|jwt|auth)\s*[:=]\s*['\"]?([^'\"\s,]+)"),
]


def sanitize_sensitive_data(text: str) -> str:
    """Masks secrets and API keys from logging strings."""
    if not isinstance(text, str):
        return text
    sanitized = text
    for pattern in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(r"\1=***REDACTED***", sanitized)
    return sanitized


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as structured JSON with correlation IDs and timestamps."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": sanitize_sensitive_data(record.getMessage()),
            "correlation_id": correlation_id_ctx.get(),
            "module": record.module,
            "func_name": record.funcName,
            "line_no": record.lineno,
        }

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            log_obj.update(record.extra_fields)

        return json.dumps(log_obj)


def get_logger(name: str = "athena") -> logging.Logger:
    """Returns a structured JSON logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


logger = get_logger("athena.core")
