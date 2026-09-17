# Content, UI, and quality bar (all build and review roles)

Shared acceptance bar for the builder and every QA role. Channel deltas live in
`guidelines/<channel>/`; check procedures live in `guidelines/global/qa/`.

## Content fidelity

- Preserve every required visible string exactly, including punctuation,
  capitalization, numerals, labels, legal copy, and calls to action.
- Do not add marketing copy, links, testimonials, prices, claims, or features
  not present in the source or explicitly requested.
- Do not omit visually present content because it appears repetitive.
- Record source text in `content-inventory.json` and verify the output against
  it mechanically before semantic review.

## UI fidelity

- Match hierarchy, geometry, spacing, alignment, typography, colors, borders,
  radii, shadows, opacity, gradients, imagery, and stacking.
- Render and inspect every supplied reference viewport.
- Perform blocking visual-fidelity and responsive-intent checks only at
  supplied variant widths. The 320, 375, 768, 1024, and 1440 pixel matrix is a
  baseline diagnostic for unsupplied widths unless the user or page guidelines
  explicitly require those widths; do not treat an absent mobile or desktop
  design as an implicit variant.
- At diagnostic-only widths, block only concrete technical or accessibility
  failures that are independent of an invented layout, such as unreachable
  controls, page-level accidental overflow, or hidden essential content. Do
  not fail UI solely because a desktop-only fixed-layout or image-document page
  preserves its source canvas instead of reflowing like a mobile design.
- Verify hover, focus-visible, active, disabled, menu, modal, and form states
  when those states exist.

## Accessibility and technical quality gates

- Use semantic landmarks and exactly one page-level `h1`.
- Preserve logical heading order and keyboard operation.
- Give controls accessible names and inputs associated labels.
- Reject broken local assets, console errors, failed local network requests,
  horizontal overflow, invalid document structure, and placeholder content.
