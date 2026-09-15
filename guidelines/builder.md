# Builder defaults

- Produce exactly `images/`, `index.html`, `base.css`, and `page.css` as the deployable output.
- Keep global element and token rules in `base.css`; keep page and component rules in `page.css`.
- Use semantic HTML and native controls before ARIA.
- Use CSS custom properties for repeated source tokens.
- Use Grid and Flexbox based on the extracted layout rather than absolute
  positioning except where the source genuinely requires layering.
- Keep selectors shallow and component-scoped.
- Store local assets in `images/` and use relative URLs.
- Implement responsive behavior from supplied variants; interpolate
  conservatively between them without hiding required content. Typography
  reflows by default — do not add breakpoint-specific font sizes unless the
  spec explicitly defines different values per breakpoint.
- When only one variant is supplied, preserve that variant's source intent and
  add only a conservative technical baseline. Do not invent an unsupplied
  mobile or desktop composition. A fixed-layout document may preserve a
  readable source canvas within a contained scroller instead of shrinking or
  redesigning its content.
- Do not use inline styles, `!important`, remote scripts, trackers, frameworks,
  or fabricated placeholder copy.
- Keep each semantic section's HTML independently replaceable for focused
  repairs: self-contained `<section>` blocks with clear IDs. Shared CSS
  component classes may span sections — section isolation applies to the HTML,
  not the CSS.
- Use `design-taste-frontend` only when the orchestrator routes it for a landing
  page, portfolio, marketing/editorial page, or redesign. State a one-line
  Design Read and apply it only to choices the source leaves unspecified.
- Exact Figma copy, geometry, tokens, assets, variants, user decisions, and
  these effective guidelines override Taste guidance. Taste must not introduce
  dependencies, remote resources, generated assets, or fabricated content.

## Interactive patterns

- **Tabs** are content visibility toggles — one panel shown, the others hidden.
  No routing, no page load. Implement as CSS-driven show/hide: the active tab
  and its panel share a state class; inactive panels use `display: none`.
- **Navigation rows** that link to sections on the same page are scroll anchors.
  Use `<a href="#section-id">`. The visual may look like a tab bar or button
  group — the behavior is always a same-page scroll to the target section.
- At mobile breakpoints, a horizontal tab or nav row collapses to a full-width
  dropdown. Pure CSS — no JavaScript. Hide the desktop row at the mobile
  breakpoint; show the dropdown in its place.

## CSS component architecture

Baseline CSS naming, value, and hygiene rules live in `guidelines/global/coding/*.md`,
delivered alongside this file, plus the active channel's `guidelines/<channel>/coding/*.md`
delta (e.g. font-size unit). The rules below are builder-specific and complement them.

- HTML sections are independently replaceable DOM units for repair targeting.
  CSS components are shared classes used across multiple sections. These are
  separate concerns — do not confuse them.
- Before writing any section HTML, define shared component classes in `page.css`
  first: buttons, cards, tags, typography utilities, and any pattern that
  appears in more than one section.
- Express per-section differences as BEM modifiers on the component, not as
  descendant selectors: `.btn` defines the base and `.btn--hero` adjusts its
  size, rather than `.hero .btn`. This keeps selectors shallow and keeps the
  component readable on its own.
- Do not copy a component's full ruleset into a section block. Reference the
  shared component class and add a modifier only where the section genuinely
  differs; a modifier declares only the properties that change.
- Open `page.css` with a comment block listing the component vocabulary, so the
  next agent can see the intended shared classes before reading any selector.
  This block is required: correct it rather than deleting it, and every repair
  that adds or renames a component class updates it.
- **MediChannel exception:** use `px` for all font sizes; `rem` is unreliable
  because the client template controls the root font-size. See
  `guidelines/medichannel/coding/deviations.md`.
