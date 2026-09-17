# HTML Rules (channel-agnostic baseline)

> Prettier + html-validate handle formatting, closing tags, doctype, charset, quoting, void elements. Channel deltas live in `<channel>/coding/` — read that alongside this file.

## Document Structure

- HTML-001 `<html lang="…">` must match page language.
- HTML-002 `<title>` is left **empty** (`<title></title>`) on initial build.
- HTML-003 The footer PDF/e-PI link is left with `href="#"` as a placeholder on initial build (same two-stage pattern as `<title>`), `target="_blank"` set from the start. Before delivery, `href` is filled in with the real PDF path.
- HTML-004 Exactly one `<main>` per page (channel delta: MediChannel has no `<main>` — see `medichannel/coding/xhtml-syntax.md`).
- HTML-005 `.container` on a `<div>` inside `<section>`, never on `<section>` itself.

## Semantic HTML

- HTML-006 Use `<h2>`/`<h3>` for section titles. Never a styled `<div>` as heading.
- HTML-007 Exactly one `<h1>`. No skipped heading levels. A component class that implies a heading level (e.g. `cst-h1-banner`) must actually contain that heading — a class name promising `<h1>` that wraps `<h2>` or nothing is a defect.
- HTML-008 When Figma's H1 is a graphical/image banner (not real text), wrap the `<img>` directly in a real `<h1>`: `<h1><img src="…" alt="…"></h1>`. Never ship a heading-shaped `<div>` with no `<h1>` at all.
- HTML-009 Tags for meaning, not appearance. Meaningful emphasis → `<strong>`/`<em>`, not `<b>`/`<i>`.
- HTML-010 No spacer `<div>`. No empty elements or blank `class` attributes.

## Accessibility

- HTML-011 Every `<img>` needs `alt`. Content → descriptive; decorative → `alt=""`.
- HTML-012 `alt` describes what the image shows, not its role. For PNG content images, derive from the nearest preceding `<h3>`/`<h4>`.
- HTML-013 `aria-label` in page language.
- HTML-014 Never remove focus outlines without a visible replacement.
- HTML-015 Use `:focus-visible` for keyboard styles — never plain `:focus`, never combined with `:hover` in one rule. All focus styles on a page share one token; no second visually distinct focus-ring color.

## HTML Hygiene

- HTML-016 No inline `style="…"`. Move to a CSS class.
- HTML-017 No commented-out blocks. Delete unused code; use `<!-- TODO: reason -->` for intentional omissions.
- HTML-018 No `href="javascript:void(0)"`. Use `<button>` for actions, or `href="#"` + `preventDefault()`.
