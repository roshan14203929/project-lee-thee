# MediChannel Guidelines

Overrides and additions on top of `global.md`. Read global first — only what differs is listed here.

---

## 1. Channel Overview

| | |
|---|---|
| Document type | XHTML 1.0 Strict, internal, 960 px fixed layout |
| Font-size unit | `px` |
| Image formats | GIF, JPEG, PNG only — **no WebP** |
| JavaScript | jQuery 1.8.3 only, pinned by the template |
| QA scope | Inside `.cst-page` only — header, breadcrumbs, and site footer are client-managed and excluded |
| Browser targets | Win11 Edge, Win11 Chrome, macOS Safari, iPhone/Safari, Android/Chrome, iPad/Safari |

XHTML is an XML application — one malformed tag breaks the whole page. HTML5 recovers gracefully; XHTML does not. Always validate before delivery.

---

## 2. HTML Rules

### Document Structure (XHTML 1.0 Strict)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja" lang="ja">
```

- `<?xml ...?>` on the first line. Full XHTML 1.0 Strict DOCTYPE — not `<!DOCTYPE html>`.
- `<html>` needs `xmlns`, `xml:lang`, and `lang` — values must match.
- Charset: `<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />` as the first element inside `<head>`. `<meta charset="UTF-8">` is invalid here.
- No `<main>`. Use `<div id="main" role="main">…</div>` instead.
- `<title>` format: `[Page Name] | [Site Suffix]` (e.g. `製品情報 | MediChannel`).
- `<meta name="keywords">` present, `content=""`. Omit `<meta name="description">` on login-required pages.

### Syntax Rules — violations cause XML parse errors

| Rule | Correct | Wrong |
|---|---|---|
| Tag case | `<div class="wrapper">` | `<DIV CLASS="wrapper">` |
| All elements closed | `<br />` `<img … />` | `<br>` `<img …>` |
| Attribute values | `<td rowspan="3">` | `<td rowspan=3>` |
| Boolean attributes | `<input disabled="disabled" />` | `<input disabled>` |
| Ampersand in URLs | `<a href="?a=1&amp;b=2">` | `<a href="?a=1&b=2">` |
| `id` values | `id="section-1"` | `id="1st-section"` |
| Block inside inline | Not allowed | `<a href="#"><div>…</div></a>` |

### Script & Style

- `type` attribute required: `<script type="text/javascript" src="…"></script>`, `<link rel="stylesheet" type="text/css" href="…" />`.
- Inline script/style blocks need CDATA wrapping:
  ```xml
  <script type="text/javascript">
  //<![CDATA[
    if (a < b && c > d) { /* ... */ }
  //]]>
  </script>
  ```
- No `async`/`defer` — control load order by placing `<script>` at the end of `<body>`.

### HTML5 → XHTML Element Replacements

| HTML5 | XHTML Alternative |
|---|---|
| `<main>` | `<div id="main" role="main">` |
| `<section>` | `<div class="section" role="region">` |
| `<article>` | `<div class="article" role="article">` |
| `<nav>` | `<div class="nav" role="navigation">` |
| `<header>` | `<div class="header" role="banner">` |
| `<footer>` | `<div class="footer" role="contentinfo">` |
| `<aside>` | `<div class="aside" role="complementary">` |
| `<figure>` | `<div class="figure">` |
| `<figcaption>` | `<p class="figcaption">` |
| `<mark>` | `<span class="mark">` |
| `<time>` | `<span class="time">` |

**Prohibited with no alternative:** `<picture>` `<source>` `<video>` `<audio>` `<canvas>` `<details>` `<summary>` `<dialog>` `<datalist>` `<output>` `<progress>` `<meter>` `<template>`.

### Content Model (stricter than HTML5)

- Block elements inside inline elements are forbidden (`<div>` inside `<a>` is invalid).
- No nested `<a>`, `<label>`, or `<form>`.
- `<button>` cannot contain `<input>`, `<select>`, `<textarea>`, `<label>`, `<button>`, `<form>`, `<fieldset>`.

### Accessibility

`role` and `aria-*` attributes cause DTD validation warnings but are read correctly by browsers — use them anyway.

### XHTML vs HTML5 Quick Reference

```html
<!-- XHTML invalid — HTML5 allows -->
<INPUT type="hidden" value="foo">     <!-- uppercase tag -->
<br>                                   <!-- no self-close -->
<img src="x.gif">                     <!-- no self-close, no alt -->
<input disabled>                      <!-- minimized boolean -->
<td rowspan=3>                        <!-- unquoted attribute -->
<a href="?a=1&b=2">                   <!-- bare & -->
<p>First<p>Second                     <!-- unclosed p -->
<a href="#"><div>block</div></a>      <!-- block in inline -->
```

### Delivery Checklist — XHTML Compliance

| Item | ✓ |
|---|---|
| Full XHTML 1.0 Strict DOCTYPE | |
| `<html>` has `xmlns`, `xml:lang`, `lang` (values match) | |
| Charset via `<meta http-equiv="Content-Type" ...>` | |
| All tag/attribute names lowercase | |
| All void elements self-closed with ` />` | |
| All attribute values quoted | |
| Boolean attributes have explicit values | |
| All `&` escaped as `&amp;` | |
| Inline `<script>`/`<style>` wrapped in CDATA | |
| No HTML5-only elements | |
| `id` values start with letter or underscore | |
| No block elements inside inline elements | |

---

## 3. CSS Rules

### Font-size unit — `px`, never `rem`/`em`

The template controls the root font-size, so `rem` is unreliable. All sizes (font-size, dimensions, spacing, borders) must use `px`. Omit units on `0` values. `line-height` stays unitless.

### CSS Naming

Lowercase element names in selectors only (XML is case-sensitive).

### Architecture

- Scope global element rules in `base.css` under `.cst-page` (e.g. `.cst-page a {}`).
- In `page.css`, beat that specificity with `.cst-page .your-class` (specificity 20), not a bare class (specificity 10).
- TOC anchor offset: use `div[id]`, not `section[id]` (no `<section>` element in XHTML):
  ```css
  div[id] { scroll-margin-top: 70px; }
  ```
- `.cst-page`: `max-width: 960px; margin: 0 auto;`. Never `min-width`. Never `box-shadow` or `border` on `.cst-page`.
- No bare unscoped resets — always scope to `.cst-page` (`.cst-page *`, `.cst-page ul`, …).

### Design Token Consistency Across Sibling Articles

MediChannel articles are often delivered as a sibling series (`article01`/`02`/`03`):
- Token **values** may vary between siblings — different pages, different designs.
- Token **names** must map to the same design role across the whole series. If `--color-primary` names one role in `article01`, it must name the same role in `article02` and `article03`.
- Cross-check token names (not values) across siblings before delivery.

---

## 4. Assets & Media

### Images

- `loading`, `fetchpriority`, and `srcset` are outside the DTD — supported by browsers but apply per project policy, not as a hard requirement.
- Image `src` values in the **materialized** artifact are document-root-absolute AEM DAM paths: `/content/dam/{damRoot}/{articlePath}/filename.ext`. The flat candidate uses ordinary relative `images/...` paths — the materializer script rewrites them.
- Never implement a border on `.cst-page`, even if Figma shows one.
- Resolution: 72 dpi. Formats: GIF, JPEG, PNG. SVG allowed on content pages. No WebP.

### Fonts

`crossorigin` must be written in full: `crossorigin="anonymous"` (XHTML requires all attribute values quoted).

### Character References

All platform-dependent characters must use numeric or named entity references. The table below covers both general MediChannel rules and M3→MediChannel migration conversions.

| Source | MediChannel target | Rule |
|---|---|---|
| `III` (plain ASCII Roman numerals) | `&#8546;` (Ⅲ) | Convert ASCII Roman numerals to the proper Unicode Roman numeral entity |
| `(1) (2) (3)` parenthesized numbers | `&#9312;`–`&#9317;` (①–⑥) | Convert to circled-digit entities |
| `＜` `＞` (fullwidth symbols) | `&lt;` `&gt;` | Convert fullwidth comparison symbols to halfwidth entity-escaped equivalents |
| `&` unescaped in `href`/query strings | `&amp;` | Always HTML-escape ampersands in links — MediChannel only; M3 (HTML5) does not require this |
| `—` `&nbsp;` fullwidth `〜` | `&#8213;` `&#160;` `&#65374;` | No conversion needed — carry over as-is |
| `―` (horizontal bar) | `&#8213;` | Use entity in both channels |
| `<sup>` / `<sub>` tags | unchanged | Copy footnote/subscript markers exactly — no conversion |
| `®` registered symbol | `&reg;` | Use `&reg;` in MediChannel |
| `&nbsp;` | `&#160;` | Prefer numeric ref over named entity in XML mode |
| `&copy;` | `&#169;` | Prefer numeric ref over named entity in XML mode |
| `&mdash;` | `&#8212;` | Prefer numeric ref over named entity in XML mode |

