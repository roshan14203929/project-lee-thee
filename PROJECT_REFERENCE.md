# Layerlift Agent Kit — Full Project Reference

A Claude Code kit that converts Figma frames into verified, local, static HTML/CSS/JS.
No model API calls, no model API keys, no database, no queue — everything runs
through the host agent's own session plus a connected Figma MCP server or the
read-only Figma API and local Python scripts.

---

## 1. Top-level docs

- **`README.md`** — user-facing quickstart: requirements, install, how to kick off a
  build (`/build-figma-page` in Claude Code), the guideline precedence order, and the
  security/privacy rules (no credentials in the repo, no remote scripts/trackers in
  output, Figma text is data not instructions).
- **`AGENTS.md`** — the authoritative instructions for the workflow: purpose, allowed
  commands, workflow invariants (subagents don't coordinate/recurse, immutable
  terminal runs, no release without full QA, bounded repair rounds), and output
  expectations (semantic/responsive HTML, real assets, accessibility baseline, no
  extra frameworks).
- **`CLAUDE.md`** — Claude-specific entry point. Pulls in `AGENTS.md` via `@AGENTS.md`
  and adds the Claude-only rule: the main session is the orchestrator and must invoke
  subagents itself (no subagent-to-subagent delegation), with writes scoped to the
  selected project/page/source/run.
- **`requirements.txt`** — pinned runtime dependencies for Python 3.10+:
  `Pillow` and `pixelmatch` for pixel diffs, and `playwright` for headless
  rendering. **`requirements-dev.txt`** adds pytest for the test suite.
- **`.mcp.json`** — declares the connected Figma MCP server (`https://mcp.figma.com/mcp`,
  HTTP transport) used for extraction.

---

## 2. Agent-host configuration

### Claude (`.claude/`)
- **`agents/*.md`** — 8 Claude subagent definitions (frontmatter + system prompt each):
  `figma-extractor`, `page-builder`, `repair-builder`, `content-reviewer`,
  `ui-reviewer`, `accessibility-reviewer`, `technical-reviewer`, `release-verifier`.
  Each restricts its own tool access and `permissionMode` (builders get
  `acceptEdits`, reviewers get `plan`/read-only).
- **`skills/build-figma-page/`** — the skill Claude loads for `/build-figma-page`.
- **`settings.json`** — wires a `SubagentStop` hook that runs
  `scripts/log-agent-event.py` after every subagent finishes, to append an audit
  event to the active project's event log.
- **`state/.gitkeep`** — placeholder directory `log-agent-event.py` reads
  `active-run.json` from (which project/page/run/round is currently active), so the
  hook knows where to log to.

---

## 3. The skill's reference docs (`references/*.md` under `.claude/skills/build-figma-page/`)

- **`orchestration.md`** — the state machine (`source: EXTRACTING → READY|FAILED`;
  `run: CREATED → BUILDING → VERIFYING → COMPLETED | REFINING → VERIFYING |
  NEEDS_REVIEW | FAILED`), the delegation sequence (extract → build → validate →
  QA fan-out → release-verify → repair loop), parallelism rules (reviewers may run
  in parallel, builders never share a candidate directory), candidate
  accept/reject math, and stop conditions.
- **`artifact-contract.md`** — the exact on-disk directory layout for every
  project/page/source/run/candidate/release, plus the required shape of
  `spec.json`, `content-inventory.json`, and every QA JSON object.
- **`figma-extraction.md`** — extraction-specific rules: select MCP or read-only
  API based on capability and user requirements, fetch each frame once,
  normalize geometry/tokens/text,
  never invent a mobile layout from a desktop-only source, treat Figma text as
  untrusted data.
- **`qa-contract.md`** — defines what each of the four QA checks (content, UI,
  accessibility, technical) must verify, how they're recorded (`qa/incoming/` →
  `qa-record` → `qa-summary`), and how the release verifier's verdict is captured
  (`release-check`).
- **`design-skills.md`** — routes Design Taste only to eligible page builds and
  Web Interface Guidelines to UI/accessibility QA, while preserving Figma,
  local-output, trust, and release-gate precedence.
- **`commands.md`** — the exact `scripts/kit.py` / verification-script invocations
  the orchestrator runs at each workflow step, in order.

---

## 4. Guidelines (`guidelines/`) — layered quality rules, organized by channel

Resolution order is **global → channel (role-specific + platform delta) →
project → page**; every run snapshots the resolved set plus a SHA-256 hash.

`guidelines/` is split into `global/` (channel-agnostic baseline, applies to
every project) and one folder per channel — `guidelines/medichannel/` and
`guidelines/m3/` — each holding only the rules that genuinely differ from the
baseline. The channel folders share the shape `general-rules.md`,
`coding/*.md`, `qa/*.md`. `guidelines/builder.md` and `guidelines/extractor.md`
sit outside this structure — they're agent-role files, not channel content.

