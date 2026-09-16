# QA contract

All four checks are mandatory and independently blocking.

## Content

Mechanically run `verify-output.py` with the source content inventory, then
have the content reviewer compare DOM/rendered content to Figma. Verify exact
copy, labels, links, buttons, forms, numbers, legal text, image purpose,
metadata, omissions, duplication, truncation, and fabricated content.

## UI

Render every supplied variant at its exact width. Compare each candidate PNG
with its matching Figma PNG using `visual-diff.py`. The UI reviewer must also
inspect reference, candidate, and diff images and check hierarchy, geometry,
typography, color, effects, media cropping, responsive reflow, overflow,
stacking, and interactive states.

Full-page references are tall enough that an image host downscales them
heavily; a 988x4725 desktop reference arrives at roughly 0.42 scale, where
body copy and fine print are no longer legible. Inspect the full-page images
**once** for layout, section ordering, and vertical rhythm, then run
`crop-bands.py` against each diff report and base pixel judgements on the
native-resolution crops it produces. Crops supplement the full-page pass; they
do not replace it. Record the band y-range of any finding drawn from a crop in
its `bands: { "start", "end" }` field as well as in the message — the
orchestrator groups findings by locality from that field, not from prose.

Use `spec.page.variantScope` as the fidelity boundary. Only supplied fidelity
targets receive pixel comparison and source-intent responsive findings. Do not
invent a mobile design or fail UI because a desktop-only fixed-layout/document
frame does not reflow like an unsupplied mobile variant. Additional widths may
still be checked for baseline technical integrity, keyboard access, and
catastrophic clipping, but they are diagnostic rather than visual release
gates unless the user or effective page guidelines explicitly require
responsive behavior at those widths.

Numeric thresholds come from `guidelines/global/general-rules.md`. A numeric pass does not
override an obvious structural or content mismatch.

Use fixed-height screenshots (`--full-page false`) when Figma references have
fixed viewport heights. Use full-page screenshots only when the reference was
exported using the same full-page convention. Combine every per-viewport diff
with `visual-summary.py`; candidate acceptance uses that aggregate.

`visual-diff.py` compares only images of identical dimensions. References are
exported at 1x matching their `spec.variants` width and height; render the
candidate at those same values, using `render-page.py --scale` when a reference
is at a higher density. A mismatch yields `status: ERROR`,
`reason: dimension-mismatch`, and exit 3 — missing evidence, not a regression.
Do not record it as a UI failure or convert it into findings; correct the
dimensions and re-measure.

## Accessibility

Check landmarks, single `h1`, heading order, names, labels, alt text, keyboard
operation, focus order and visibility, reduced motion, hidden content, and
native semantics. Record user impact and selector evidence.

## Technical

Run static verification and browser diagnostics. Check broken local assets,
unsafe paths, console errors, failed requests, horizontal overflow, invalid
document structure, remote runtime dependencies, and placeholders. Confirm the
page works through `scripts/serve.py` without the agent host.

## QA recording

The main agent writes each returned JSON object to `qa/incoming/` and records
it with `qa-record`. The controller stamps the current run and accepted
candidate. Accepting a new candidate clears old QA, making stale review reuse
impossible. Run `qa-summary` after all four have returned. Missing, stale, or
unavailable checks fail the summary.

After the four checks pass, the release verifier returns a JSON verdict with
`status: "READY"`, `runId`, `candidateId`, `checkedAt`, and `summary`. Record it
with `release-check`; the release command refuses missing or stale verdicts.

## PDF export (optional)

Only when the user has asked for a PDF deliverable: `content` (delegate to
`content-reviewer`) and `visual-cutoff` (delegate to `ui-reviewer`) are two
additional, independently blocking QA kinds scoped to a `pdf-###` export
rather than the HTML candidate. See `pdf-export.md` for the full sequence;
they are recorded and summarized the same way (`pdf-qa-record`,
`pdf-qa-summary`) but never substitute for, or get satisfied by, the four
checks above.
