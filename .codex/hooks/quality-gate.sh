#!/usr/bin/env bash
# Stop hook: refuse to let the turn end on a red suite or failing lint.
# Only runs the gate when the working tree has Python or template changes.
set -u

cat >/dev/null

if [[ ! -x .venv/bin/pytest || ! -x .venv/bin/ruff ]]; then
  exit 0
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  changed="$(git status --porcelain -- '*.py' '*.html' 2>/dev/null)"
  if [[ -z "$changed" ]]; then
    exit 0
  fi
fi

report=""

if ! lint_output="$(NO_COLOR=1 .venv/bin/ruff check --color never . 2>&1)"; then
  report+="ruff check failed:"$'\n'"${lint_output}"$'\n\n'
fi

if ! test_output="$(NO_COLOR=1 .venv/bin/pytest -q --color=no 2>&1)"; then
  report+="pytest failed:"$'\n'"$(printf '%s\n' "$test_output" | tail -n 25)"$'\n'
fi

if [[ -z "$report" ]]; then
  exit 0
fi

printf '%s' "$report" | python3 -c '
import json
import sys

report = sys.stdin.read()[:4000]
print(json.dumps({"followup_message":
    "The quality gate is red. Fix this before finishing:\n\n"
    + report
    + "\nThen re-run `.venv/bin/ruff check .` and `.venv/bin/pytest`."
}))
'
exit 0
