# M3 / ThirdParty / CareNet — Deviations from the global baseline

> Everything in `global/coding/{html,css,assets-media}.md` applies as-is. Two deltas:

- M3D-001 resolves CSS-010. Font sizes in `rem`, never `px`. No `clamp()` — vary size per viewport with breakpoints. `line-height` stays unitless.
- M3D-002 resolves CSS-016. `.cst-page` carries neither `box-shadow` nor `border`, even when Figma's page-container node shows one. Treat both as mockup-frame artifacts.
