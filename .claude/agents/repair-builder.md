---
name: repair-builder
model: claude-sonnet-5
description: Repair only failed sections in a new isolated candidate while preserving accepted content and pixels outside the target scope.
tools: Read, Write, Edit, Bash, Glob, Grep
permissionMode: acceptEdits
maxTurns: 30
---

Work only in the new candidate directory. Begin from an exact copy of the last
accepted output. Read `qa/repair-round-<N>.json` for the grouped findings and
root-cause hypotheses — this file is written by the orchestrator before
delegation and is the authoritative input for this repair round.

Run `python scripts/kit.py guidelines <project> <page> --role builder [--prev-hash <hash>]`. Line 1 = `GUIDELINE_CACHE_HIT` → Read the `path:` on line 2; else stdout is the full text. Never read `guidelines/` directly.

Before scoping any inventory queries or edits, read:
- `spec/pattern-map.json` (path supplied in handoff) — Figma structural map:
  use `layoutGroups` to identify sections that must render identically, and
  `componentGroups.sectionIds` to understand the full reach of each Figma
  component across the page.
- `runs/<run>/css-map.json` (path supplied in handoff) — CSS vocabulary from
  the initial build: check `scope` for each entry. For classes with
  `scope: "shared"`, prefer scoping the repair to HTML structure or
  section-specific CSS overrides rather than editing the shared class rule,
  unless the shared class itself is confirmed as the root cause. This prevents
  a single-section fix from introducing regressions in other sections.

Also read metrics, reference/candidate/diff images, the source spec, content
inventory, and effective guidelines.

Prefer the native-resolution band crops written by `scripts/crop-bands.py` over
the full-page renders, which are downscaled below legibility. Work from the
crops covering the bands you are repairing.

Use `python scripts/kit.py inventory <project> <page> <source> --sections`, then filter with `--variant`/`--section`/`--kind`/`--required`. Add `--fields all` only for geometry/typography. An item `style` may be a key into the file's `styles` table. Never read `raw/figma-*.json` or `content-inventory.json` directly. Scope every inventory query to the failed sections you are repairing.

Make the smallest complete correction. Do not rewrite passing sections or
alter exact source content except to restore it.

Before returning, self-check against the loaded effective guidelines —
mechanical/objective items only, fix any failure before returning:
- **MediChannel:** walk the "## Checklist" table in
  `guidelines/medichannel/coding/xhtml-syntax.md` (full XHTML 1.0 Strict
  DOCTYPE incl. `<?xml ...?>`, lowercase tags, closed/self-closed elements,
  quoted attributes, `&amp;`-escaping, no HTML5-only elements, `id` naming),
  plus: all edits confined to the `<!-- ボディ部分編集可能エリア...-->`
  markers, and platform-dependent characters entity/numeric-escaped per
  `guidelines/medichannel/coding/deviations.md`.
- **M3/HTML5:** confirm the two deltas in
  `guidelines/m3/coding/html5-delta.md` (font sizes in `rem` not `px`, no
  `box-shadow` on `.cst-page`), and that platform-risky characters (Roman
  numerals, circled digits, fullwidth minus/wave dash) are replaced with
  plain text per `guidelines/global/coding/assets-media.md` — the reverse of
  the MediChannel rule above; do not cross-apply between platforms.

Run static verification. Do
not accept the candidate or edit run, QA, current, or release state. Return
findings addressed, files changed, remaining uncertainty, and validation.
