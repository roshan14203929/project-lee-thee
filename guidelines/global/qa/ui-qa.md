# UI QA defaults

- Inspect reference, candidate, and difference images at every source viewport.
- Treat only supplied variants as visual-fidelity targets. Checks at
  unsupplied widths are diagnostic unless responsive behavior there is an
  explicit user or page requirement; do not fail a desktop-only source for not
  matching an invented mobile layout.
- Check both full-page composition and localized bands.
- Attribute mismatches to semantic sections and concrete CSS properties.
- Verify responsive reflow, wrapping, clipping, stacking, sticky elements,
  overlays, menus, interactive states, and media cropping. Responsive
  breakpoint checks (viewport widths, no horizontal scroll) are covered in
  `technical-qa.md` — don't duplicate them here.
- Treat a numeric diff as evidence, not a substitute for visual diagnosis.
- Do not recommend broad rewrites when a bounded section repair is possible.

## Brand & Color

- All hex values match brand guidelines.
- If a brand color was changed for accessibility, flag for client notification (INFO severity).

## Typography

- Brand font used consistently throughout all text elements.
- Font size, weight, and line-height match design specs per section and element type.
- Minimum font size is 8px — flag anything smaller as a defect.
- Border widths and font-size/line-height must match the Figma spec exactly (see `global/coding/css.md`).

## Layout

- Layout and item order match the wireframe/Figma reference exactly.
- Base template correctly applied.
- Component positions, sizes, images, icons, and hierarchy match the reference.
- No layout breakdown at any breakpoint (no overlapping, clipping, or horizontal scroll).

## Icons & Buttons

- Icon styles consistent: same family, weight, and size throughout.
- Button styles (primary, secondary, disabled) consistent. Disabled state and
  edge-case variants require manual Peer Review verification — note this in findings.

## Visual Fidelity

- Colors match Figma exactly (verify via computed styles or eyedropper).
- Font family, size, weight, and line-height match design specs.
- Spacing, padding, and margins match design — no layout shifts.
- Images and icons are sharp, correct size, not stretched or distorted.
- Overall layout hierarchy and structure match the approved Figma.

## Interactive Elements

- All links and CTAs point to correct href targets; no broken links.
- Hover, focus, and active states display correctly in browser (focus-ring
  correctness itself is an accessibility-qa.md check — this is the visual
  confirmation pass).
- Hyperlinks match Figma component states — interactive state verification
  requires manual browser confirmation; note in findings.
