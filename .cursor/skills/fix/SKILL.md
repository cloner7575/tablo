---
name: fix
description: Run ruff check and ruff format --check on recently modified files and fix reported issues. Use when the user asks to fix lint, format, or type issues, or says "/fix".
---

# Fix Lint and Format

Run ruff on the files that were modified in this session (or the path the user named).

```bash
.venv/bin/ruff check <files>
.venv/bin/ruff format --check <files>
```

Then fix every error or warning reported. Do not suppress with `# noqa` unless there is no correct alternative, and explain why.

After edits, re-run the same commands until they pass. Do not change behavior to silence the linter.
