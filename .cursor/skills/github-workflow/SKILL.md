---
name: github-workflow
description: Git workflow for commits, branches, and pull requests following project conventions. Use when creating commits, managing branches, or opening PRs.
---

# GitHub Workflow

## Branch Naming

`{initials}/{description}` — e.g. `as/fix-login-button`. Never commit on `main`/`master`.

## Commit Messages

Conventional Commits:

```
<type>(optional scope): <description>

[optional body]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.

## Creating a Commit

Only commit when the user asked. Follow the user git protocol:

- `git status`, `git diff`, `git log` in parallel first
- Stage specific files; never `git add -A`
- Never commit `.env`, secrets, or `.venv`
- Message via HEREDOC
- Do not `--amend` unless the user asked, HEAD is yours, and it is unpushed
- Do not skip hooks
- Do not update git config
- Do not push unless asked

```bash
git commit -m "$(cat <<'EOF'
feat(auth): add password reset flow

EOF
)"
```

## Creating a Pull Request

Only when the user asked:

```bash
git push -u origin HEAD
gh pr create --title "feat(auth): add password reset flow" --body "$(cat <<'EOF'
## Summary
- Brief description

## Test Plan
- [ ] `.venv/bin/pytest`
- [ ] Manual testing

EOF
)"
```

PR title uses the same conventional format. Keep the PR focused on one concern. Run tests and ruff before opening it.
