from __future__ import annotations

import re

_PASSWORD_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(=password=)([^\s]+)", re.IGNORECASE),
    re.compile(r"('password'\s*:\s*')([^']*)(')", re.IGNORECASE),
    re.compile(r'("password"\s*:\s*")([^"]*)(")', re.IGNORECASE),
)


def sanitize(text: str) -> str:
    """Mask password values in string-like debug output."""

    sanitized = text
    for pattern in _PASSWORD_PATTERNS:
        sanitized = pattern.sub(r"\1***\3" if pattern.groups == 3 else r"\1***", sanitized)
    return sanitized
