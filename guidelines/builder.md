# Builder defaults

- BLD-001 Produce exactly `images/`, `index.html`, `base.css`, and `page.css` as the deployable output.
- BLD-002 Use semantic HTML and native controls before ARIA.
- BLD-003 Use CSS custom properties for repeated source tokens.
- BLD-004 Use Grid and Flexbox based on the extracted layout rather than absolute
  positioning except where the source genuinely requires layering.
- BLD-005 Keep selectors shallow and component-scoped.
- BLD-006 Store local assets in `images/` and use relative URLs.
- BLD-007 Implement responsive behavior from supplied variants; interpolate
  conservatively between them without hiding required content. Typography
  reflows by default — do not add breakpoint-specific font sizes unless the
  spec explicitly defines different values per breakpoint.
- BLD-008 When only one variant is supplied, preserve that variant's source intent and
  add only a conservative technical baseline. Do not invent an unsupplied
  mobile or desktop composition. A fixed-layout document may preserve a
  readable source canvas within a contained scroller instead of shrinking or
  redesigning its content.
- BLD-009 No remote scripts, trackers, frameworks, or fabricated placeholder copy.
- BLD-010 Keep each semantic section's HTML independently replaceable for focused
  repairs: self-contained `<section>` blocks with clear IDs. Shared CSS
  component classes may span sections — section isolation applies to the HTML,
  not the CSS.
- BLD-011 Use `design-taste-frontend` only when the orchestrator routes it for a landing
  page, portfolio, marketing/editorial page, or redesign. State a one-line
  Design Read and apply it only to choices the source leaves unspecified.
- BLD-012 Exact Figma copy, geometry, tokens, assets, variants, user decisions, and
  these effective guidelines override Taste guidance. Taste must not introduce
  dependencies, remote resources, generated assets, or fabricated content.

## Interactive patterns

- BLD-013 **Tabs** are content visibility toggles — one panel shown, the others hidden.
  No routing, no page load. Implement as CSS-driven show/hide: the active tab
  and its panel share a state class; inactive panels use `display: none`.
- BLD-014 **Navigation rows** that link to sections on the same page are scroll anchors.
  Use `<a href="#section-id">`. The visual may look like a tab bar or button
  group — the behavior is always a same-page scroll to the target section.
- BLD-015 At mobile breakpoints, a horizontal tab or nav row collapses to a full-width
  dropdown. Pure CSS — no JavaScript. Hide the desktop row at the mobile
  breakpoint; show the dropdown in its place.

## CSS architecture

Baseline naming, value, and hygiene rules are in `global/coding/css.md`, plus the
active channel's `<channel>/coding/` delta.

- BLD-016 HTML sections are independently replaceable DOM units for repair targeting;
  CSS components are shared classes spanning sections. Separate concerns.

## HTML and template delivery

- BLD-017 Treat delivery templates as read-only. Build and iterate in a separate file,
  then copy only finished code into the template's designated editable area.
  Never run a formatter over an entire delivery template.
- BLD-018 When available, rely on Prettier and `html-validate` for formatting, tag
  closing, doctype, charset, attribute quoting, and void-element validation;
  apply the platform coding-rules files to requirements those tools do not cover.
- BLD-019 When XHTML is explicitly required, convert the completed HTML only as the
  final local step and manually compare the result against
  `docs/xhtml-vs-html5.md`. Do not introduce an external model API for the
  conversion.
