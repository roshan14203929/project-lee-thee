# Rule ID registry

Human-facing registry for the rule IDs declared under `guidelines/`. This file is
**never** delivered to an agent: `kit.py gfiles()` globs only `guidelines/`, the
project, and the page directory, so everything here is free of context cost. Put
rationale, provenance, and worked examples here rather than in a guideline file.

## Format

`PREFIX-NNN` — zero-padded 3 digits. One prefix per normative-home file, 1:1 and
total, so an ID locates its own file without a path: an agent reading `CSS-017`
knows to open `guidelines/global/coding/css.md`. No channel segment — the prefix
already implies the channel.

| Prefix | Normative home | Channel |
|---|---|---|
| `GEN` | `guidelines/global/general-rules.md` | both |
| `FID` | `guidelines/global/fidelity.md` | both |
| `ORC` | `guidelines/global/orchestrator.md` | both (no role receives it) |
| `HTML` | `guidelines/global/coding/html.md` | both |
| `CSS` | `guidelines/global/coding/css.md` | both |
| `AM` | `guidelines/global/coding/assets-media.md` | both |
| `BASE` | `guidelines/global/coding/base-css-template.md` | both (builder only) |
| `BLD` | `guidelines/builder.md` | both |
| `EXT` | `guidelines/extractor.md` | both |
| `MC` | `guidelines/medichannel/general-rules.md` | medichannel |
| `MCD` | `guidelines/medichannel/coding/deviations.md` | medichannel |
| `MCX` | `guidelines/medichannel/coding/xhtml-syntax.md` | medichannel |
| `M3` | `guidelines/m3/general-rules.md` | html5 |
| `M3D` | `guidelines/m3/coding/html5-delta.md` | html5 |

## Declaring

ID leads the bullet, bare, no backticks:

```
- CSS-017 Never substitute a spacing token for a font-size token, or vice versa.
```

Enumerable rules stay in tables with `ID` as the first column.

## Citing

A citation carries the check *procedure*, never the assertion. QA files cite and
declare nothing — that is the mechanical expression of "coding owns the rule, QA
cites it".

```
- Grep delivered CSS for a spacing token in font-size position -> CSS-017.
```

A channel override declares its own ID and names what it displaces, which makes
the precedence chain machine-readable:

```
- MCD-001 overrides CSS-019. Font-size unit is px, never rem/em.
```

## Stability

1. **Append-only per prefix.** Never renumber. Never reuse a retired number.
2. One ID = one atomic, independently-testable assertion.
3. Rewording that does not change the assertion keeps the ID. Changing the
   assertion retires the old ID and allocates a new one.
4. Splitting a rule retires the old ID and allocates two new ones — it never
   keeps the old number for one half.
5. Retired IDs are listed below, never in a shipped guideline file, so a stale
   citation fails validation as "retired" rather than resolving to a different
   rule.

## Enforcement

`scripts/validate-kit.py` blocks on four conditions:

1. An ID declared twice.
2. A citation under `guidelines/` that is neither declared nor retired.
3. An ID declared in a file whose prefix it does not own.
4. Any declaration inside `guidelines/*/qa/*.md`.

Near-duplicate *text* detection is deliberately **not** a blocking gate — it is
threshold-tuned and noisy, so it would get disabled. Run it by hand instead.

## Retired IDs

None yet.

| ID | Retired | Reason | Superseded by |
|---|---|---|---|
