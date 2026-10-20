# Site fonts

All active fonts are self-hosted; there are no runtime requests to font CDNs.

- Vazirmatn Arabic and Latin variable subsets: body text and UI, 100–900.
- Estedad variable WOFF2: headings and category names, 100–900, `--font-display`.
  Official source: https://github.com/aminabedi68/Estedad
  Downloaded 2026-10-20 from `fonts/webfonts/Estedad[wght].woff2`.
  SIL Open Font License 1.1 is retained in `Estedad-OFL.txt`.
- IBM Plex Sans Latin and JetBrains Mono Latin are retained starter assets;
  they are not used by the Persian UI. Both use SIL Open Font License 1.1.

Declarations and fallbacks live in `static/css/tokens.css` with `font-display: swap`.
