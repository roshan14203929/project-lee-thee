# Orchestration

## State machine

Use `scripts/kit.py` for every state transition.

```text
source: EXTRACTING -> READY | FAILED
run: CREATED -> BUILDING -> VERIFYING -> COMPLETED
                           -> REFINING -> VERIFYING
                           -> NEEDS_REVIEW | FAILED
```

`COMPLETED`, `NEEDS_REVIEW`, and `FAILED` are terminal. Start a new run instead
of reopening one.

## Delegation sequence

1. Apply `source-reuse.md`. Request the source with one
   `--variant <label>=<url>` per supplied frame. If the controller returns
   `reused: true`, do not invoke extraction. When the user identifies changed
   nodes, create an incremental source from the current READY source and invoke
   `figma_extractor` / `figma-extractor` only for those nodes. For a genuinely
   new source, it owns only that source directory. Require it to record
   `page.variantScope`; supplied frames define fidelity scope and missing
   counterparts are not inferred. After the source reaches `READY`, run:
   ```
   kit.py spec-pattern-map <project> <page> <source>
   ```
   This writes `sources/<source>/spec/pattern-map.json`. Skip if the file
   already exists (reused source).
2. Create a run and a candidate. Invoke `page_builder` / `page-builder` alone.
   Supply the run directory path in the handoff. It writes `css-map.json` in
   the run directory after its pre-build analysis and before writing HTML.
3. Run the structural check described below, then deterministic static
   validation, browser rendering, and visual metrics.
4. Accept or reject the candidate. Copying into `generated/` is performed by
   `candidate-result`, not by a reviewer.
5. Invoke content, UI, accessibility, and technical reviewers. Include
   `page.variantScope` in each handoff so unsupplied widths remain diagnostic
   unless explicitly required. They are read-only and return one QA JSON
   object each. The main agent records them.
### Handoff ordering for QA reviewers

Structure every reviewer handoff with stable content first and variable content
last. Prompt caching requires a stable prefix; a run ID or candidate path at the
top of a handoff invalidates the cache on every run.

Order:
1. Effective guidelines — `kit.py guidelines <project> <page> --role <role>`
2. `pattern-map.json` path — `sources/<source>/spec/pattern-map.json` (stable
   per source; never changes after `source-ready`)
3. Source spec summary — `tokens` block from `spec/spec.json`
4. Content inventory — `kit.py inventory` filtered to the relevant sections
5. `page.variantScope`
---
6. Run ID, candidate ID, accepted candidate directory path
7. Render, diff, crop, and QA artifact paths
8. Candidate-specific metrics or prior grouped findings (repair rounds only)
9. `css-map.json` path — `runs/<run>/css-map.json` (repair-builder handoff only)

Keep items 1–5 textually identical across successive runs on the same page so
the cached prefix carries over. Never put a run ID, timestamp, or path before
the stable block. Note that any guideline edit re-keys every role's snapshot
hash, so the first read per role afterwards is a full cache miss and every
stored `--prev-hash` is dead; that is expected, not a fault.

6. Invoke `release_verifier` / `release-verifier` after the summary passes and
   record its verdict with `release-check`.
7. On failure, apply the repair grouping process below, then create a new
   candidate with `--from-accepted` and invoke `repair_builder` /
   `repair-builder` with the grouped findings (including root-cause
   hypotheses), the current accepted output, reference evidence, affected
   sections, and the paths to `pattern-map.json` and `css-map.json`. It owns
   only a new candidate directory.

## Structural check

Run this immediately after the builder writes its files and before
`verify-output.py`. It is a **smoke test for catastrophic layout misreads** — a
row built as a column, a grid collapsed to one track — not a fidelity gate. The
release thresholds in the effective guidelines remain the only quality bar.

1. Crop the above-the-fold band from the variant's reference PNG:
   `crop-region.py --image <reference.png> --output <structural-ref.png> --top 900`.
   Read the actual `height` from the sidecar JSON; a short reference is
   truncated, never padded.
2. Render the candidate to exactly that size:
   `render-page.py --root <candidate> --output <structural-cand.png>
   --width <spec.variants[].width> --height <height> --scale 1 --full-page false`.
3. `visual-diff.py --reference <structural-ref.png> --candidate <structural-cand.png>`.

Write all three artifacts under the candidate's `structural-check/` directory.

Reading the result:

- `status: ERROR` with `reason: dimension-mismatch` is a **harness** problem, not
  a layout problem. The reference was not exported at 1x, or its dimensions do
  not match the recorded `spec.variants` entry. Fix the evidence — do not report
  it to the builder as a visual failure and do not record it as a QA result.
- `pixelDifferencePercent` above **50%** means the above-the-fold composition is
  structurally wrong. Return the diff image to the builder with a targeted
  finding, e.g. "Hero layout direction or grid column count appears incorrect —
  review before completing the page."
