# MediChannel materialization

Apply this reference to every *native* MediChannel run (`new-run`, not
`new-conversion-run`). It describes how the flat build/repair/QA candidate
becomes the nested AEM/JCR tree the client's CMS actually expects. Never
confuse this with `channel-conversion.md`: conversion ports an
already-accepted page to a *new page* on the other platform, and its
candidates are genuinely nested from creation by a real HTML5-\>XHTML
structural transform; materialization derives an *additional* nested artifact
from the *same* page's own flat build, and never runs that structural
transform (the flat candidate is already XHTML-compliant — see below).

## Why the candidate is flat

A native MediChannel candidate builds, repairs, and passes QA in exactly the
flat shape used by HTML5/M3 (`index.html`, `base.css`, `page.css`, `images/`,
relative asset paths) — see `artifact-contract.md`. It is still required to
be valid XHTML 1.0 Strict throughout (`guidelines/medichannel/coding/
xhtml-syntax.md`), so no structural or entity conversion is ever needed at
materialization time — only splicing and path rewriting.

## The stored delivery template

`delivery-templates/medichannel/<template>/` (default `1column`,
`project.json.delivery.template`) holds:

- `shell.html` — a real MediChannel AEM page template, read-only structural
  authority outside its marker regions.
- `manifest.json` — the exact marker literals and a `sha256` of `shell.html`
  (a test asserts they match, to catch accidental drift).

Three marker regions, found by inspecting a real production ticket:

- **Head CSS marker** — deterministic; only the `base.css`/`page.css`
  `<link>` `href`s get rewritten to the target `cssRoot`/`articlePath`.
  Everything else in the slice (shared, non-per-article stylesheet links)
  stays untouched.
- **Body marker** — the splice target. The flat candidate's own
  `<body>...</body>` content (asset paths rewritten to the DAM location)
  replaces the content strictly between these two comments.
- **JS marker** — reserved, normally empty. Materialization fails loudly if
  the flat candidate's body contains a `<script>` tag rather than guessing
  where it belongs — resolve by hand first.

The shell's `<title>` (outside any marker) is also replaced with the flat
candidate's own title — the one non-marker substitution.

## Sequence

**Release-time (mandatory for every native MediChannel run):**

```
kit.py release-materialize <project> <page> <run>
python scripts/materialize-medichannel.py --input <release>/site --output <release>/jcr \
  --content-root <> --dam-root <> --css-root <> --article-path <> \
  --output-report <release>/jcr-materialization-report.json
```

Run this immediately after `kit.py release` succeeds. It reads
`project.json.delivery` and `page.json.articlePath`, allocates
`releases/v-###/jcr/`, and returns the paths the script needs. `site/` and
`current/` are unaffected — they stay flat.

**On-demand mid-run preview (optional, e.g. before release, or against a
repair candidate a human wants to inspect in its delivered shape):**

```
kit.py new-materialization <project> <page> <run> [--from-candidate <candidate>]
python scripts/materialize-medichannel.py --input <resolved-input> --output <resolved-root> ...
kit.py materialization-result <project> <page> <run> <materialization-id> --status ready|failed --file <report.json>
```

Defaults to `runs/<run>/generated` when `--from-candidate` is omitted. Works
even on a terminal run (mirrors `new-pdf-export`'s rationale: this is a side
artifact attached to a run, not a run-state transition). Lives entirely under
`runs/<run>/materialized/materialized-###/jcr/` — never inside `candidates/*`
or `generated/`, so it can never be mistaken for the deployable flat payload
and never mutates it.

Both commands reject a channel-conversion run and a non-medichannel project.

## Reading a materialization report

`{status: "OK", template, templateSha256, checkedAt, filled: {title, headCss,
body}, findings: []}`. There is no `flagged` worklist — unlike
`convert-platform.py`, nothing here requires human judgment by design; a
non-`OK` status means the run exited non-zero (bad input shape, missing
template, or an unresolved `<script>` tag), not a partial result to review.
