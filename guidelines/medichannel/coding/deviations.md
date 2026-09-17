# MediChannel — Deviations from the global baseline

> Everything in `global/coding/{html,css,assets-media}.md` applies unless overridden below.

## Font-size unit — **`px`, never `rem`/`em`**

The template controls the root font-size, so `rem` is unreliable. All sizes (font-size, dimensions, spacing, borders) are `px`. Omit units on `0` values. `line-height` stays unitless.

## Content model (stricter than HTML5)

- Block elements inside inline elements are forbidden (`<div>` inside `<a>` invalid).
- No nested `<a>`, `<label>`, or `<form>`.
- `<button>` cannot contain `<input>`, `<select>`, `<textarea>`, `<label>`, `<button>`, `<form>`, `<fieldset>`.

## Accessibility

`role` and `aria-*` cause DTD validation errors but are read correctly by browsers — use them anyway.

## Images

`loading`, `fetchpriority`, and `srcset` are outside the DTD; supported by modern browsers but not mandatory here — apply per project policy rather than as a hard requirement.

Image `src` values are document-root-absolute AEM DAM paths (`/content/dam/{damRoot}/{articlePath}/filename.ext`), never relative `images/...` — the article's images live in a completely separate part of the JCR tree from the article HTML itself. `{damRoot}` and `{articlePath}` come from the project's and page's delivery configuration (see `general-rules.md`).

Never implement a border on `.cst-page`, even if Figma's page-container node shows one.

## Fonts

`crossorigin` must be written in full (`crossorigin="anonymous"`) — an instance of the general "quote all attribute values" syntax rule, not a separate rule.

## Character references

All platform-dependent characters must use numeric or named entity references per the formal client spec. The table below covers both general MediChannel rules and M3→MediChannel migration conversions.

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

Flag any platform-dependent characters found in the Figma source back to the design team.

## CSS naming

Lowercase element names in selectors only (XML is case-sensitive).

## CSS architecture

- Scope global element rules in `base.css` under `.cst-page` (e.g. `.cst-page a {}`).
- In `page.css`, beat that specificity with `.cst-page .your-class` (specificity 20) rather than a bare class (specificity 10).
- TOC anchor offset goes on `div[id]`, not `section[id]` (no `<section>` element exists here):
  ```css
  div[id] { scroll-margin-top: 70px; }
  ```
- `.cst-page` itself: `max-width: 960px; margin: 0 auto;`. Never `min-width`.
- No bare unscoped resets (`* { margin: 0; }`) — scope to `.cst-page` (`.cst-page *`, `.cst-page ul`, …).