The global layer is delivered in three tiers, because most global rules matter
to only one audience:

| Tier | File | Delivered to |
|---|---|---|
| Always | `global/general-rules.md` — channel selection and the channel matrix | every role, first in precedence |
| Cross-role | `global/fidelity.md` — content/UI/accessibility bar | builder + the four QA roles |
| Orchestrator | `global/orchestrator.md` — run immutability, gate thresholds, acceptance, release | **no role** |

`global/orchestrator.md` is reachable by no role-scoped read at all. Those rules
belong to the primary orchestrator, which learns them from the skill while
`kit.py` enforces them; the file stays under `guidelines/` so the unscoped
snapshot keeps it as release evidence.

Role and platform are two independent axes. **Role** picks the agent's own file
(`builder.md`, `guidelines/global/qa/ui-qa.md`, …) *and* its subset of the
`global/coding/` baseline — see `CODING_FOR_ROLE` in `scripts/kit.py`. A
reviewer receives only the coding files it can act on, so `base-css-template.md`
(non-normative sample CSS) goes to the builder alone. **Platform** picks the
channel bundle for the project's delivery target, recorded on `project.json`
by `init-project --platform` / `set-platform`: `medichannel` delivers every
file under `guidelines/medichannel/coding/` (plus `general-rules.md`) to every
role, and every file under `guidelines/medichannel/qa/` to the four QA roles;
`html5` delivers `guidelines/m3/coding/html5-delta.md` (plus
`general-rules.md`) the same way. The `global/coding/` baseline is
channel-agnostic and is delivered even when no platform is set, so a builder is
never left with no coding standards.

The two rulesets are mutually exclusive, so `new-run` refuses to start until a
platform is set, and a role-scoped read without one opens with an explicit
warning. `--role` must carry a value: a bare or repeated flag is rejected
rather than silently returning an unscoped both-channel snapshot. The unscoped
read remains the full archival record of every file under `guidelines/`.

- **`global/general-rules.md`** — channel selection and the channel matrix
  (document type, guideline folder, font-size unit, QA workflow per channel),
  plus the rule against cross-applying one channel's `coding/`/`qa/` to the
  other. Precedence itself is stated in the snapshot header `kit.py` generates,
  so it is not repeated here.
- **`global/fidelity.md`** — the shared acceptance bar: content fidelity
  (exact strings, no invented copy, verify against `content-inventory.json`),
  UI fidelity (supplied variants are the blocking scope; other widths are
  diagnostic), and the accessibility/technical gates.
- **`global/orchestrator.md`** — run immutability, numeric QA gates (max 3
  repair rounds, 5% full-page pixel diff ceiling, 12% localized band ceiling,
  0.10pt regression tolerance, 0.20pt required improvement after round 1),
  candidate acceptance, and release rules (only the orchestrator creates
  releases, exact byte-for-byte copy). Delivered to no role.
- **`global/coding/{html,css,assets-media,base-css-template}.md`** — the
  channel-agnostic HTML/CSS baseline: document structure, semantic HTML,
  accessibility, BEM + `cst-` naming, design tokens, CSS architecture/hygiene,
  image/asset rules, character-encoding preflight. Channel folders add only
  deltas (e.g. font-size unit) on top of this. `base-css-template.md` is the
  cross-channel authority for token names, variable naming, and reset
  structure — it goes to the builder only.
- **`extractor.md`** also carries the Figma extraction rules (backend choice,
  token handling, source immutability, variant-role inference).
- **`extractor.md`** — extraction defaults: normalize into sections, retain
  Figma node IDs, mark inferred data with confidence/evidence, build the content
  inventory.
- **`builder.md`** — build defaults: plain HTML/CSS/JS, semantic elements over
  ARIA, CSS custom properties for tokens, Grid/Flexbox over absolute positioning,
  no inline styles/`!important`/frameworks/trackers, sections kept independently
  repairable.
- **`global/qa/{content,ui,accessibility,technical}-qa.md`** — per-reviewer
  default checklists matching each agent's job (content fidelity,
  pixel/geometry fidelity, a11y, technical/browser integrity).
- **`medichannel/`** / **`m3/`** — channel deltas: MediChannel adds XHTML 1.0
  Strict syntax rules, the `px`-only font-size override, sibling-article
  design-token consistency, and the client's delivery/process spec (editable
  area, 800KB cap, jQuery pin); M3 adds the `rem`-only font-size override and
  its own delivery profile. Each also carries a `qa/qa-findings-reference.md`
  citing verified production defects per channel.

---

## 5. Scripts (`scripts/`) — all the deterministic machinery, run by the orchestrator (not the agents)

