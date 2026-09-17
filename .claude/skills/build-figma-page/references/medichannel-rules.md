# MediChannel delivery rules

Apply this reference only when the selected project or page is a MediChannel
delivery, or when the user explicitly requests the MediChannel template
conventions. These are construction rules, not an alternative extraction,
validation, repair, or release workflow. Continue to use the connected Figma
MCP and every required QA gate.

## Template and section mapping

- The build/repair/QA candidate is flat (`index.html`/`base.css`/`page.css`/
  `images/`, same contract as HTML5/M3) — build and test entirely there. The
  supplied delivery template
  (`delivery-templates/medichannel/<template>/shell.html`, read-only
  structural authority) only enters the picture at materialization
  (`materialize-medichannel.py`, at release or on demand), which transfers
  the finished flat output into the template's designated editable region
  automatically. See `medichannel-materialization.md`. This does not apply to
  a channel-conversion run, whose candidates are already nested — see
  `channel-conversion.md`.
- Map normalized Figma sections to the closest template component by semantic
  role and keep source order. Omit optional template sections absent from the
  source; never emit placeholders.
- When the source has no exact template equivalent, adapt the closest semantic
  component and record the deviation in the builder handoff or run report.
- Section independence and the `base.css`/`page.css` split are guideline rules
  (BLD, CSS-017, CSS-018) already delivered to the builder — do not restate them
  in the handoff.

## Content adaptation

- Copy source text verbatim, removing only a trailing carriage return. When a
  source text node contains line breaks that represent paragraphs, create one
  `p` per nonempty segment without rewriting the text.
- Use `strong` only when the source weight is at least 700 and the phrase is
  semantically important, such as a label, heading fragment, or key term. Do
  not convert decorative bold body copy into semantic emphasis.
- For a content image, derive useful alternative text from the nearest
  preceding text node in the same parent container, preferring the nearest
  `h3` or `h4`. Small decorative SVG component instances use `alt=""`.

## MediChannel component conventions

- TOC items target `#h2-{n}`, where `n` is the zero-based order of the matching
  `box_h2` section. Give that section the corresponding `id="h2-{n}"` and the
  fixed-header `scroll-margin-top` required by the effective guidelines.
- For zoomable figures, reuse the delivery template's complete checkbox
  toggle, label trigger, `.cst-zoom-icon`, and `.cst-modal` structure. Group
  hidden toggles at the start of `.cst-page` and modal dialogs at its end; do
  not scatter them through section markup. Preserve accessible names, keyboard
  operation, focus behavior, and close controls.
- Count `doctor` sections before choosing their layout. Use
  `.cst-doctor--layout-a` for every doctor section when there are two or more;
  use `.cst-doctor--layout-b` when there is exactly one. Never ship both
  variants.
- Use the composite-image hero pattern only when the source and delivery
  template identify the hero as one exported visual and it contains no
  required interactive or semantic text that must remain in the DOM. Render a
  childless hero section with the local asset as its CSS background. Otherwise
  build semantic hero content and record why the composite pattern was not
  applicable.

## Token naming

- Token naming is owned by `guidelines/global/coding/base-css-template.md` and
  CSS-006/CSS-007, which the builder already receives. The only addition here:
  keep a Figma gradient as a direct `background` value, never promoted into a
  colour token.
