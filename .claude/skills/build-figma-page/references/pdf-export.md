# PDF export

Apply this reference only when the user asks for a PDF deliverable alongside
(or instead of) the HTML release. It is a side artifact attached to a run —
it never changes `run.json`'s own status machine and does not require the run
to have reached `COMPLETED` first, only that it has an accepted candidate.

## Sequence

1. `kit.py new-pdf-export <project> <page> <run> --from-candidate
   <accepted-candidate-id>`. Rejects a candidate that is not the run's
   `acceptedCandidateId`. Creates `runs/<run>/pdf/pdf-###/pdf.json` with
   `status: PENDING` and returns its root.
2. Run the renderer directly (deterministic script, not a subagent):
   ```
   python scripts/render-pdf.py --root <run>/generated --output <pdf-root>/index.pdf \
     [--entry index.html] [--width 960] [--page-format A4] \
     --strip-report <pdf-root>/strip-report.json
   ```
   It comment-wraps non-content interactive elements it can identify
   unambiguously — whole `<nav>` blocks and `target="_blank"` anchors — and
   only flags the rest (`<button>`, an external link with no `target="_blank"`)
   for a human/agent decision; it never deletes or guesses. It also reports
   any heading/image/table/figure that straddles a page boundary at the given
   `--page-format`.
3. `kit.py pdf-result <project> <page> <run> <pdf-id> --status ready|failed
   --file <meta.json>` records `pageCount` and `straddlingElements` (or
   whatever subset of `strip-report.json` you choose to persist) onto
   `pdf.json`. Use `--status failed` if `render-pdf.py` exits non-zero.
4. Two independent QA gates are required, same mechanics as the four HTML
   QA kinds (`pdf-qa-record`, `pdf-qa-summary`; both must PASS before
   release):
   - **`content`** — delegate to `content-reviewer` scoped to the PDF: confirm
     nothing that should remain visible was comment-wrapped, and that every
     comment-wrapped element is genuinely non-content (navigation or an
     external CTA), not omitted body copy.
   - **`visual-cutoff`** — delegate to `ui-reviewer` scoped to the rendered
     PDF and `strip-report.json`'s `straddlingElements`: open the PDF at each
     reported page boundary and judge whether the break is visually acceptable
     (a long paragraph splitting is normal) or actually bad (a heading
     orphaned from its content, a table or figure sliced through the middle).
   Record each as the usual QA JSON object
   (`{"kind": "content"|"visual-cutoff", "status", "summary", "findings"}`)
   with `qa/incoming/` staging, then `pdf-qa-record ... --file <qa.json>`.
5. If `visual-cutoff` fails on a genuinely bad break: the fix is a human/agent
   inserting a U+2060 WORD JOINER at the break point in the source HTML —
   `render-pdf.py` never inserts one itself. After the fix, start a **new**
   `new-pdf-export` attempt (do not reuse or mutate the failed `pdf-###`) and
   re-run the sequence above.
6. Once both QA kinds PASS, `kit.py pdf-release <project> <page> <run> <pdf-id>`
   copies `index.pdf` to `pages/<page>/current/index.pdf` and, if the page
   already has a `currentReleaseId`, alongside that release's `pdf/index.pdf`
   too. It requires the QA gate to already PASS; it does not re-check anything
   else.

## Non-negotiable boundaries

- `render-pdf.py` never modifies `base.css`, `page.css`, or `images/` — a
  ground-truthed real M3 PDF export uses these byte-identical to the HTML
  deliverable. If a QA finding suggests a PDF-only style change, that is a
  reason to reject the finding or escalate, not to edit CSS outside the
  normal HTML build/repair flow.
- Never comment-wrap or delete content outside what `render-pdf.py` itself
  identifies as unambiguous (`<nav>`, `target="_blank"` anchors). A flagged
  `<button>` or ambiguous external link is resolved by a human/agent decision
  recorded in the `content` QA finding, not by re-running the script with
  different heuristics.
- Do not release a PDF whose `content` or `visual-cutoff` QA is missing,
  stale, or failing, even if the page's HTML release already passed.
