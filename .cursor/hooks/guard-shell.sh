#!/usr/bin/env bash
# Ask before destructive or environment-damaging shell commands.
# Fails open: a broken guard must not block ordinary work.
set -u

input="$(cat)"
command="$(printf '%s' "$input" | python3 .cursor/hooks/_json_field.py command)"

if [[ -z "${command:-}" ]]; then
  printf '%s\n' '{"permission":"allow"}'
  exit 0
fi

ask() {
  python3 - "$1" <<'PY'
import json
import sys

reason = sys.argv[1]
print(
    json.dumps(
        {
            "permission": "ask",
            "user_message": f"This command looks destructive: {reason}. Review it before running.",
            "agent_message": f"A project hook flagged this command: {reason}.",
        }
    )
)
PY
  exit 0
}

case "$command" in
  *"rm -rf /"*|*"rm -rf ~"*|*"rm -fr /"*)
    ask "recursive delete outside the project" ;;
  *"git push --force"*|*"git push -f "*)
    ask "force push" ;;
  *"git reset --hard"*|*"git clean -"*[dfx]*)
    ask "discards uncommitted work" ;;
  *"manage.py flush"*|*"manage.py sqlflush"*|*"manage.py reset_db"*)
    ask "wipes database contents" ;;
  *"DROP TABLE"*|*"DROP DATABASE"*|*"TRUNCATE "*)
    ask "destructive SQL" ;;
  *"DJANGO_SETTINGS_MODULE=core.settings.production"*"migrate"*)
    ask "migration against production settings" ;;
esac

# pip outside the project virtualenv pollutes the system interpreter.
if [[ "$command" == *"pip install"* && "$command" != *".venv/bin/pip"* && "$command" != *"python -m pip"* ]]; then
  ask "pip install outside .venv/bin/pip"
fi

printf '%s\n' '{"permission":"allow"}'
exit 0
