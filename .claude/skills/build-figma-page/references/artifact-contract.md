# Artifact contract

**HTML5 / M3 (flat)** — `project.json.platform` is `html5`:

```text
projects/<project>/
  project.json
  guidelines/*.md
  events/agent-events.jsonl
  pages/<page>/
    page.json
    guidelines/*.md
    sources/source-###/
      source.json
      raw/figma-*.json
      spec/spec.json
      spec/content-inventory.json
      spec/pattern-map.json
      asset-manifest.json
      assets/*
      reference/*.png
    runs/run-###/
      run.json
      effective-guidelines.md
      css-map.json
      candidates/candidate-###/
        candidate.json
        images/*
        index.html
        base.css
        page.css
      generated/
        images/*
        index.html
        base.css
        page.css
      visual/*
      qa/content.json
      qa/ui.json
      qa/accessibility.json
      qa/technical.json
      qa/summary.json
      qa/release-verifier.json
      qa/repair-round-*.json
    current/
      images/*
      index.html
      base.css
      page.css
    releases/v-###/
      site/
        images/*
        index.html
        base.css
        page.css
      run.json
      effective-guidelines.md
      qa/*
      release.json
```

**MediChannel (nested AEM JCR tree)** — `project.json.platform` is `medichannel`;
`{contentRoot}`, `{damRoot}`, `{cssRoot}` come from `project.json.delivery`,
`{articlePath}` from `page.json.articlePath` (see `commands.md`). Every
`candidates/candidate-###/`, `generated/`, `current/`, and `releases/v-###/site/`
payload below shares this same shape instead of the flat one:

```text
    candidates/candidate-###/ (and generated/, current/, releases/v-###/site/)
      candidate.json                                 (candidate dir only)
      content/{contentRoot}/{articlePath}.html
      content/dam/{damRoot}/{articlePath}/*           (image assets)
      etc/designs/code/{cssRoot}/{articlePath}/base.css
      etc/designs/code/{cssRoot}/{articlePath}/page.css
```

## Pattern map

`spec/pattern-map.json` is a mechanical derivation of `spec.json`, generated
by `kit.py spec-pattern-map` once after `source-ready`. It contains three
arrays: `componentGroups` (one entry per Figma component in `tokens.components`,
with its `figmaId`, `name`, `instanceCount`, and `sectionIds`),
`sectionProfiles` (one entry per section with its `role`, `components` list,
`layout` summary, and optional `background`), and `layoutGroups` (sections that
share an identical component set, labeled for quick lookup). The file is
immutable once written — a `READY` source's pattern-map must not be regenerated.
Pass its path in the stable prefix of every agent handoff.

## CSS map

`runs/run-###/css-map.json` is written by the page-builder to the run directory
after its pre-build analysis and before writing any HTML. It records one entry
per CSS vocabulary class: `cssClass` (selector string), `figmaComponent` (name
from `tokens.components`), `figmaId`, `sectionIds`, and `scope` (`"shared"` for
classes used in multiple sections, `"local"` for single-section classes). The
file persists for the lifetime of the run and is passed in the variable suffix
of the repair-builder handoff. It is not deployable output and is not included
in `generated/`, `current/`, or `releases/`.

## Source spec

`source.json` records a canonical `fingerprint`, `extractionMode` (`FULL` or
`INCREMENTAL`), optional `baseSourceId` and `changeSet`, per-variant
`referenceState`, and a bounded `callLedger`. Incremental sources retain an
immutable lineage to their READY base. Existing legacy sources may omit these
fields; derive their fingerprint in memory rather than rewriting them.

Candidates record `projectId`, `pageId`, `runId`, `sourceId`, and optional
`baseSourceId` for explicit provenance; they do not copy source extraction data.
`candidate.json` is lifecycle metadata, not deployable output. Candidate,
generated, current, and release site payloads contain exactly `images/`,
`index.html`, `base.css`, and `page.css` for HTML5/M3 — the nested MediChannel
shape above for `medichannel` projects; source snapshots continue to use
`assets/` for immutable Figma exports.

Write `spec/spec.json` with:

- `version: 1`
- `page`: source page identity, primary language, and `variantScope` containing
  the inferred mode, supplied labels, fidelity targets, confidence, and
  evidence
