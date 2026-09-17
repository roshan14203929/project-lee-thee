# UI QA defaults

Procedures only. Report findings by ID; do not restate rules. Fidelity scope is
FID-005 to FID-009 — blocking checks at supplied variants only, diagnostic
elsewhere. Responsive breakpoint and horizontal-scroll checks belong to
`technical-qa.md`; do not repeat them here.

- Inspect reference, candidate, and difference images at every source viewport.
- Check both full-page composition and localized bands.
- Attribute mismatches to semantic sections and concrete CSS properties.
- Verify reflow, wrapping, clipping, stacking, sticky elements, overlays, menus, interactive states, media cropping.
- Treat a numeric diff as evidence, not a substitute for visual diagnosis.
- Do not recommend a broad rewrite where a bounded section repair is possible.

## Visual checks

- Colors match Figma exactly (computed styles or eyedropper) -> CSS-006. A brand colour changed for accessibility is INFO, flag for client notification.
- Brand font used consistently. Font size, weight, line-height match spec per section and element type. **Minimum 8px — anything smaller is a defect.**
- Border widths exact -> CSS-009.
- Spacing, padding, margins match the design. Layout, item order, component position/size/hierarchy match the reference. Base template correctly applied.
- No layout breakdown at any breakpoint: overlapping or clipping.
- Images and icons sharp, correct size, not stretched. Icon family, weight, size consistent throughout.

## Interactive elements

- Links and CTAs resolve to the correct `href`; no broken links.
- Hover, focus, and active states render correctly. Focus-ring *correctness* is an `accessibility-qa.md` check -> HTML-015; this is the visual confirmation pass.
- Button variants (primary, secondary, disabled) consistent. Disabled and edge-case variants, and Figma component states, need manual browser/Peer Review confirmation — say so in findings.
