# Commands

Run from the kit root.

```bash
python scripts/kit.py init-project <project> "<name>" --platform medichannel [--content-root <path>] [--dam-root <path>] [--css-root <path>] [--template 1column]
python scripts/kit.py init-project <project> "<name>" --platform html5
python scripts/kit.py set-platform <project> --platform medichannel|html5 [--content-root <path>] [--dam-root <path>] [--css-root <path>] [--template 1column]
python scripts/kit.py init-page <project> <page> "<name>" [--article-path <path>]
python scripts/kit.py new-source <project> <page> --variant desktop=<url> --variant mobile=<url>
python scripts/kit.py new-source <project> <page> --from-source <source> --changed-node desktop=<node-id> --reason "<change>"
python scripts/kit.py source-budget <project> <page> <source>
python scripts/kit.py source-call <project> <page> <source> --operation <name> --status <SUCCESS|TRANSIENT_ERROR|AUTH_ERROR|RATE_LIMITED|FAILED> [--node <node-id>] [--retry-after <seconds>]
python scripts/kit.py source-patch <project> <page> <source> --file <patch.json>
python scripts/kit.py resolve-question <project> <page> <source> --question <id> --decision "<user decision>" --by user
python scripts/kit.py source-ready <project> <page> <source>
python scripts/kit.py spec-pattern-map <project> <page> <source>
python scripts/kit.py spec-compact <project> <page> <source>
python scripts/kit.py inventory <project> <page> <source> --sections
python scripts/kit.py inventory <project> <page> <source> --tree [--section <id>] [--variant <label>] [--kind <kind>] [--component <name>] [--fields id,kind,text|all]
python scripts/kit.py inventory <project> <page> <source> [--variant <label>] [--section <id>] [--kind <kind>] [--node <node-id>] [--id <item-id>] [--text <substring>] [--required] [--fields id,kind,text|all] [--limit <n>] [--offset <n>] [--component <name>]
python scripts/kit.py source-fail <project> <page> <source> --message "<reason>"
python scripts/kit.py guidelines <project> <page> [--role builder|extractor|ui|content|accessibility|technical]
python scripts/kit.py new-run <project> <page> --source <source>
python scripts/kit.py transition <project> <page> <run> BUILDING
python scripts/kit.py new-candidate <project> <page> <run> --round 0 --scope full-page
python scripts/verify-output.py --root <candidate-dir> --inventory <inventory> --output <report> [--platform html5|medichannel --content-root <path> --dam-root <path> --css-root <path> --article-path <path>]
python scripts/render-page.py --root <candidate-dir> --output <candidate.png> --width <width> --height <height> [--scale 1] --full-page false
python scripts/browser-summary.py --report <desktop.png.json> --report <mobile.png.json> --output <browser-summary.json>
python scripts/visual-diff.py --reference <reference.png> --candidate <candidate.png> --output <visual-review.json>
python scripts/crop-bands.py --report <desktop-diff.json> --output <desktop-crops.json> [--regions 3] [--pad 40] [--min-difference 5]
python scripts/crop-region.py --image <reference.png> --output <crop.png> [--top 900] [--start 0]
python scripts/visual-summary.py --report <desktop-review.json> --report <mobile-review.json> --output <visual-summary.json>
python scripts/kit.py candidate-result <project> <page> <run> <candidate> --status accepted --static <static.json> --browser <browser-summary.json> --metrics <visual-summary.json>
python scripts/kit.py transition <project> <page> <run> VERIFYING
python scripts/kit.py qa-record <project> <page> <run> <kind> --file <qa.json>
python scripts/kit.py qa-summary <project> <page> <run>
python scripts/kit.py transition <project> <page> <run> REFINING
python scripts/kit.py next-repair <project> <page> <run>
python scripts/kit.py new-candidate <project> <page> <run> --round <N> --scope <section> --from-accepted
python scripts/kit.py release-check <project> <page> <run> --file <release-verdict.json>
python scripts/kit.py release <project> <page> <run>
python scripts/kit.py needs-review <project> <page> <run> --message "<reason>"
python scripts/kit.py fail <project> <page> <run> --message "<reason>"
python scripts/create-qa-docs.py <TICKET>
python scripts/kit.py convert-source <project> <page> --from-project <p> --from-page <pg> --from-source <source> [--force-new]
python scripts/kit.py new-conversion-run <project> <page> --direction m3-to-medichannel|medichannel-to-m3 --from-project <p> --from-page <pg> --from-run <run> --from-candidate <candidate>
python scripts/kit.py new-candidate <project> <page> <run> --round 0 --from-external <project>/<page>/<run>/<candidate>
python scripts/convert-platform.py --direction m3-to-medichannel|medichannel-to-m3 --input <dir> --output <dir> --content-root <path> --dam-root <path> --css-root <path> --article-path <path> --output-report <report.json>
python scripts/kit.py new-pdf-export <project> <page> <run> --from-candidate <candidate>
python scripts/render-pdf.py --root <run>/generated --output <index.pdf> [--entry index.html] [--width 960] [--page-format A4] --strip-report <report.json>
python scripts/kit.py pdf-result <project> <page> <run> <pdf-id> --status ready|failed --file <meta.json>
python scripts/kit.py pdf-qa-record <project> <page> <run> <pdf-id> content|visual-cutoff --file <qa.json>
python scripts/kit.py pdf-qa-summary <project> <page> <run> <pdf-id>
python scripts/kit.py pdf-release <project> <page> <run> <pdf-id>
python scripts/kit.py new-materialization <project> <page> <run> [--from-candidate <candidate>]
python scripts/materialize-medichannel.py --input <flat-dir> --output <dir> --content-root <path> --dam-root <path> --css-root <path> --article-path <path> [--template 1column] --output-report <report.json>
python scripts/kit.py materialization-result <project> <page> <run> <materialization-id> --status ready|failed --file <report.json>
python scripts/kit.py release-materialize <project> <page> <run>
```

