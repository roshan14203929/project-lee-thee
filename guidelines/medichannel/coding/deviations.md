# MediChannel — Deviations from the global baseline

> Everything in `global/coding/{html,css,assets-media}.md` applies unless overridden below.

## Font-size unit — **`px`, never `rem`/`em`**

- MCD-010 resolves CSS-010. All sizes (font-size, dimensions, spacing, borders) in `px` — the template controls root font-size, so `rem` is unreliable. Omit units on `0`. `line-height` stays unitless.

## Content model (stricter than HTML5)

- MCD-001 Block elements inside inline elements are forbidden (`<div>` inside `<a>` invalid).
- MCD-002 No nested `<a>`, `<label>`, or `<form>`.
- MCD-003 `<button>` cannot contain `<input>`, `<select>`, `<textarea>`, `<label>`, `<button>`, `<form>`, `<fieldset>`.

## Accessibility

- MCD-011 `role` and `aria-*` cause DTD validation errors but are read correctly by browsers — use them anyway.

## Images

- MCD-012 relaxes AM-003. `loading`, `fetchpriority`, `srcset` are outside the DTD — supported by modern browsers but not mandatory here; apply per project policy.

- MCD-013 Image `src` in the **materialized** artifact is a document-root-absolute AEM DAM path (`/content/dam/{damRoot}/{articlePath}/filename.ext`) — an article's images sit in a separate part of the JCR tree from its HTML. The flat candidate you build uses ordinary relative `images/...`; `materialize-medichannel.py` rewrites them. `{damRoot}`/`{articlePath}` come from delivery config (`general-rules.md`).

- MCD-014 resolves CSS-016. `.cst-page` carries neither `border` nor `box-shadow`, even when Figma's page-container node shows one. Treat both as mockup-frame artifacts.

## Fonts

- MCD-015 Write `crossorigin` in full (`crossorigin="anonymous"`) — an instance of MCX quote-all-attribute-values, not a separate rule.

## Character references

- MCD-016 overrides AM Character Encoding Preflight. All platform-dependent characters use numeric or named entity references per the client spec. The table covers both general MediChannel rules and M3->MediChannel migration.

| Source | MediChannel target | Rule |
|---|---|---|
| `III` (plain ASCII Roman numerals) | `&#8546;` (Ⅲ) | Convert ASCII Roman numerals to the proper Unicode Roman numeral entity |
| `(1) (2) (3)` parenthesized numbers | `&#9312;`–`&#9317;` (①–⑥) | Convert to circled-digit entities |
| `＜` `＞` (fullwidth symbols) | `&lt;` `&gt;` | Convert fullwidth comparison symbols to halfwidth entity-escaped equivalents |
| `&` unescaped in `href`/query strings | `&amp;` | Always HTML-escape ampersands in links — MediChannel only; M3 does not require this |
| `—` `&nbsp;` fullwidth `〜` | `&#8213;` `&#160;` `&#65374;` | No conversion needed — carry over as-is |
| `―` (horizontal bar) | `&#8213;` | Use entity in both channels |
| `<sup>` / `<sub>` tags | unchanged | Copy footnote/subscript markers exactly — no conversion |
| `®` registered symbol | `&reg;` | Use `&reg;` in MediChannel |
| `&nbsp;` | `&#160;` | Prefer numeric ref over named entity in XML mode |
| `&copy;` | `&#169;` | Prefer numeric ref over named entity in XML mode |
| `&mdash;` | `&#8212;` | Prefer numeric ref over named entity in XML mode |

- MCD-017 Flag platform-dependent characters found in the Figma source back to the design team.

## Design tokens

- MCD-004 MediChannel articles ship as sibling series (`article01`/`02`/`03`). Cross-check token *names*, not values, against the siblings before delivery. Extends the name-to-role rule in `global/coding/css.md`.

## CSS naming

- MCD-018 Lowercase element names in selectors (XML is case-sensitive).

## CSS architecture

- MCD-005 Scope global element rules in `base.css` under `.cst-page` (e.g. `.cst-page a {}`).
- MCD-006 In `page.css`, beat that specificity with `.cst-page .your-class` (specificity 20) rather than a bare class (specificity 10).
- MCD-007 TOC anchor offset goes on `div[id]`, not `section[id]` (no `<section>` element exists here):
  ```css
  div[id] { scroll-margin-top: 70px; }
  ```
- MCD-008 `.cst-page` itself: `max-width: 960px; margin: 0 auto;`. Never `min-width`.
- MCD-009 No bare unscoped resets (`* { margin: 0; }`) — scope to `.cst-page` (`.cst-page *`, `.cst-page ul`, …).
