# Run, gate, and release rules (primary orchestrator only)

> Audience: the primary orchestrator only. No `kit.py guidelines --role <role>`
> read delivers this file — it is absent from every role snapshot by design, not
> by omission. It is present in a run's `effective-guidelines.md` as release
> evidence, and `kit.py` enforces most of it mechanically.

## Precedence bookkeeping

- Write the resolved guideline source list and SHA-256 hash into every run.
  `kit.py` does this automatically; verify it is present before releasing.

## Run immutability

- A source snapshot is immutable after it becomes `READY`.
- A run may change only while its status is nonterminal.
- `COMPLETED`, `NEEDS_REVIEW`, and `FAILED` are terminal.
- Start a new run for every fresh attempt or user-approved alternative.
- Preserve every generated candidate and record acceptance or rejection.

## QA gates

- Maximum automatic repair rounds: 3.
- Full-page maximum pixel difference: 5%.
- Maximum localized horizontal-band difference: 12%.
- Candidate regression tolerance: 0.10 percentage points.
- Meaningful improvement required after the first repair: 0.20 percentage
  points in either full-page or peak-band difference.
- Required checks: `content`, `ui`, `accessibility`, and `technical`.
- A missing or unavailable required check is not a pass.
- Do not average independent checks into a passing score. Every gate must pass.

## Candidate acceptance

- Validate HTML, CSS, asset references, and required content before rendering.
- Accept a repair only if it fixes its targeted failure without exceeding the
  regression tolerance elsewhere.
- Reject malformed or regressing candidates and preserve the last accepted
  artifact exactly.
- Stop when all gates pass, the repair cap is reached, no meaningful
  improvement occurs, required Figma data is unavailable, or a user decision
  is necessary.

## Release

- Only the primary orchestrator may create `releases/v-###`.
- Release the exact accepted generated directory; do not rewrite it while
  copying.
- Include the run record, guideline snapshot, final QA summary, and checksums.
