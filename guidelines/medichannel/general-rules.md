# MediChannel — Delivery & Process Rules

> Channel profile: XHTML 1.0 Strict, internal, 960 px fixed layout. Coding deltas live in `coding/`; QA specifics in `qa/`. This file covers delivery process/governance only.

## Template & Editable Area

- Use the distributed `MediChannel_template`. Treat it as read-only outside the editable area.
- Write HTML only between `<!-- ボディ部分編集可能エリアここから -->` and `<!-- ボディ部分編集可能エリアここまで -->` (the real marker used in every production ticket — not the English "Body editable area starts/ends here" phrasing).
- `index.html` is excluded from the comment-stripping rule in `global/coding/css.md` — its structure, including the editable-area marker comments and everything outside the editable area, must stay identical to the reference template/example folder. Only the content written inside the editable area is authored and cleaned; the surrounding template is never modified.
- Load CSS/JS as external files, after the template's `desktop.css`/`script.css`.

## Document Type

**XHTML 1.0 Strict — not HTML5.** See `coding/xhtml-syntax.md` and `coding/deviations.md`.

## File & Asset Rules

- Image formats: GIF/JPEG/PNG (`.gif`/`.jpg`/`.png`). SVG allowed on content pages. **WebP not permitted.**
- Resolution: 72 dpi.
- All files must have extensions; unify if a type is referenced with mixed extensions.
- Delete before delivery: `Thumb.db`, `.DS_Store`, files starting with `._`, `_notes` folder.
- Paths are document-root-relative (`/img/foo.jpg`), not relative (`../`).

## Meta Tags & Title

- `<meta name="keywords">` present, `content=""`.
- `<meta name="description">` omitted on login-required pages.
- `<title>` format: `[Page Name] | [Site Suffix]` (e.g. `製品情報 | MediChannel`). Matches `<h1>` at delivery — see `global/coding/html.md`.

## JavaScript

- jQuery **1.8.3** only, pinned by the template. No other JS library or version.
- Plugins are permitted; do not load additional library versions to support them.

## QA Scope Boundary — Client-Managed Zones

Excluded from all QA checks and must never be edited: **site header** (global nav, logo, login controls), **breadcrumbs** (`#breadcrumb`/`.breadcrumb`), **site footer** (copyright, site-wide links, legal disclaimers). Placeholder content in the breadcrumb (e.g. `/test.html`) is an **INFO** note for the client, not a defect to fix.

## Browser Targets (General Rendering)

Win11 Edge, Win11 Chrome, macOS Safari, and mobile simulation (iPhone/Safari, Android/Chrome, iPad/Safari).

## Validation

Always validate. Missing closing tags, spelling errors, and unnecessary styles are not acceptable; code with validation errors may not publish.
