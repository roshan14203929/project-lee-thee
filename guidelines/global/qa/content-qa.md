# Content QA defaults

Procedures only. Report findings by ID; do not restate rules.

- Compare rendered output, DOM text, accessible names, and metadata against `content-inventory.json` and the Figma reference.
- Detect missing, duplicated, truncated, reordered, fabricated, or altered content.
- Verify title, headings, paragraphs, nav, buttons, links, form labels, errors, captions, prices, numerals, legal copy.
- Cite the content item identifier and output selector for every failure.
- In scope: FID-001, FID-002, FID-003, FID-004, FID-013, HTML-012.

## Copy accuracy

- Text matches wireframe/approved copy exactly — no typos, missing or duplicated text.
- CTAs, disclaimers, footnotes, superscripts, symbols all present and correctly placed.
- ®, ™, †, superscript and subscript render correctly in-browser -> AM-011, AM-012.
- Japanese pages: full-width vs half-width numerals and punctuation match the design; platform-risky characters -> `global/coding/assets-media.md` Character Encoding Preflight.
- Document code / version (JP number) correct and current. Title format -> MC-012.

## Placeholder severity

Unreplaced placeholder copy is a blocker (FID-013): `JP-○○○○`, `Lorem`, `TODO`,
`PLACEHOLDER`, `ここに入る`. **Exception — MediChannel only:** breadcrumb
placeholders such as `/test.html` sit in a client-managed zone and are INFO, not
defects -> MC-015, MC-016.