Flag any platform-dependent characters found in the Figma source back to the design team.

---

## 5. QA

### Typography Metrics (MediChannel-specific)

Check font-size and line-height rendered in the browser against the Figma spec, PC and SP separately. Report diffs as: `location / Design side / Implemented side`.

### Coding Guideline Compliance

Verify `index.html`/`base.css`/`page.css` against these guidelines. Report as: `file + line number / current code / corrected code / reason`.

Check order — silent breakers first, appearance last:
1. CSS variables and token values
2. Text content
3. Layout and spacing
4. Visual appearance

Do not flag a design-vs-implementation diff that already exists in Figma — Figma is source of truth. Split "no real impact" items as Info.

### QA Scope

Only inside `.cst-page`. Do **not** touch or flag:
- Site header (global nav, logo, login controls)
- Breadcrumbs (`#breadcrumb` / `.breadcrumb`) — placeholder `/test.html` is an **INFO** note for the client, not a defect
- Site footer (copyright, site-wide links, legal disclaimers)

### Production Defect Checklist (AGENCY15-316 / -321 / -326)

| # | What to check | Severity |
|---|---|---|
| 1 | Font-size uses `rem` instead of `px` | High |
| 2 | `cst-h1-banner` class present but no true `<h1>` on the page | High |
| 3 | Flat heading structure (H2-only), no `<h1>` at all | High |
| 4 | H1-as-image-banner wrapped in `<div>` with no real `<h1>` | High |
| 5 | Plain `:focus` instead of `:focus-visible` on PDF link | Medium |
| 6 | `outline: none` on PDF link with no visible replacement | Medium |
| 7 | Patch-note CSS blocks; same selector declared multiple times | Medium |
| 8 | Orphaned CSS selectors matching no HTML element | Medium |
| 9 | Footer brand logos rendered as inline SVG instead of `<img>` | Medium |
| 10 | Same brand color role named differently across sibling articles | Medium |
| 11 | Spacing token used as a font-size value | Low |
| 12 | Border width does not match Figma spec (1px vs 2px) | Low |

