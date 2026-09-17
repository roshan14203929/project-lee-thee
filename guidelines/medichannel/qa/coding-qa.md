# MediChannel — Coding QA

> MediChannel-specific technical/visual-metric pass only. Design and content QA
> are channel-agnostic (`global/qa/ui-qa.md`, `global/qa/content-qa.md`).
> Editable area: inside `.cst-page` only -> MC-015.

- Typography metrics: font-size and line-height rendered in-browser vs the Figma spec, PC and SP separately. Report as "location / design side / implemented side".
- Compliance: verify `index.html`/`base.css`/`page.css` against the `MCD-*`, `MCX-*`, `MC-*`, and global coding rules already in this payload. Report as "file + line / current / corrected / reason".
- Order findings: silent breakers (CSS variables, text) first, appearance last.
- Don't flag dead CSS with no matching element — that is `technical-qa.md`'s CSS-026 check.
- Don't flag a design-vs-implementation diff that already exists in Figma; Figma is source of truth.
- Split "no real impact" items as Info.
