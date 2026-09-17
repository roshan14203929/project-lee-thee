# Channel conversion

Apply this reference only when the user asks to port an already-accepted page
to the other platform (`html5`/M3 -> `medichannel`, or the reverse). It is an
alternate `BUILDING` phase for a **new page record on the target platform**,
not a replacement for extraction, QA, repair, or release. Every downstream
step (structural check, static/browser/visual validation, the four QA gates,
repair rounds, release) is unchanged.

## When to use it

Only when the user names an existing accepted run on the other platform as
the conversion source. Never invent a source page, never convert a run that
has no accepted candidate, and never convert into a page whose platform does
not match the requested direction.

## Sequence

1. **Target page must already exist** with the target platform set
   (`init-project --platform` / `set-platform`) and `init-page` run, same as
   any other page.
2. `kit.py new-conversion-run <target-project> <target-page> --direction
   m3-to-medichannel|medichannel-to-m3 --from-project <src-project>
   --from-page <src-page> --from-run <src-run> --from-candidate
   <src-accepted-candidate>`. This:
   - Rejects a direction whose target platform does not match the target
     project's recorded platform.
   - Rejects a candidate that is not the accepted candidate of the named
     source run.
   - Internally materializes the source's `READY` spec/assets/reference into
     a new source under the target page (`convert-source`, deduped by
     `provenance.convertedFrom` — rerunning it reuses the same source instead
     of duplicating it; pass `--force-new` only if the user explicitly wants a
     fresh copy).
   - Creates an ordinary run on the target page and stamps
     `run.json.convertedFrom` with the source project/page/run/candidate.
3. `kit.py transition <target-project> <target-page> <run> BUILDING`, then
   `kit.py new-candidate <target-project> <target-page> <run> --round 0
   --from-external <src-project>/<src-page>/<src-run>/<src-candidate>`. This
   freezes the source run's accepted `generated/` payload into the new
   candidate's `_conversion-input/` subdirectory — never into the candidate's
   own deployable payload, and never combinable with `--from-accepted` (that
   flag is only for same-page repair rounds).
4. Run the mechanical transform directly (deterministic script, not a
   subagent):
   ```
   python scripts/convert-platform.py --direction m3-to-medichannel|medichannel-to-m3 \
     --input <candidate-root>/_conversion-input --output <candidate-root> \
     --content-root <...> --dam-root <...> --css-root <...> --article-path <page.json.articlePath> \
     --output-report <candidate-root>/../conversion-report.json
   ```
   For `m3-to-medichannel`, `_conversion-input` is the flat HTML5 payload and
   `--output` is the candidate root, so it writes the nested JCR tree directly
   into the candidate. For `medichannel-to-m3`, `_conversion-input` is the
   JCR-shaped payload and `--output` is the candidate root, so it writes the
   flat `index.html`/`base.css`/`page.css`/`images/` directly.
   It applies only what is mechanically unambiguous — doctype/head swap, the
   structural-element table, void/boolean/quoting syntax, ampersand escaping,
   asset-path rewrite, and the flat<->JCR shape move — and never guesses at
   the rest.
5. Read `conversion-report.json`. A `status: REVIEW_NEEDED` with a non-empty
   `flagged` array (prohibited elements with no XHTML alternative, ambiguous
   Roman-numeral/circled-digit candidates) is not a build failure; it is
   worklist for the builder. Delegate to `page_builder` / `page-builder` (a
   fresh build role acting on this candidate, not a repair-builder — the
   payload was just mechanically generated, nothing is "accepted" yet)
   with: the effective guidelines for the target platform, `pattern-map.json`,
   the flagged list, and the candidate directory. It resolves each flagged
   item by hand per `guidelines/medichannel/coding/deviations.md` (M3 ->
   MediChannel character re-encoding) or by removing platform-risky
   characters per `guidelines/global/coding/assets-media.md` (MediChannel ->
   M3), and rewrites any prohibited element using the target platform's
   available structural elements. It must not touch `_conversion-input/` and
   must not alter exact source content beyond what conversion requires.
6. Delete or leave `_conversion-input/`; it is excluded from `verify-output.py`
   and from `generated/` automatically (see `artifact-contract.md`) so it never
   reaches release, but never treat it as part of the deployable payload
   during review.
7. Continue the ordinary workflow: structural check, full static/browser/visual
   validation, `candidate-result`, `VERIFYING`, the four QA gates (content, UI,
   accessibility, technical — the target platform's guidelines apply, same as
   any other run on that platform), repair rounds if needed, release verifier,
   `release`.

## Provenance

Three fields record lineage back to the origin; never edit them by hand:

- `source.json.provenance.convertedFrom` (materialized source):
  `{project, page, sourceId}`.
- `run.json.convertedFrom` (conversion run): `{project, page, run, candidate,
  direction}`.
- `candidate.json.convertedFrom` (the candidate seeded with `--from-external`,
  only): `{project, page, run, candidate}`.
