# Cursor Skills

Skills for this Django **starter**. They travel into every derived project as long as the layout stays the same.

## Skills by category

### Starter and product UI

| Skill | Description |
|-------|-------------|
| [starter-architecture](./starter-architecture/SKILL.md) | Where code belongs; how to add apps |
| [bootstrap-project](./bootstrap-project/SKILL.md) | Clone this base into a new product |
| [product-intake](./product-intake/SKILL.md) | Ask brand, locale, DB, theme before building |
| [ui-ux](./ui-ux/SKILL.md) | Django templates, tokens, a11y; maps Pro Max output into this starter |
| ↳ [quality-bar.md](./ui-ux/quality-bar.md) | The checklist a screen must pass before it is done |
| [ui-ux-pro-max](./ui-ux-pro-max/SKILL.md) | Searchable design intelligence (styles, palettes, UX rules, CLI) |
| [persian-ui](./persian-ui/SKILL.md) | فارسی/RTL: composition, quality bar, Iranian chrome and trust patterns |
| ↳ [rtl-engineering.md](./persian-ui/rtl-engineering.md) | Fonts, direction, numerals, bidi, forms — the mechanics |
| ↳ [corporate-sites.md](./persian-ui/corporate-sites.md) | سایت شرکتی / لندینگ: IA and page recipes |
| [persian-locale](./persian-locale/SKILL.md) | Jalali calendar, Persian numerals, Tehran time |
| [persian-ecommerce](./persian-ecommerce/SKILL.md) | فروشگاه فارسی: تومان، جداکننده هزارگان، checkout |
| [persian-shop-playbook](./persian-shop-playbook/SKILL.md) | NightRuby-class shop: storefront + panel + domain checklist |
| ↳ [design.md](./persian-shop-playbook/design.md) | Locked cream UI system — copy to project `design.md` for the next shop |

### Workflows

| Skill | Description |
|-------|-------------|
| [definition-of-done](./definition-of-done/SKILL.md) | The senior loop: plan → failing test → implement → verify → report |
| [onboard](./onboard/SKILL.md) | Explore the codebase before implementing |
| [ticket](./ticket/SKILL.md) | GitHub issue end-to-end |
| [pr-review](./pr-review/SKILL.md) | Review a PR |
| [pr-summary](./pr-summary/SKILL.md) | PR description from the branch diff |
| [code-quality](./code-quality/SKILL.md) | ruff + pytest |
| [code-reviewer](./code-reviewer/SKILL.md) | Django + UI review checklist |
| [docs-sync](./docs-sync/SKILL.md) | Docs vs code |
| [worktree-commit-merge](./worktree-commit-merge/SKILL.md) | Commit worktree and merge |
| [github-workflow](./github-workflow/SKILL.md) | Branches, commits, PRs |
| [fix](./fix/SKILL.md) | Fix ruff findings |

### Testing and debugging

| Skill | Description |
|-------|-------------|
| [pytest-django-patterns](./pytest-django-patterns/SKILL.md) | pytest-django, factories, TDD |
| [systematic-debugging](./systematic-debugging/SKILL.md) | Root-cause first |

### Django

| Skill | Description |
|-------|-------------|
| [django-models](./django-models/SKILL.md) | Models, QuerySets, `TimeStampedModel` |
| [django-views-urls](./django-views-urls/SKILL.md) | Typed function views, URLconf, permissions, pagination |
| [django-services](./django-services/SKILL.md) | Service layer, selectors, transactions, `on_commit` |
| [django-forms](./django-forms/SKILL.md) | Forms and validation |
| [django-templates](./django-templates/SKILL.md) | Inheritance, partials, components, error pages |
| [django-migrations](./django-migrations/SKILL.md) | Safe schema changes, data migrations, `--check` |
| [django-i18n](./django-i18n/SKILL.md) | gettext, `LANGUAGES`, `makemessages`, RTL |
| [django-performance](./django-performance/SKILL.md) | N+1, indexes, query-count tests |
| [django-logging](./django-logging/SKILL.md) | Logger naming, levels, never swallowing |
| [django-extensions](./django-extensions/SKILL.md) | Introspection commands |
| [django-rest-framework](./django-rest-framework/SKILL.md) | APIs (wired at `/api/v1/`) |
| [django-auth](./django-auth/SKILL.md) | `accounts.User`, auth screens, permissions, JWT |
| [django-admin](./django-admin/SKILL.md) | ModelAdmin |
| [django-signals](./django-signals/SKILL.md) | Signals and `on_commit` |
| [django-caching](./django-caching/SKILL.md) | Cache and N+1 |

### Jobs and deploy

| Skill | Description |
|-------|-------------|
| [htmx-patterns](./htmx-patterns/SKILL.md) | HTMX partials |
| [celery-patterns](./celery-patterns/SKILL.md) | Background tasks |
| [docker-django](./docker-django/SKILL.md) | Images and compose |

## Adding skills

1. Create `.cursor/skills/skill-name/SKILL.md`
2. Frontmatter: `name` + trigger-rich `description`
3. Omit `disable-model-invocation` so the skill can auto-apply
4. Keep instructions **starter-generic** (paths like `apps/`, `core/settings/`) so copies still work
5. Update this README
