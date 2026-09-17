# MediChannel — verified production defects

Real defects from the `fsn_hes_article` sibling series (AGENCY15-316 / -321 /
-326). Prioritisation signal only: the normative rule is the cited ID. Full
write-ups in `docs/medi.md`.

| Finding | Ticket(s) | Rule | Severity |
|---|---|---|---|
| Font sizes in `rem` throughout instead of `px` | -316, -321, -326 | MCD-010 | High |
| `cst-h1-banner` present but zero true `<h1>` | -316 | HTML-007 | High |
| Flat H2-only structure, no `<h1>` | -326 | HTML-007 | High |
| H1-as-image-banner in a `<div>` with no `<h1>` (other tickets wrapped the same pattern correctly) | -316/-321/-326 | HTML-008 | High |
| Same brand colour named `--color-secondary` in one sibling, `--color-primary` in another | -316 vs -321 | CSS-007, MCD Design tokens | Medium |
| Plain `:focus` on the PDF link | -326 | HTML-015 | Medium |
| `outline: none` on the PDF link, no replacement | -321 | HTML-014 | Medium |
| Patch-note CSS appended; `.cst-page` declared 3x | -316, -321, -326 | CSS-025, CSS-027 | Medium |
| 8-20 orphaned class selectors matching no element | -316, -321 | CSS-026 | Medium |

Pattern risks seen in this channel but not yet ticketed: AM-005 (footer logo as
inline SVG rather than `<img>`), CSS-008 (spacing token as font-size), CSS-009
(border width off by 1px).
