# MediChannel — Delivery & Process Rules

> Channel profile: XHTML 1.0 Strict, internal, 960 px fixed layout. Coding deltas live in `coding/`; QA specifics in `qa/`. This file covers delivery process/governance only.

## Template & Editable Area

- MC-001 Candidates build flat (`index.html`/`base.css`/`page.css`/`images/`, same
  contract as HTML5/M3) through BUILDING/VERIFYING/REFINING. The distributed
  `MediChannel_template` is versioned at
  `delivery-templates/medichannel/<template>/shell.html` (default
  `1column`); it is read-only structural authority, used only when the flat
  candidate is materialized into the nested AEM/JCR tree
  (`scripts/materialize-medichannel.py`, at release or on demand) — the
  builder never edits it directly.
- MC-002 The materializer writes HTML only between
  `<!-- ボディ部分編集可能エリアここから -->` and
  `<!-- ボディ部分編集可能エリアここまで -->` (the real marker used in every
  production ticket — not the English "Body editable area starts/ends here"
  phrasing sometimes seen in older candidates) by splicing in the flat
  candidate's own `<body>` content verbatim.
- MC-003 The shell's structure, including every marker comment and everything
  outside the editable area, stays byte-identical to
  `delivery-templates/medichannel/<template>/shell.html`; only the spliced
  editable-area content and the two per-article CSS `<link>` hrefs change.
  See `manifest.json` alongside the shell for the exact marker literals.
- MC-004 Load CSS/JS as external files, after the template's `desktop.css`/`script.css`.

## Document Type

- MC-019 **XHTML 1.0 Strict, not HTML5.** See `coding/xhtml-syntax.md` and `coding/deviations.md`.

## File & Asset Rules

- MC-005 Image formats: GIF/JPEG/PNG (`.gif`/`.jpg`/`.png`). SVG allowed on content pages. **WebP not permitted.**
- MC-006 Resolution: 72 dpi.
- MC-007 All files must have extensions; unify if a type is referenced with mixed extensions.
- MC-008 Delete before delivery: `Thumb.db`, `.DS_Store`, files starting with `._`, `_notes` folder.
- MC-009 Materialized paths are document-root-relative, never `../` — see `coding/deviations.md`.

## Meta Tags & Title

- MC-010 `<meta name="keywords">` present, `content=""`.
- MC-011 `<meta name="description">` omitted on login-required pages.
- MC-012 `<title>` format: `[Page Name] | [Site Suffix]` (e.g. `製品情報 | MediChannel`). Matches `<h1>` at delivery — see `global/coding/html.md`.

## JavaScript

- MC-013 jQuery **1.8.3** only, pinned by the template. No other JS library or version.
- MC-014 Plugins are permitted; do not load additional library versions to support them.

## QA Scope Boundary — Client-Managed Zones

- MC-015 Excluded from all QA and never edited: **site header** (global nav, logo, login controls), **breadcrumbs** (`#breadcrumb`/`.breadcrumb`), **site footer** (copyright, site-wide links, legal disclaimers).
- MC-016 overrides FID-013 inside MC-015 zones only. Placeholder content in the breadcrumb (e.g. `/test.html`) is an **INFO** note for the client, not a defect.

## Browser Targets (General Rendering)

- MC-017 Browser targets: Win11 Edge, Win11 Chrome, macOS Safari, and mobile simulation (iPhone/Safari, Android/Chrome, iPad/Safari).

## Validation

- MC-018 Always validate. Missing closing tags, spelling errors, and unnecessary styles are not acceptable; code with validation errors may not publish.
