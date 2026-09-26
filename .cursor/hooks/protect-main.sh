#!/usr/bin/env bash
# Block agent file edits while on main/master. No-op if this is not a git repo.
set -u

cat >/dev/null

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  printf '%s\n' '{"permission":"allow"}'
  exit 0
fi

branch="$(git branch --show-current 2>/dev/null || true)"
if [[ "$branch" == "main" || "$branch" == "master" ]]; then
  printf '%s\n' '{"permission":"deny","user_message":"Cannot edit files on main/master. Create a feature branch first.","agent_message":"Edits on main/master are blocked. Create a feature branch first."}'
  exit 0
fi

printf '%s\n' '{"permission":"allow"}'
exit 0
