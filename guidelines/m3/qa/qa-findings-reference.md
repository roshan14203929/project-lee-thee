# M3 / ThirdParty / CareNet — QA Findings Reference (AGENCY15-363 / -306)

Verified/pattern-risk findings from the M3 simple-set reference tickets. Use as a QA checklist; each row cites the rule it violates.

| # | Finding | Ticket | Rule violated | Severity |
|---|---|---|---|---|
| 1 | Heading level skip: `<h1>` followed directly by `<h3>`, no `<h2>` | -363 | `global/coding/html.md` — no skipped levels | High |
| 2 | `<title>` empty or missing at delivery | (rule) | `global/coding/html.md` — title-empty-on-build | High |
| 3 | Footer logo implemented as inline SVG instead of `<img>` | (pattern risk) | `global/coding/assets-media.md` — footer logos | Medium |
| 4 | `:focus` used instead of `:focus-visible` on interactive links | (pattern risk) | `global/coding/html.md` — focus-visible | Medium |
| 5 | Font-size declared in `px` instead of `rem` | (pattern risk) | `coding/html5-delta.md` | Medium |
| 6 | Orphaned CSS selectors left after element removal | (pattern risk) | `global/coding/css.md` / `global/qa/technical-qa.md` | Medium |
| 7 | Filename case mismatch between `src` and file on disk | (pattern risk) | `global/coding/assets-media.md` — asset hygiene | Medium |
| 8 | Patch-note CSS block appended instead of merged into original rule | (pattern risk) | `global/coding/css.md` — hygiene | Medium |
| 9 | Unused image files left in `images/` at delivery | (pattern risk) | `global/coding/assets-media.md` — asset hygiene | Low |
| 10 | Border width does not match Figma spec (1px vs 2px) | (pattern risk) | `global/coding/css.md` — border widths | Low |
| 11 | Spacing token used as a font-size value | (pattern risk) | `global/coding/css.md` — token misuse | Low |
| 12 | `box-shadow` implemented on `.cst-page` (found in real deliveries) — now a defect since the container decoration was removed | (pattern risk, going-forward correction) | `coding/html5-delta.md` — no box-shadow | Medium |

Reference: -306 is the positive example for correct `:focus-visible` implementation.
