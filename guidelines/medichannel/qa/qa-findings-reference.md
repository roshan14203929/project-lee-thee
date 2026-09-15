# MediChannel — QA Findings Reference (AGENCY15-316 / -321 / -326)

Verified production defects from the MediChannel `fsn_hes_article` sibling series. Use as a QA checklist; each row cites the rule it violates.

| # | Finding | Ticket(s) | Rule violated | Severity |
|---|---|---|---|---|
| 1 | Font-size uses `rem` throughout instead of `px` | -316, -321, -326 | `coding/deviations.md` — font-size unit | High |
| 2 | `cst-h1-banner` component present but zero true `<h1>` elements on the page | -316 | `global/coding/html.md` — heading/class-name match | High |
| 3 | Completely flat heading structure (H2-only throughout), no `<h1>` | -326 | `global/coding/html.md` — one true `<h1>` | High |
| 4 | Same brand color named `--color-secondary` in one sibling, `--color-primary` in another | -316 vs -321 | `coding/design-token-consistency.md` | Medium |
| 5 | Plain `:focus` used instead of `:focus-visible` on PDF link | -326 | `global/coding/html.md` — focus-visible | Medium |
| 6 | `outline: none` on PDF link with no visible replacement | -321 | `global/coding/html.md` — focus-visible | Medium |
| 7 | Patch-note CSS blocks appended at end of file; selector declared multiple times (`.cst-page` 3×) | -316, -321, -326 | `global/coding/css.md` — hygiene | Medium |
| 8 | 8–20 orphaned CSS class selectors matching no HTML element | -316, -321 | `global/coding/css.md` / `global/qa/technical-qa.md` | Medium |
| 9 | Footer brand logos rendered as inline SVG instead of `<img>` | (pattern risk) | `global/coding/assets-media.md` — footer logos | Medium |
| 10 | Spacing token used as a font-size value | (pattern risk) | `global/coding/css.md` — token misuse | Low |
| 11 | Border width does not match Figma spec (1px vs 2px) | (pattern risk) | `global/coding/css.md` — border widths | Low |
| 12 | H1-as-image-banner wrapped in `<div>` with no `<h1>` at all, in some tickets, while others correctly wrap the same pattern in a real `<h1>` | (real inconsistency across production tickets) | `global/coding/html.md` — H1-as-image-banner | High |
