# MediChannel — Delivery & Process Rules

> Channel profile: XHTML 1.0 Strict, internal, 960 px fixed layout. Coding deltas live in `coding/`; QA specifics in `qa/`. This file covers delivery process/governance only.

## Template & Editable Area

- Candidates build flat (`index.html`/`base.css`/`page.css`/`images/`, same
  contract as HTML5/M3) through BUILDING/VERIFYING/REFINING. The distributed
  `MediChannel_template` is versioned at
  `delivery-templates/medichannel/<template>/shell.html` (default
  `1column`); it is read-only structural authority, used only when the flat
  candidate is materialized into the nested AEM/JCR tree
  (`scripts/materialize-medichannel.py`, at release or on demand) — the
  builder never edits it directly.
- The materializer writes HTML only between
  `<!-- ボディ部分編集可能エリアここから -->` and
  `<!-- ボディ部分編集可能エリアここまで -->` (the real marker used in every
  production ticket — not the English "Body editable area starts/ends here"
  phrasing sometimes seen in older candidates) by splicing in the flat
  candidate's own `<body>` content verbatim.
- The shell's structure, including every marker comment and everything
  outside the editable area, stays byte-identical to
  `delivery-templates/medichannel/<template>/shell.html`; only the spliced
  editable-area content and the two per-article CSS `<link>` hrefs change.
  See `manifest.json` alongside the shell for the exact marker literals.
- Load CSS/JS as external files, after the template's `desktop.css`/`script.css`.

## Document Type

**XHTML 1.0 Strict — not HTML5.** See `coding/xhtml-syntax.md` and `coding/deviations.md`.

## File & Asset Rules

- Image formats: GIF/JPEG/PNG (`.gif`/`.jpg`/`.png`). SVG allowed on content pages. **WebP not permitted.**
- Resolution: 72 dpi.
- All files must have extensions; unify if a type is referenced with mixed extensions.
- Delete before delivery: `Thumb.db`, `.DS_Store`, files starting with `._`, `_notes` folder.
- Paths are document-root-relative (`/img/foo.jpg`), not relative (`../`) —
  in the **materialized** artifact. The flat candidate itself uses ordinary
  relative `images/...` paths, same as HTML5/M3; `materialize-medichannel.py`
  rewrites them to the absolute DAM/CSS paths this rule requires.

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