`create-qa-docs.py <TICKET>` generates four human-reviewer DOCX files under
`qa-reports/<TICKET>/`: `<TICKET>_overview-qa.docx` (Chapter 1 — project cover
sheet and sign-off), `<TICKET>_design-qa.docx` (Chapter 2 — WF vs Design diff),
`<TICKET>_content-qa.docx` (Chapter 3 — copy accuracy, Design vs HTML), and
`<TICKET>_coding-qa.docx` (Chapter 4 — typography metrics and guideline
compliance). Run this once at the start of the QA phase. Blank templates with the
`TICKET-ID` placeholder are kept at `qa-reports/` root for reference.

The browser summary has the same `{ "status": "PASS|FAIL" }` top-level shape
as a single render report and may aggregate several viewport render reports.
The `release` command requires the run to be `VERIFYING`, current-candidate
passing reports for all four QA kinds, a matching recorded release-verifier
verdict, and the exact generated payload: `images/`, `index.html`, `base.css`,
and `page.css` — for HTML5/M3 **and** for every native MediChannel run (a run
with no `convertedFrom.direction == "m3-to-medichannel"`). Only a
channel-conversion run's release is the nested `content/`/`content/dam/`/
`etc/designs/` tree described in `artifact-contract.md`. For a native
MediChannel run, follow `release` with `release-materialize` to derive that
nested tree as a separate, additional artifact — see
`medichannel-materialization.md`. `project.json.delivery` and
`page.json.articlePath` (set via `init-project`/`set-platform
--content-root/--dam-root/--css-root/--template` and `init-page
--article-path`) are only required at materialization time, not at build time.

`guidelines` resolves the global, channel, project, and page layers in
precedence order. `--role` is mandatory for agent reads and must carry a value:
a bare or repeated `--role` is rejected, because it used to fall back silently
to the unscoped both-channel snapshot.

A role-scoped read delivers, in precedence order:

1. `guidelines/global/general-rules.md` — precedence and the channel table.
2. `guidelines/global/fidelity.md` — the shared content/UI/quality bar, for the
   builder and the four QA roles (not the extractor).
3. The role's own file: `builder.md`, `extractor.md`, or
   `guidelines/global/qa/<role>-qa.md`.
4. **Only the `guidelines/global/coding/*.md` files that role can act on** — see
   `CODING_FOR_ROLE` in `scripts/kit.py`. `base-css-template.md` is builder-only:
   it is non-normative sample CSS carrying comment banners, and `technical-qa.md`
   requires delivered CSS to contain zero comments, so shipping it to a reviewer
   manufactures false findings.
5. The project's channel bundle (`guidelines/medichannel/` or `guidelines/m3/`).
6. Project, then page guidelines.

`guidelines/global/orchestrator.md` (run immutability, QA gate thresholds,
candidate acceptance, release) reaches **no role** — those rules belong to the
primary orchestrator, which learns them from this skill while `kit.py` enforces
them. It is still archived in the unscoped snapshot.

