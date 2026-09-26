---
name: onboard
description: Onboard the agent to a new task by exploring the codebase, building context, and preparing to implement. Use when starting a new task, feature, or bug fix that requires understanding the codebase first. Triggers on requests like "onboard me", "get ready for this task", "explore and prepare", or "/onboard".
---

# Onboard

The user has provided context about the task. Use it to guide exploration.

## Instructions

Onboard to the current task by:

- If this is a **new product** (no filled `PRODUCT.md`), stop and run `product-intake` instead of exploring
- Exploring the codebase thoroughly (`apps/`, `core/`, templates, tests, settings)
- Reading `starter-architecture` and `ui-ux` when the task adds apps or screens
- Asking clarifying questions only when blocked
- Preferring over-exploration to under-exploration

Record findings in `.cursor/tasks/[TASK_ID]/onboarding.md` so a later session can resume. Include:

- Goal and acceptance criteria
- Relevant files and why they matter
- Existing patterns to copy
- Risks, open questions, and a proposed implementation order

`.cursor/tasks/` is gitignored; it is session notes, not product docs.