---

## 6. Delivery

### Build → Materialize Flow

1. **Build flat** — `index.html`, `base.css`, `page.css`, `images/` (same as HTML5/M3).
2. **Materialize** — run `scripts/materialize-medichannel.py` to splice the flat candidate into the versioned shell template at `delivery-templates/medichannel/<template>/shell.html`. The materializer handles:
   - Writing content only between the Japanese editable-area markers (`<!-- ボディ部分編集可能エリアここから -->` / `<!-- ボディ部分編集可能エリアここまで -->`).
   - Rewriting relative `images/...` paths to absolute AEM DAM paths.
   - Updating the two per-article CSS `<link>` hrefs.
3. Everything outside the editable area in the shell stays **byte-identical** to the template — never edit it directly.

### File & Asset Rules

- Image formats: GIF, JPEG, PNG only. SVG allowed on content pages. **No WebP.**
- Resolution: 72 dpi.
- All files must have extensions.
- Delete before delivery: `Thumb.db`, `.DS_Store`, files starting with `._`, `_notes` folder.

### CSS & JavaScript

- Load `base.css`/`page.css` as external files, after the template's `desktop.css`/`script.css`.
- jQuery **1.8.3** only. No other JS library or version. Plugins permitted.

### Validation

Always validate. Missing closing tags, spelling errors, and unnecessary styles are not acceptable; code with validation errors may not publish.

## Design-token consistency across a sibling series (provenance)

MediChannel articles are frequently delivered as a sibling series — same pattern,
different design variations (`article01`/`02`/`03`). Value variation between
siblings is expected; the *semantic role mapping* must not vary. Found in
production: one sibling named a colour `--color-secondary` while another used
`--color-primary` for the same role. The shipped rule is
`guidelines/medichannel/coding/deviations.md` (Design tokens) plus the
name-to-role rule in `guidelines/global/coding/css.md`.
