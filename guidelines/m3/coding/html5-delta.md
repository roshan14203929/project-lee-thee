# M3 / ThirdParty / CareNet — Deviations from the global baseline

> Everything in `global/coding/{html,css,assets-media}.md` applies as-is. This channel has two deltas:

## Font-size unit — **`rem`, never `px`**

The HTML5 root font-size is reliable and user-scalable, so use `rem` for all font sizes. Do not use `clamp()` — use breakpoints to vary size per viewport instead. `line-height` stays unitless.

## `.cst-page` container — no box-shadow

Never implement `box-shadow` on `.cst-page`, even if Figma's page-container node shows one. This reverses a pattern found in some earlier deliveries — treat any container shadow in the Figma spec as an artifact of the standalone mockup frame, not something to reproduce.

No other deltas beyond the two above. `<section>`/`<main>`/`<picture>` restrictions, the entity-escaping rules, and the CSS specificity workaround in `medichannel/coding/deviations.md` do not apply here.
