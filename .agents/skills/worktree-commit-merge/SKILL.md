---
name: worktree-commit-merge
description: Commit worktree changes, merge into master/main, then sync the worktree branch with main. Trigger when the user says "commit and merge to master", "we're done with this worktree, commit and merge", or similar. If there are changes and they mention merging to master/main, use this skill.
---

# Worktree Commit and Merge

You are in a git worktree on a feature branch with uncommitted changes. This skill:

1. Commits those changes on the current branch
2. Merges the branch into `master`/`main` (fast-forward if possible)

Only run this when the user explicitly asked to commit and merge.

## 1. Gather context

Run in parallel:

```bash
git status
git diff HEAD
git branch --show-current
git worktree list
git log --oneline -10
```

## 2. Commit

Stage specific files. Never `git add -A`. Never commit `.env`, secrets, or `.venv`.

Follow the user's git protocol: HEREDOC message, conventional commit, do not amend unless they asked and the commit is yours and unpushed, do not skip hooks.

```bash
git commit -m "$(cat <<'EOF'
type(scope): description

EOF
)"
```

## 3. Identify merge target

From `git worktree list`, the first entry is the main worktree. Note `MAIN_PATH`, `MAIN_BRANCH` (`main` or `master`), and `CURRENT_BRANCH`.

## 4. Merge into main

```bash
git -C <MAIN_PATH> merge --ff-only <CURRENT_BRANCH> \
  || git -C <MAIN_PATH> merge <CURRENT_BRANCH> --no-edit
```

Tell the user whether it was a fast-forward or a merge commit.

## 5. Sync the worktree branch

```bash
git merge <MAIN_BRANCH>
```

## 6. Confirm

```bash
git -C <MAIN_PATH> log --oneline -5
```

Do not push unless the user asked.