- `variants`: frame/node identity, label, width, height, and reference filename
- `tokens`: colors, typography, spacing, radii, shadows, and reusable components
- `sections`: ordered section identity, role, bounds per variant, text-node IDs,
  asset IDs, layout, visual values, and responsive relationships
- `assets`: node ID, local filename, media type, purpose, bounds, and variant
- `openQuestions`: unresolved source ambiguities with stable IDs
- `decisions`: immutable user decisions recorded by `resolve-question`

Write `spec/content-inventory.json` with `version: 1` and exact content items.
Every item requires `id`, `kind`, `text`, `required`, `nodeId`, and `sectionId`.

## Normalized spec storage

`spec/spec.json` and `spec/content-inventory.json` are derived views. The
immutable backend evidence stays in `raw/figma-*.json`, so anything normalization
drops from a derived view remains recoverable from the raw record.

`source-ready` rewrites both files into their normalized on-disk form, and
`python scripts/kit.py spec-compact` performs the same rewrite on demand.
Normalization is idempotent and removes JSON indentation. It also:

- Hoists repeated inventory `style` objects into a top-level `styles` table,
  replacing each item's `style` with its table key.
- Rewrites float `tokens.colors` values as CSS colors: `#rrggbb`, or
  `rgba(r,g,b,a)` when alpha is below `0.999`. Figma stores 8-bit sRGB as
  float32, so this reproduces the exact channel bytes. Colors already written
  as CSS strings are left alone.
- Drops `uses` and `nodeIds` from every token group. `count` remains as the
  ranking signal, and the full node-level provenance stays in
  `raw/figma-*.json`. This applies only to `tokens`; `sections` keeps its
  `textNodeIds`, `sourceNodeIds`, and `assetIds`, which are load-bearing.

An item `style` is therefore either an inline object or a `styles` key such as
`"s0"`. Resolve keys through `styles` when reading the file directly. The
`inventory` query resolves them for you and returns only the `styles` entries
its result actually uses.

Use token colors directly as CSS values; do not convert them again.

Do not read the whole inventory when a slice answers the question. Use
`python scripts/kit.py inventory` with `--sections` to map the page, then filter
by `--variant`, `--section`, `--kind`, `--node`, `--id`, `--text`, or
`--required`. It returns the seven identity/content fields by default; request
`--fields all` or an explicit field list only when geometry or typography is
needed, and page long results with `--limit` and `--offset`. Never read
`raw/figma-*.json`; it is unnormalized backend evidence, not an agent input.

Write `asset-manifest.json` even when no assets exist. Do not store temporary
Figma export URLs; they expire and may contain sensitive query parameters.

## QA object

Every QA agent returns:

```json
{
  "kind": "content",
  "status": "PASS",
  "runId": "run-001",
  "candidateId": "candidate-001",
  "checkedAt": "ISO-8601",
  "summary": "Short evidence-based result.",
  "findings": []
}
```

The controller stamps `runId` and `candidateId` while recording the report, so
reports from an earlier candidate cannot release a later candidate. Findings
require `id`, `severity`, and `message`; add `section`, `evidence`, and
`suggestedFix` when available. A finding tied to a vertical region also carries
`bands: { "start": <px>, "end": <px> }` in reference-image coordinates, so the
orchestrator can group findings by locality mechanically instead of parsing
prose. Valid statuses are `PASS`, `FAIL`, and `UNAVAILABLE`. Valid severities
are `critical`, `high`, `medium`, and `low`.

## Deterministic evidence locations

Store static checks under `visual/static.json`, browser diagnostics beside each
PNG as `<viewport>.png.json`, per-viewport diffs as
`visual/<viewport>-diff.json`, and their aggregate as `visual/summary.json`.
Store the structural check's reference crop, candidate render, and diff under
the candidate's `structural-check/` directory; it is pre-acceptance diagnostic
evidence and is not a QA gate. Temporary reviewer JSON may live in
`qa/incoming/`; `qa-record` copies and stamps the authoritative report.

A visual report may also carry `status: "ERROR"` with a `reason`. That means no
comparison was performed — most often `dimension-mismatch`, where the reference
was not exported at 1x or does not match its `spec.variants` dimensions. It is
missing evidence, not a visual regression, and it blocks acceptance without
being recorded as a failure or consuming a repair round.
