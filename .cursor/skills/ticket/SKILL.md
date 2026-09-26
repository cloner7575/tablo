---
name: ticket
description: Work on a GitHub issue end-to-end: read the issue, explore the codebase, create a branch, implement with TDD, run quality checks, comment on the issue, and open a PR. Use when the user provides an issue number or asks to implement a ticket. Triggers on "/ticket 123", "work on this issue", "implement #123".
---

# Ticket Workflow

Work on the GitHub issue ID the user provided.

## 1. Read the Issue

```bash
gh issue view <id>
gh issue view <id> --comments
```

Summarize title, body, acceptance criteria, blockers, and linked PRs.

## 2. Explore

Search for related code. Identify files to change. Prefer the `onboard` skill when the area is unfamiliar.

## 3. Branch

```bash
git checkout -b {initials}/{issue-id}-{brief-description}
```

Do not edit on `main`/`master`.

## 4. Implement with TDD

Write a failing test first. Follow project skills (`django-models`, `django-rest-framework`, etc.). Make incremental conventional commits via HEREDOC.

## 5. Quality Checks

```bash
.venv/bin/ruff check .
.venv/bin/ruff format .
.venv/bin/pytest
```

## 6. Update the Issue

```bash
gh issue comment <id> --body "In progress. Branch \`as/123-short-name\`."
```

## 7. Open a PR Linked to the Issue

```bash
gh pr create --title "feat(#123): description" --body "$(cat <<'EOF'
## Summary
- Implements #123

## Test Plan
- [ ] pytest
- [ ] Manual check

EOF
)"
```

Include `Fixes #123` or `Closes #123` in the body when the PR should close the issue.

## 8. Unrelated Bugs

If you find an unrelated bug: open a new issue with `gh issue create`, link it, note it in the PR, and stay on the original task.
