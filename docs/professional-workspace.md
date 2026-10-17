# Professional workspace

The experience combines a public inspiration gallery for shop owners, completed work, useful guides, private references, specialists and project management. Following owner feedback, the original white/grey, charcoal and crimson palette is restored. The concept editor has been removed, including its route, form, template, script and styles.

## Current capabilities

| Area | Capability |
| --- | --- |
| Discovery | Searchable, paginated portfolio gallery with service/city filters and sorting |
| References | Private browser-session board with independent ideas and portfolio references |
| Project requests | Start a request from the board; reference titles and links prefill the description in the existing wizard |
| Quotes | Side-by-side comparison of price, installation cost, delivery and warranty |
| Vendor workspace | Existing matched requests, quotes, chat, profile and portfolio; direct access to discovery and board |
| Execution | Existing quote-linked chat, acceptance, completion and reviews retained |

## Design and implementation

- Original product colours live in `static/css/tokens.css`: white/grey surfaces, charcoal header/footer and crimson actions.
- The homepage uses a light composition with a charcoal workshop section.
- Self-hosted Vazirmatn, Persian copy, logical CSS, RTL and Jalali display remain.
- `atelier.css` composes discovery and the homepage alongside existing `base.css` and `tablo.css`.
- Illustrative fallback images are labelled «تصویر الهام» on discovery surfaces.
- New UI uses keyboard-accessible controls, visible focus, responsive layouts, reduced motion and designed empty states.
- Forms, views and ORM selectors extend their existing app modules. The initial workspace added no models or packages. The editorial extension now adds models and migrations in `apps/editorial`, retaining existing dependencies.

## Routes and storage

- `/portfolio/`: public discovery.
- `/portfolio/board/`: permanent redirect to `/inspiration/`.
- `/inspiration/saved/`: private collection of both independent ideas and saved portfolio references.
- `/portfolio/board/<pk>/`: POST-only add/remove with CSRF, discoverability checks and preserved gallery filters.
- `/request/from-board/`: POST-only handoff of current discoverable references to the existing request wizard. Empty boards return to the collection with an explanation.

The board belongs to the current browser, expires with the existing Django session, and is not synced between devices. Reference links become database-backed project content after normal authentication and final confirmation. Removing the editor does not remove previously submitted projects.

## Verification

Tests cover board isolation, capacity, hidden work, CSRF, safe local redirects, pagination/filter preservation, constant list query counts, reference handoff and the absence of the removed editor.

```bash
DATABASE_URL=sqlite:////tmp/tablo-verify.sqlite3 REDIS_URL= .venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/ruff format --check .
DATABASE_URL=sqlite:////tmp/tablo-verify.sqlite3 .venv/bin/python manage.py makemigrations --check --dry-run
DATABASE_URL=sqlite:////tmp/tablo-verify.sqlite3 .venv/bin/python manage.py check
```

Ruff excludes the bundled design-skill scripts under both `.cursor` and `.agents`. Application code is checked. Restricted environments require local networking permission for the WebSocket communicator tests.

Owner-feedback revision verified: 177 tests passed; Ruff lint/format, Django checks, missing-migration and whitespace checks passed. Browser verification confirms the original grey canvas, charcoal header and crimson actions, with no horizontal page overflow at the checked mobile/desktop widths.

The independent gallery, articles, ownership controls and SEO setup are documented in [editorial-seo.md](editorial-seo.md).
