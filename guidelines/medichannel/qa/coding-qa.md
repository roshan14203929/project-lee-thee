# MediChannel — Coding QA

> Design QA (WF vs Design diff, brand/typography/logo compliance) and Content QA (copy accuracy, placeholder detection) live in `global/qa/ui-qa.md` and `global/qa/content-qa.md` — already channel-agnostic. This file covers the MediChannel-specific technical/visual-metric pass only. Editable area: only inside `.cst-page` — don't touch header/footer/nav.

## Typography metrics

Check that font-size and line-height rendered in the browser match the Figma spec, PC and SP separately. Report diffs as "location / Design side / implemented side".

## Coding guideline compliance

Check `index.html`/`base.css`/`page.css` against `medichannel/coding/*.md`, `medichannel/general-rules.md`, and `global/coding/*.md` — don't re-derive rules here, just verify against them. Report as "file + line number / current code / corrected code / reason".

## Noise reduction

Check in order: silent breakers (CSS variables, text) first, appearance last. Don't flag dead CSS with no matching element (that's `global/qa/technical-qa.md`'s orphaned-selector check). Don't flag a design-vs-implementation diff that already exists in Figma — Figma is source of truth. Split "no real impact" items as Info.
