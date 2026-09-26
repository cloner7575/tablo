#!/usr/bin/env python3
"""After a models.py edit, tell the agent when a migration is missing."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
PYTHON = REPO / ".venv" / "bin" / "python"


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

    path = _file_path(payload)
    if not path or Path(path).name != "models.py":
        return
    if not PYTHON.is_file():
        return

    result = subprocess.run(
        [str(PYTHON), "manage.py", "makemigrations", "--check", "--dry-run"],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if result.returncode == 0:
        return

    detail = (result.stdout + result.stderr).strip()[:1500]
    print(
        json.dumps(
            {
                "additional_context": (
                    "Model changes have no migration yet. Run "
                    "`.venv/bin/python manage.py makemigrations`, read the "
                    "generated file, and commit it with the model change.\n"
                    f"{detail}"
                )
            }
        )
    )


if __name__ == "__main__":
    main()
