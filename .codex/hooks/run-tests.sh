#!/usr/bin/env bash
# Run pytest on a modified test file. Non-blocking. No-op if pytest is missing.
set -u

input="$(cat)"
file_path="$(printf '%s' "$input" | python3 .cursor/hooks/_file_path.py)"

if [[ -z "${file_path:-}" || "${file_path}" != *.py ]]; then
  exit 0
fi

base="$(basename "$file_path")"
case "$file_path" in
  *.venv/*|*/.venv/*) exit 0 ;;
esac

if [[ "$base" != test_*.py && "$base" != *_test.py && "$file_path" != */tests/* ]]; then
  exit 0
fi

if [[ -x .venv/bin/pytest ]]; then
  pytest_bin=".venv/bin/pytest"
elif command -v pytest >/dev/null 2>&1; then
  pytest_bin="pytest"
else
  exit 0
fi

output="$(NO_COLOR=1 "$pytest_bin" "$file_path" -x -q --color=no 2>&1)"
status=$?
if [[ $status -eq 0 ]]; then
  exit 0
fi
output="$(printf '%s\n' "$output" | tail -n 30)"
python3 -c 'import json,sys; print(json.dumps({"additional_context": sys.stdin.read()[:4000]}))' <<<"$output"
exit 0
