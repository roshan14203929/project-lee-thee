# Technical QA defaults

- Validate document structure, local asset references, console output, local
  request failures, viewport overflow, CSS loading, and JavaScript errors.
- Reject unresolved placeholders, missing files, remote runtime dependencies,
  and paths that escape the generated directory.
- Verify the page works from the included local server without the agent host.
- Keep reports machine-readable and include exact evidence.
- Scan for CSS selectors that match nothing in the HTML (orphaned rules) after
  any element removal or icon consolidation.
- Confirm every file in `images/` is referenced by `src` somewhere in the HTML;
  flag unreferenced files.
- Confirm `src` filename case matches the file on disk exactly.
- Confirm delivered `base.css`/`page.css` (both channels) and M3's `index.html`
  contain zero comments — flag any surviving comment, including a leftover
  component-vocabulary block, as a defect. For MediChannel, only check the
  editable-area content for stray comments; the template outside it retains
  its own comments (including the editable-area markers) unchanged.

## General Rendering

- Page renders without console errors in target browsers. Browser-target
  matrix is channel-specific — see `<channel>/general-rules.md`.
- Page displays correctly at 1280px (desktop) and 375px (mobile).
- No unwanted horizontal scroll at any viewport width.

## Delivery

- All files stored with correct naming convention per project delivery requirements.
