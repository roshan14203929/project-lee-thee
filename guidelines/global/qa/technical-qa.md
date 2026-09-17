# Technical QA defaults

Procedures only. Report findings by ID; do not restate rules.

- Validate document structure, local asset references, console output, local request failures, viewport overflow, CSS loading, JavaScript errors.
- Reject unresolved placeholders, missing files, remote runtime dependencies, paths escaping the generated directory.
- Verify the page works from the included local server without the agent host.
- Keep reports machine-readable with exact evidence.
- Scan for orphaned selectors after element removal or icon consolidation.
- Cross-check `images/` against `src` usage, and `src` filename case against disk.
- Confirm delivered CSS carries zero comments, including a leftover component-vocabulary block. M3 `index.html` is in scope; on MediChannel check only the editable-area content — the template keeps its own comments and markers.
- In scope: CSS-022, CSS-023, CSS-024, CSS-026, CSS-027, AM-009, AM-010, FID-013.

## General rendering

- No console errors on the channel's browser targets -> MC-017 / M3-003.
- Renders correctly at 1280px and 375px. No unwanted horizontal scroll at any width.
- Validation clean before delivery -> MC-018.

## Delivery

- Files named per the project's delivery requirements.
