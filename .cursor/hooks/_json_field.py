#!/usr/bin/env python3
"""Print one top-level (or tool_input) field from Cursor hook JSON on stdin."""

from __future__ import annotations

import json
import sys


def _lookup(data: object, key: str) -> str | None:
    if not isinstance(data, dict):
        return None
    value = data.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    for nested_key in ("tool_input", "toolInput"):
        nested = data.get(nested_key)
        found = _lookup(nested, key)
        if found:
            return found
    return None


def main() -> None:
    if len(sys.argv) < 2:
        return
    raw = sys.stdin.read()
    if not raw.strip():
        return
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return
    value = _lookup(data, sys.argv[1])
    if value:
        sys.stdout.write(value)


if __name__ == "__main__":
    main()