- Below 50%, continue. Pixelmatch counts any channel change, so a uniform
  vertical offset alone can score 20–40% on a correct layout. Do not tighten
  this number into a fidelity gate; that is what the visual metrics step does.

Bounds:

- **Exactly one re-entry.** The builder still owns the candidate at this point
  (`candidate-result` has not run), so it corrects the structural issue in the
  same candidate directory. If the second check still exceeds the threshold,
  record the finding and proceed to full validation anyway — the QA gates and
  repair rounds handle it from there. Never loop.
- `render-page.py` exits non-zero on accessibility and structure diagnostics
  (h1 count, missing alt, duplicate IDs). Those are expected on a first
  candidate. Judge the render by whether the PNG was written, not by exit code.
- Skip the check only when the variant has no reference PNG. Log the skip.

## Parallelism

Parallelize independent read-heavy reviewers. Wait for every reviewer before
aggregating. Do not parallelize builders that would modify the same candidate,
generated directory, page record, or run record. If sections are built in
parallel, give every worker a separate candidate subdirectory and let the main
agent assemble them deterministically.

## Candidate decision

Reject a candidate when static validation fails, required content is missing,
the browser reports console/network/overflow failures, or visual metrics are
unavailable. `candidate-result --status accepted` mechanically requires
passing static, browser, and aggregate visual reports.

A visual report with `status: ERROR` means no comparison was performed — the
evidence is missing, not failing. Treat it as a harness fault: correct the
reference export or the render dimensions and re-measure. Do not record it as a
visual regression, do not send it to the repair-builder, and do not let it
consume a repair round.

For a repair candidate, compare it with the last accepted candidate:

- Reject if full-page difference regresses by more than 0.10 percentage points.
- Reject if peak-band difference regresses by more than 0.10 points.
- After repair round one, require at least 0.20 points of improvement in
  full-page or peak-band difference unless the targeted nonvisual failure is
  demonstrably fixed without visual regression.
- Preserve the previous accepted output byte-for-byte after rejection.

## Repair grouping

Before delegating to the repair-builder, group all failed findings by their
likely root cause. Pass each group — with its root-cause hypothesis — to the
repair-builder so it addresses causes rather than individual symptoms.

**Step 1 — Spatial grouping.** Findings whose `section` fields are identical,
or whose `bands` ranges overlap or sit within 100 px of each other, likely share
a layout root cause. Collect them into one spatial group. Group only on the
structured `section` and `bands` fields; do not infer locality from message
prose.

**Step 2 — Selector grouping.** Within a spatial group, look for a common CSS
selector or BEM block that all findings reference in their `evidence` fields.
If one is found, it is the most likely root cause.

**Step 3 — Write a hypothesis per group.** One sentence naming the probable
root cause, for example:
- "These 4 findings all target `.product-grid` — likely cause: column count
  is 2 in the candidate but 3 in the Figma source."
- "These 3 findings occur in the `.hero` section bands 0–900 px — likely
  cause: flex-direction is `column` instead of `row`."

**Step 4 — Write groups to disk, then pass to the repair-builder.** Before
delegating, write the complete group structure to
`qa/repair-round-<N>.json` in the current run directory (where N is the
one-based repair round number):

```json
{
  "runId": "run-###",
  "round": 1,
  "baseCandidateId": "candidate-###",
  "createdAt": "ISO-8601",
  "groups": [
    {
      "id": "A",
      "hypothesis": "one-sentence root-cause hypothesis",
      "findings": [
        { "id": "...", "kind": "ui", "severity": "high", "message": "..." }
      ]
    }
  ]
}
```

The repair-builder reads this file directly. Writing it before delegating
means the groups survive context compaction — if the orchestrator restarts
mid-repair it re-reads the file rather than re-grouping from scratch.

Structure the inline handoff prompt the same way for legibility:

```
Group A (root cause: <hypothesis>)
  - [finding-id] severity: message
  - [finding-id] severity: message

Group B (root cause: <hypothesis>)
  - [finding-id] severity: message
```

If the repair-builder determines a hypothesis is wrong, it must state the
actual root cause and return without making changes, so the orchestrator can
regroup before re-delegating.

Single isolated findings with no obvious peer receive their own group with the
hypothesis "No shared root cause identified — treat as isolated."

## Stop conditions

Stop and request user input when Figma is ambiguous, guidelines conflict with
the source, source variants contradict one another, essential assets are
unavailable, or changing copy/design intent is required.

Stop automatically and mark `NEEDS_REVIEW` when the configured repair cap is
reached, two consecutive candidates yield no meaningful improvement, a
required reviewer is unavailable, or an unresolved critical/high finding
remains.
