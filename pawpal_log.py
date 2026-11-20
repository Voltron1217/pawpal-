"""Logging setup for PawPal+: one rotating log file (pawpal.log) with secrets redacted."""
from __future__ import annotations

import logging
import os
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FILE = Path(__file__).parent / "pawpal.log"
_KEY_PATTERN = re.compile(r"(AIza[0-9A-Za-z_\-]{20,}|AQ\.[0-9A-Za-z_\-]{20,}|sk-ant-[0-9A-Za-z_\-]{10,})")
_SECRET_ENV_VARS = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY")


def redact(text: str) -> str:
    """Replace anything that looks like an API key, or equals a configured one, with [REDACTED]."""
    for name in _SECRET_ENV_VARS:
        secret = os.environ.get(name)
        if secret:
            text = text.replace(secret, "[REDACTED]")
    return _KEY_PATTERN.sub("[REDACTED]", text)


class _RedactingFormatter(logging.Formatter):
    """Formats like the base class, then scrubs secrets from the whole line (including tracebacks)."""

    def format(self, record: logging.LogRecord) -> str:
        return redact(super().format(record))


def get_logger(name: str = "pawpal") -> logging.Logger:
    """The shared 'pawpal' logger (or a child of it), configured once per process."""
    root = logging.getLogger("pawpal")
    if not root.handlers:
        root.setLevel(logging.INFO)
        root.propagate = False
        formatter = _RedactingFormatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")
        console = logging.StreamHandler()
        console.setLevel(logging.WARNING)
        console.setFormatter(formatter)
        root.addHandler(console)
        try:
            file_handler = RotatingFileHandler(LOG_FILE, maxBytes=500_000, backupCount=2, encoding="utf-8")
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
        except OSError:  # read-only folder etc.: keep running with console logging only
            root.warning("Could not open %s; logging to console only", LOG_FILE)
    return root if name == "pawpal" else logging.getLogger(name)