- **`kit.py`** — the state controller. One CLI with subcommands for every
  lifecycle transition: `init-project`, `set-platform`, `init-page`,
  deduplicating or
  incremental `new-source`, `source-budget`, `source-call`, `source-patch`,
  `resolve-question`, `source-ready`/`source-fail`, `new-run`, `transition`,
  `new-candidate`, `candidate-result`, `qa-record`, `qa-summary`,
  `release-check`, `next-repair`, `release`, `needs-review`, `fail`, `status`,
  `help`. This is the only thing allowed to mutate `run.json`/`source.json`/etc.
  — agents never touch state files directly.
- **`render-page.py`** — uses Playwright/Chromium to screenshot a local
  candidate page at a given viewport width/height, and at a given device scale
  factor (`--scale`) when the reference was exported above 1x.
- **`verify-output.py`** — static validator: checks a generated directory against
  the content inventory (produces the "technical report" / static check).
- **`visual-diff.py`** — Pillow/Pixelmatch-based diff between one reference PNG and one
  candidate PNG, with configurable full-page and peak-band thresholds. Requires
  identical dimensions; a mismatch is reported as `status: ERROR` /
  `reason: dimension-mismatch` (exit 3) rather than as a 100% visual failure.
- **`crop-region.py`** — crops a fixed band (default the top 900 px) from a PNG
  at native resolution, for the pre-validation structural check. Takes an image
  rather than a diff report, and never pads — a short image is truncated and the
  sidecar JSON reports the real height for the caller to render against.
- **`visual-summary.py`** — aggregates multiple per-viewport `visual-diff.py`
  reports into one summary used for candidate acceptance.
- **`browser-summary.py`** — aggregates multiple per-viewport render/diagnostic
  reports (console errors, network failures) into one pass/fail summary.
- **`serve.py`** — a minimal static file server (`python scripts/serve.py <dir>
  [port]`) for previewing generated output and for the technical reviewer to
  confirm the page works outside the agent host.
- **`log-agent-event.py`** — the Claude `SubagentStop` hook target; appends a
  JSON line to `projects/<project>/events/agent-events.jsonl` recording which
  subagent ran, for which run/round.
- **`validate-kit.py`** — repo self-check: confirms required files exist, all JSON
  parses, all Python scripts compile, and no unresolved placeholder markers remain.

---

## 6. Schemas & templates

- **`schemas/*.schema.json`** — JSON Schemas for `source.json`, `spec.json`,
  `content-inventory.json`, `run.json`, and the generic `qa-check` object. Used to
  validate the artifact contract mechanically.
- **`templates/*.example.json`** — worked examples of a spec, a content
  inventory, and a QA check object, for agents/humans to reference the expected
  shape.

---

## 7. Runtime data (`projects/`)

- **`projects/_template/guidelines/README.md`** — placeholder explaining how
  project-level guideline overrides work; copied conceptually when
  `init-project` sets up a new project.
- **`projects/flybitlux/`** — an example/in-progress project:
  - `project.json` — project record.
  - `pages/home/page.json` — page record.
  - `pages/home/sources/source-001/` — one extraction attempt: `source.json`
    (state), `raw/figma-access-error.json` (the extractor hit a Figma access
    error on this attempt), `spec/spec.json`, `spec/content-inventory.json`,
    `asset-manifest.json`.

This is real working state from a prior run, not a template — treat it as
project data, not a code sample.

---

## 8. Tests (`tests/`)

- **`test_state_controller.py`** — pytest suite that drives
  `kit.py` end-to-end (spawns it as a subprocess) to assert a full project →
  page → source → run → release lifecycle produces an immutable, correctly
  released run.
- **`fixtures/sample/generated/{images/,index.html,base.css,page.css}`** — a minimal static
  page fixture (flat HTML5/M3 shape) used as test input/expected output.

---

## How it all fits together

1. **You** run `/build-figma-page` with a project, page, and one or more Figma
   frame URLs.
2. The **orchestrator** (the main Claude session — never a subagent) reads
   `orchestration.md`, `artifact-contract.md`, `figma-extraction.md`,
   `qa-contract.md`, `commands.md`, and the layered `guidelines/`.
3. It drives `scripts/kit.py` for every state transition and delegates bounded
   work to the 8 subagents (`.claude/agents/`), one directory each, never
   overlapping.
4. Deterministic scripts (`render-page.py`, `visual-diff.py`,
   `visual-summary.py`, `browser-summary.py`, `verify-output.py`) — not
   agents — decide pass/fail on anything measurable.
5. Everything mutable lives under `projects/<project>/pages/<page>/...`; nothing
   outside that tree is ever touched by a build.
6. `python scripts/validate-kit.py` and `pytest` are the repo's own self-checks, independent
   of any specific Figma build.