`new-run` still writes the unscoped snapshot to `effective-guidelines.md`, so
release evidence stays complete.

Platform is a second axis, orthogonal to role. MediChannel (XHTML 1.0 Strict)
delivers `guidelines/medichannel/general-rules.md` and every file under
`guidelines/medichannel/coding/` to every role, plus every file under
`guidelines/medichannel/qa/` to the four QA roles; HTML5 delivers
`guidelines/m3/general-rules.md` and `guidelines/m3/coding/html5-delta.md`. The
`guidelines/global/coding/` baseline is channel-agnostic and is delivered even
when no platform is set, so a builder is never left with no coding standards.
`new-run` fails until a platform is set, and a role-scoped read with no
platform opens with an explicit warning rather than silently omitting the
standards.

`crop-bands.py` reads a `visual-diff.py` report, fuses its adjacent `worstBands`
into coherent regions, and writes native-resolution reference/candidate/diff
crops for the worst ones. Use it for pixel judgements; a full-page reference is
downscaled too far to read.

`source-ready` normalizes `spec/spec.json` and `spec/content-inventory.json`
losslessly and reports the byte change; `spec-compact` applies the same
normalization on demand. Prefer `inventory` slices over reading
`spec/content-inventory.json` in full, and never read `raw/figma-*.json`.

`spec-pattern-map` derives `sources/<source>/spec/pattern-map.json` from
`spec.json`: `componentGroups` (Figma component → section IDs, instance count),
`sectionProfiles` (role, component list, layout summary, background per section),
and `layoutGroups` (sections that share an identical component set). Run it once
after `source-ready`; skip if the file already exists on a reused source. This
file is passed as a stable-prefix path to every agent handoff so they can orient
without issuing `--component` inventory calls.

`inventory --tree` returns content as `sections → groups → items`, mirroring the
expected DOM hierarchy. Groups come from `spec.sections[].groups`, which the
extractor writes from the section frame's direct children. Each section reports
`groupSource`: `spec` when real structure was found, `fallback` when the section
had none and all its items landed in one `<sectionId>__content` group. Text
nodes belonging to no group land in `<sectionId>__other`.

Sections are split by variant: desktop and mobile share a `sectionId`, so each
`(section, variant)` pair is its own entry. Pass `--variant` when building one
viewport. All the usual filters apply (`--section`, `--variant`, `--kind`,
`--required`, `--component`, `--fields`); `--limit` and `--offset` are rejected,
because paging a tree truncates mid-section and yields a misleading blueprint.

`--component <name>` (works with `--tree`, `--sections`, and flat mode) filters
results to the sections containing instances of the named Figma component,
matched case-insensitively as a substring of `tokens.components[].name`. An
unknown name is an error listing the recorded component names — it never
silently returns an empty or unfiltered result. Use it during Pre-Build Analysis
to find every section that shares a component pattern.

`crop-region.py` crops a fixed band from a PNG at native resolution, for the
structural check. Unlike `crop-bands.py` it takes an image rather than a diff
report, and crops a known region rather than the worst-differing one. It never
pads: a short image is truncated and the sidecar JSON reports the actual
`height`, which the caller passes to `render-page.py --height` so the pair has
identical dimensions.

`render-page.py --scale` sets the browser's device scale factor. Use it when a
reference was exported above 1x, so the candidate is rasterized natively instead
of resampling the reference. `visual-diff.py` requires exact dimension equality;
a mismatch returns `status: ERROR`, `reason: dimension-mismatch`, and exit 3,
which means *evidence is missing*, not that the page regressed.

`convert-source`, `new-conversion-run`, `new-candidate --from-external`, and
`convert-platform.py` port an already-accepted page to the other platform; see
`channel-conversion.md` before using any of them. `new-pdf-export`,
`render-pdf.py`, `pdf-result`, `pdf-qa-record`, `pdf-qa-summary`, and
`pdf-release` attach a PDF deliverable to a run; see `pdf-export.md`. Both are
optional workflows triggered only when the user asks for them.

`new-materialization`, `materialize-medichannel.py`, `materialization-result`,
and `release-materialize` derive the nested AEM/JCR tree from a *native*
MediChannel run's flat output — mandatory once at release, optional on demand
mid-run for a preview. Never confuse this with the channel-conversion commands
above: conversion produces a genuinely nested candidate for a *new page*;
materialization derives a nested *artifact* from the *same* page's own flat
build. See `medichannel-materialization.md`.
