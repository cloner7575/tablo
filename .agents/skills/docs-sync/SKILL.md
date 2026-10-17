---
name: docs-sync
description: Check if documentation is in sync with code. Use when the user wants to verify that documentation matches current code, find outdated docs, or audit documentation accuracy. Triggers on "check docs", "sync documentation", "are the docs up to date", "/docs-sync".
---

# Documentation Sync

Check whether documentation still matches the code.

## Instructions

1. Find recent code changes (skip if not a git repo):

   ```bash
   git log --since="30 days ago" --name-only --pretty=format: -- "*.py" "*.md" | sort -u
   ```

2. Find related docs: `README*`, `AGENTS.md`, `.cursor/skills/`, `.cursor/rules/`, docstrings next to changed code.

3. Verify:

   - Do examples still run?
   - Are command paths still `.venv/bin/...` and `core.settings.development` / `test` / `production`?
   - Are field names and URL names still correct?

4. Flag only things that are **wrong**, not merely missing. Do not invent docs for their own sake.

5. Output a checklist of files to update.
