# Accessibility QA defaults

- Inspect landmarks, heading hierarchy, control names, labels, alt text,
  keyboard reachability, focus order, focus visibility, and reduced motion.
- Check that hidden responsive content remains available when it is essential.
- Report source selector, user impact, severity, and a bounded correction.
- Prefer native element fixes over additional ARIA.
- `:focus-visible` must be present and visibly distinct on every interactive
  element, especially the PDF/approval-code link — never `outline: none` with
  nothing restored, never plain `:focus`, never combined with `:hover`.
- A heading-level component class (e.g. `cst-h1-banner`) must actually contain
  that heading level — flag a class implying `<h1>` that wraps a lower level.
- Accessibility rules are self-contained in this file. No external skill is required.
