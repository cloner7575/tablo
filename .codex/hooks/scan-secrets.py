#!/usr/bin/env python3
"""Warn when an edited file looks like it contains a hardcoded secret.

Advisory only: it returns context for the agent, never a block, because a
false positive must not stop work.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SKIP_PARTS = {".venv", "node_modules", ".git", "__pycache__", "locale"}
SKIP_NAMES = {".env.example"}
MAX_BYTES = 400_000

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "hardcoded SECRET_KEY",
        re.compile(r"""SECRET_KEY\s*=\s*['"](?!django-insecure-)[^'"\n]{16,}"""),
    ),
    ("AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Slack token", re.compile(r"\bxox[abprs]-[0-9A-Za-z-]{10,}")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[0-9A-Za-z]{20,}")),
    (
        "inline password or token literal",
        re.compile(
            r"""(?i)\b(password|passwd|api_key|apikey|auth_token|access_token)\s*=\s*['"][^'"\n]{8,}['"]"""
        ),
    ),
    (
        "database URL with credentials",
        re.compile(r"(?i)\b(postgres|postgresql|mysql|redis)://[^:\s'\"]+:[^@\s'\"]+@"),
    ),
)


def _file_path(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None
    for key in ("file_path", "path", "filePath"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for key in ("tool_input", "toolInput"):
        found = _file_path(payload.get(key))
        if found:
            return found
    return None


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        return
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return

    raw_path = _file_path(payload)
    if not raw_path:
        return

    path = Path(raw_path)
    if path.name in SKIP_NAMES or SKIP_PARTS.intersection(path.parts):
        return
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        return

    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return

    hits = [label for label, pattern in PATTERNS if pattern.search(text)]
    if not hits:
        return

    findings = ", ".join(sorted(set(hits)))
    print(
        json.dumps(
            {
                "additional_context": (
                    f"Possible secret in {path}: {findings}. "
                    "Move the value to the environment, read it through "
                    "core/settings/env.py, and document the key in .env.example."
                )
            }
        )
    )


if __name__ == "__main__":
    main()
