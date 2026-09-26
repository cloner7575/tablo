---
name: pr-review
description: Review a pull request using project standards. Use when the user wants to review a PR, check code quality, or get structured feedback on changes. Accepts a PR number or URL. Triggers on "review PR 123", "check this pull request", "/pr-review 123".
---

# PR Review

Review the pull request the user named (number or URL).

## Instructions

1. Fetch the PR:

   ```bash
   gh pr view <n>
   gh pr diff <n>
   ```

2. Apply the `code-reviewer` skill checklist to every changed file:

   - Type hints (no `Any`)
   - No silent exceptions
   - N+1 avoided (`select_related` / `prefetch_related`)
   - Loading / error / empty states in templates
   - Tests for the change
   - Docs only if they would otherwise be wrong

3. Feedback format:

   - **Critical**: must fix before merge
   - **Warning**: should fix
   - **Suggestion**: nice to have

   Cite paths and line ranges. Include a fix example for each Critical item.

4. Post comments with `gh pr comment` (or `gh pr review`) only if the user asked to publish the review.
