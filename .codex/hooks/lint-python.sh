#!/usr/bin/env bash
# Lint Python files with ruff after an agent edit. Non-blocking. No-op if ruff is missing.
set -u

input="$(cat)"
file_path="$(printf '%s' "$input" | python3 .cursor/hooks/_file_path.py)"

if [[ -z "${file_path:-}" || "${file_path}" != *.py ]]; then
  exit 0
fi

case "$file_path" in
  *.venv/*|*/.venv/*|*/migrations/*) exit 0 ;;
esac

if [[ -x .venv/bin/ruff ]]; then
  ruff_bin=".venv/bin/ruff"
elif command -v ruff >/dev/null 2>&1; then
  ruff_bin="ruff"
else
  exit 0
fi

if output="$(NO_COLOR=1 "$ruff_bin" check --color never "$file_path" 2>&1)"; then
  exit 0
fi
python3 -c 'import json,sys; print(json.dumps({"additional_context": sys.stdin.read()[:2000]}))' <<<"$output"
exit 0
