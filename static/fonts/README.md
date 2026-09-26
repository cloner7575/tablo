# Fonts

Self-hosted so the shell renders identically offline, in CI, and behind a
firewall — no Google Fonts request, no layout shift, no third-party origin.

| File | Family | Licence |
|------|--------|---------|
| `ibm-plex-sans-latin.woff2` | IBM Plex Sans (variable, 100–700, latin subset) | SIL Open Font Licence 1.1 — Copyright © 2017 IBM Corp. |
| `jetbrains-mono-latin.woff2` | JetBrains Mono (variable, 100–800, latin subset) | SIL Open Font Licence 1.1 — Copyright © 2020 JetBrains s.r.o. |

Both are declared with `@font-face` in `static/css/tokens.css` and reached
through `--font-sans` / `--font-mono`. Licence text:
<https://openfontlicense.org>.

## Swapping them

Change `--font-sans` / `--font-mono` in `tokens.css` and add the matching
`@font-face` blocks. Persian products replace the sans face with Vazirmatn or
Estedad (see the `persian-ui` skill) and may drop these latin files entirely.
