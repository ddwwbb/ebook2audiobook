"""Shared utilities for API routes."""

from __future__ import annotations

import re

# Patterns that may leak secrets in error messages
_SECRET_PATTERNS = [
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "sk-***"),
    (re.compile(r"Bearer\s+[a-zA-Z0-9._\-]{20,}"), "Bearer ***"),
    (re.compile(r"api[_-]?key[=:]\s*[a-zA-Z0-9._\-]{10,}", re.IGNORECASE), "api_key=***"),
    (re.compile(r"x-api-key[:\s]+[a-zA-Z0-9._\-]{10,}", re.IGNORECASE), "x-api-key: ***"),
]


def sanitize_error(msg: str) -> str:
    """Strip API keys and tokens from error messages before sending to client."""
    sanitized = msg
    for pattern, replacement in _SECRET_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized
