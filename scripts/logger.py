"""Structured logging with secret sanitization for dbt-toolkit."""

import logging
import re


_SECRET_PATTERNS = [
    re.compile(
        r"(password|secret|token|api_key|apikey|auth)\s*[=:]\s*\S+", re.IGNORECASE
    ),
    re.compile(r"Bearer\s+\S+", re.IGNORECASE),
]


class ToolkitLogger:
    """Logger wrapper with secret sanitization."""

    def __init__(self, name: str, level: int = logging.INFO):
        self._logger = logging.getLogger(f"dbt-toolkit.{name}")
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("[dbt-toolkit] %(message)s"))
            self._logger.addHandler(handler)
        self._logger.setLevel(level)

    def sanitize(self, text: str) -> str:
        """Remove secrets from text."""
        result = text
        for pattern in _SECRET_PATTERNS:
            result = pattern.sub(
                lambda m: (
                    m.group(0).split("=")[0] + "=***"
                    if "=" in m.group(0)
                    else m.group(0).split(":")[0] + ": ***"
                    if ":" in m.group(0)
                    else "***"
                ),
                result,
            )
        return result

    def info(self, msg: str, *args, sanitize: bool = True):
        if sanitize:
            msg = self.sanitize(msg)
        self._logger.info(msg, *args)

    def warning(self, msg: str, *args, sanitize: bool = True):
        if sanitize:
            msg = self.sanitize(msg)
        self._logger.warning(msg, *args)

    def error(self, msg: str, *args, sanitize: bool = True):
        if sanitize:
            msg = self.sanitize(msg)
        self._logger.error(msg, *args)

    def debug(self, msg: str, *args, sanitize: bool = True):
        if sanitize:
            msg = self.sanitize(msg)
        self._logger.debug(msg, *args)
