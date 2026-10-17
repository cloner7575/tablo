---
name: pr-summary
description: Generate a pull request summary for the current branch changes. Use when the user wants to create a PR description, summarize branch changes, or prepare a PR body. Triggers on "summarize my changes", "write a PR description", "what changed in this branch", "/pr-summary".
---

# PR Summary

Generate a pull request summary for the current branch.

## Instructions

1. Analyze changes (use `main` if it exists, otherwise `master`):

   ```bash
   git log main..HEAD --oneline
   git diff main...HEAD --stat
   git diff main...HEAD
   ```

2. Write:

   - What changed and why
   - Notable files
   - Breaking changes (if any)
   - How to test

3. Format:

   ```markdown
   ## Summary
   - [1-3 bullets]

   ## Test Plan
   - [ ] `.venv/bin/pytest`
   - [ ] `.venv/bin/ruff check .`
   - [ ] [manual checks]
   ```

Do not open the PR unless the user asked. If they did, follow `github-workflow`.
