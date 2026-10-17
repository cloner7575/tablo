#!/usr/bin/env python3
"""Extract a file path from Cursor hook JSON on stdin."""

from __future__ import annotations

import json
import sys


def _from_mapping(data: object) -> str | None:
    if not isinstance(data, dict):
        return None
    for key in ("file_path", "path", "filePath"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    nested = data.get("tool_input") or data.get("toolInput")
    if isinstance(nested, dict):
        found = _from_mapping(nested)
        if found:
            return found
    files = data.get("files") or data.get("file_paths")
    if isinstance(files, list) and files:
        first = files[0]
        if isinstance(first, str) and first.strip():
            return first.strip()
        found = _from_mapping(first)
        if found:
            return found
    return None


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        return
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return
    path = _from_mapping(data)
    if path:
        sys.stdout.write(path)


if __name__ == "__main__":
    main()
