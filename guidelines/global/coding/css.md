# CSS Rules (channel-agnostic baseline)

> Channel deltas (font-size unit, selector specificity, anchor targeting) live in `<channel>/coding/` — read that alongside this file.

## Naming

- BEM: `.block`, `.block__element`, `.block--modifier`. Hyphens, not underscores.
- No position/context in class names (`.references--footer` ✓, `.references__item_section_1` ✗).
- Prefix **all** custom classes with `cst-` (e.g. `.cst-hero`, `.cst-page`) when delivering inside an external template or CMS. Applies to all channels.
- Express per-section differences as BEM modifiers on a shared component (`.btn--hero`), not descendant selectors (`.hero .btn`). Do not copy a component's full ruleset into a section block.

## Variables & Values

- Follow the canonical token/reset structure in `base-css-template.md` — variable names and reset shape are mandatory; the actual values are per-design, and font-size *unit* still follows the channel rule (the template example itself uses `rem`, which does not override MediChannel's `px` rule).
- All colors via `:root` custom properties. No hardcoded hex outside `:root`.
- Semantic token names (`--color-primary`, `--font-xs`…`--font-xxl`, etc.) must map to the same design role consistently within one project. Token *values* may vary between sibling pages when their Figma designs differ; only the name-to-role mapping must stay consistent.
- Never substitute a spacing token for a font-size token or vice versa (e.g. `font-size: var(--space-xs1)`), even if the rendered value looks acceptable.
- Border widths must match the Figma spec exactly — 1px vs 2px is a real defect, not a rounding tolerance.
- Font-size **unit** is a channel delta — see `<channel>/coding/`. Font sizes are otherwise still tokens; don't hardcode.
- `padding` = inner space; `margin` = outer space between siblings.
- Use `:root` spacing variables for layout; one-off values (4px, 5px) don't need variables.
- `line-height` unitless (e.g. `1.5`).
- Duplicate property in the same selector → remove the first (overridden) one.
- No `!important`. Fix by removing the inline `style` that forces it.

## Architecture

- `.cst-page` container shadow/border is a channel decision, not a global default — see `<channel>/coding/`. Never copy Figma's page-container shadow/border effect without checking the channel rule first.
- Global element rules → `base.css`, not `page.css`.
- Before writing section HTML, define shared component classes (buttons, cards, tags, typography utilities) in `page.css` first. Open `page.css` with a comment block listing the component vocabulary; keep it updated as components are added or renamed.
- No duplicate selectors. No repeated full rulesets in media queries — only changed properties.
- No overlapping breakpoints setting the same value — merge them.
- Sections with `id` (TOC anchors) need `scroll-margin-top` matching header height (channel delta on which element carries `[id]` — see `<channel>/coding/`):
  ```css
  section[id] { scroll-margin-top: 70px; }
  ```

## Hygiene

- No commented-out CSS. Delete unused rules.
- Remove or fix stale comments.
- **Strip every comment from `base.css`/`page.css` before final delivery** — including the `page.css` component-vocabulary block and any section-divider comments. The vocabulary block is required *during* build for repair-round continuity (see `builder.md`); it is removed only at final delivery, not while the run is still in progress. For M3, `index.html` gets the same full comment strip. For MediChannel, `index.html` is excluded from this rule — see `medichannel/general-rules.md`.
- **No "patch note" blocks.** Merge a fix into its original rule. Do not append a dated comment + duplicate/overriding rule at the end of the stylesheet — this creates competing declarations for the same selector.
  ```css
  /* ❌ patch-note anti-pattern */
  .cst-page { padding: 20px; }        /* original rule */
  /* 2026-09-11 fix */
  .cst-page { padding: 16px; }        /* competing declaration, appended later */
  ```
  ```css
  /* ✅ update the original rule */
  .cst-page { padding: 16px; }
  ```
- After removing an element or consolidating icons, scan for CSS selectors that now match nothing in the HTML (orphaned rules) and delete them.
- Do not declare the same selector in multiple disconnected blocks — consolidate.
