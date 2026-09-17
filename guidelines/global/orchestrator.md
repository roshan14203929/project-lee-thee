# Run, gate, and release rules (primary orchestrator only)

> Audience: the primary orchestrator only. No `kit.py guidelines --role <role>`
> read delivers this file — it is absent from every role snapshot by design, not
> by omission. It is present in a run's `effective-guidelines.md` as release
> evidence, and `kit.py` enforces most of it mechanically.

## Precedence bookkeeping

- ORC-001 Write the resolved guideline source list and SHA-256 hash into every run.
  `kit.py` does this automatically; verify it is present before releasing.

## Run immutability

- ORC-002 A source snapshot is immutable after it becomes `READY`.
- ORC-003 A run may change only while its status is nonterminal.
- ORC-004 `COMPLETED`, `NEEDS_REVIEW`, and `FAILED` are terminal.
- ORC-005 Start a new run for every fresh attempt or user-approved alternative.
- ORC-006 Preserve every generated candidate and record acceptance or rejection.

## QA gates

- ORC-007 Maximum automatic repair rounds: 3.
- ORC-008 Full-page maximum pixel difference: 5%.
- ORC-009 Maximum localized horizontal-band difference: 12%.
- ORC-010 Candidate regression tolerance: 0.10 percentage points.
- ORC-011 Meaningful improvement required after the first repair: 0.20 percentage
  points in either full-page or peak-band difference.
- ORC-012 Required checks: `content`, `ui`, `accessibility`, and `technical`.
- ORC-013 A missing or unavailable required check is not a pass.
- ORC-014 Do not average independent checks into a passing score. Every gate must pass.

## Candidate acceptance

- ORC-015 Validate HTML, CSS, asset references, and required content before rendering.
- ORC-016 Accept a repair only if it fixes its targeted failure without exceeding the
  regression tolerance elsewhere.
- ORC-017 Reject malformed or regressing candidates and preserve the last accepted
  artifact exactly.
- ORC-018 Stop when all gates pass, the repair cap is reached, no meaningful
  improvement occurs, required Figma data is unavailable, or a user decision
  is necessary.

## Release

- ORC-019 Only the primary orchestrator may create `releases/v-###`.
- ORC-020 Release the exact accepted generated directory; do not rewrite it while
  copying.
- ORC-021 Include the run record, guideline snapshot, final QA summary, and checksums.
