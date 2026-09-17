# Global Guidelines

Rules that apply to **every channel**. M3 and MediChannel files list only what changes from this baseline.

---

## 1. Channel Overview

Two mutually exclusive channels. Building under the wrong ruleset means a complete rebuild — confirm before starting.

| | MediChannel | M3 / MedPeer / CareNet / ThirdParty |
|---|---|---|
| Document type | XHTML 1.0 Strict, internal, 960 px fixed | HTML5, external |
| Guideline file | `docs/medi.md` | `docs/m3.md` |
| Font-size unit | `px` | `rem` |
| QA workflow | Global QA + MediChannel QA | Global QA only |

**Setting the channel:** `kit.py set-platform <project> --platform medichannel|html5`
If a run opens with "no platform is set" — stop and set it before building.

**Precedence order:** Global → Channel → Project → Page. Later rules override earlier ones only when they address the same requirement explicitly.

---

## 2. Workflow & Process

### Figma Extraction

- Prefer the authenticated Figma MCP connection. Fall back to the read-only REST API when MCP is unavailable.
- In API mode, load `FIGMA_ACCESS_TOKEN` from the process environment or `.env.local` only — never print, persist, or pass it as a command argument.
- Reuse an identical READY source. Do not create new sources for HTML, CSS, or accessibility repairs — those belong in candidates.
- Fetch each top-level frame once. Parse descendants locally. Fetch variables/styles once per file.
- Export one reference screenshot per supplied viewport variant.
- Treat supplied frames as the complete fidelity scope. A single wide frame is desktop-only — do not invent a mobile counterpart.
- Never invent a missing value. Record ambiguity in `spec/spec.json.openQuestions`.

### Run Immutability

- A source snapshot is immutable once it becomes `READY`.
- A run may change only while its status is non-terminal.
- `COMPLETED`, `NEEDS_REVIEW`, and `FAILED` are terminal — start a new run for every fresh attempt.
- Preserve every generated candidate and record acceptance or rejection.

### QA Gates

| Gate | Threshold |
|---|---|
| Max automatic repair rounds | 3 |
| Full-page pixel difference | 5% |
| Localized horizontal-band difference | 12% |
| Candidate regression tolerance | 0.10 percentage points |
| Minimum improvement after first repair | 0.20 percentage points |

Required checks: `content`, `ui`, `accessibility`, `technical`. All four must pass — a missing check is not a pass. Do not average checks into a passing score.

### Candidate Acceptance

- Validate HTML, CSS, asset references, and required content before rendering.
- Accept a repair only if it fixes the targeted failure without exceeding regression tolerance elsewhere.
- Stop when all gates pass, the repair cap is reached, no meaningful improvement occurs, required Figma data is unavailable, or a user decision is necessary.

### Content Fidelity

- Preserve every required visible string exactly — punctuation, capitalization, numerals, labels, legal copy, calls to action.
- Do not add content not present in the source or explicitly requested.
- Do not omit visually present content because it appears repetitive.
- Record source text in `content-inventory.json` and verify output against it before semantic review.

### UI Fidelity

- Match hierarchy, geometry, spacing, alignment, typography, colors, borders, radii, shadows, opacity, gradients, imagery, and stacking.
- Perform blocking visual-fidelity checks only at supplied variant widths. The 320/375/768/1024/1440 px matrix is diagnostic for unsupplied widths only.
- At diagnostic-only widths, block only concrete failures independent of layout (unreachable controls, overflow, hidden essential content).
- Verify hover, focus-visible, active, disabled, menu, modal, and form states when they exist.

### HTML & Template Delivery

- Treat delivery templates as read-only. Build in a separate file, then copy only finished code into the template's editable area. Never run a formatter over an entire delivery template.
- When available, use Prettier and `html-validate` for formatting, tag closing, doctype, charset, quoting, and void-element validation.
- When XHTML is required, convert the completed HTML as the final local step only. Do not use an external model API for the conversion.

---

## 3. HTML Rules

> Prettier + html-validate handle formatting, closing tags, doctype, charset, quoting, void elements. Channel deltas are in the channel's own file.

### Document Structure

- `<html lang="…">` must match page language.
- `<title>` left **empty** (`<title></title>`) on initial build; filled with real value before delivery.
- Footer PDF/e-PI link starts as `href="#"` with `target="_blank"` set from the start; `href` filled in before delivery.
- Exactly one `<main>` per page. (MediChannel has no `<main>` — see `medi.md`.)
- `.container` on a `<div>` inside `<section>`, never on `<section>` itself.

### Semantic HTML

- Use `<h2>`/`<h3>` for section titles. Never a styled `<div>` as a heading.
- Exactly one `<h1>`. No skipped heading levels.
- A component class that implies a heading level (e.g. `cst-h1-banner`) must actually contain that heading — a class promising `<h1>` that wraps `<h2>` or nothing is a defect.
- When Figma's H1 is a graphical/image banner, wrap the `<img>` in a real `<h1>`: `<h1><img src="…" alt="…"></h1>`.
- Tags for meaning, not appearance: `<strong>`/`<em>` for emphasis, not `<b>`/`<i>`.
- No spacer `<div>`. No empty elements or blank `class` attributes.

### Accessibility

- Every `<img>` needs `alt`. Content image → descriptive; decorative → `alt=""`.
- `alt` describes what the image shows, not its role. For PNG content images, derive from the nearest preceding `<h3>`/`<h4>`.
- `aria-label` in page language.
- Never remove focus outlines without a visible replacement.
- Use `:focus-visible` for keyboard styles — never plain `:focus`, never combined with `:hover`. All focus styles on a page share one token.

### HTML Hygiene

- No inline `style="…"`. Move to a CSS class.
- No commented-out blocks. Delete unused code; use `<!-- TODO: reason -->` for intentional omissions only.
- No `href="javascript:void(0)"`. Use `<button>` for actions, or `href="#"` + `preventDefault()`.

---

## 4. CSS Rules

> Channel deltas (font-size unit, selector specificity, anchor targeting) are in the channel's own file.

### Naming

- BEM: `.block`, `.block__element`, `.block--modifier`. Hyphens, not underscores.
- No position/context in class names (`.references--footer` ✓, `.references__item_section_1` ✗).
- Prefix **all** custom classes with `cst-` (e.g. `.cst-hero`, `.cst-page`).
- Express per-section differences as BEM modifiers on a shared component (`.btn--hero`), not descendant selectors (`.hero .btn`).

### Variables & Tokens

- All colors via `:root` custom properties. No hardcoded hex outside `:root`.
- Semantic token names (`--color-primary`, `--font-xs`…`--font-xxl`) must map to the same design role consistently within one project.
- Never substitute a spacing token for a font-size token or vice versa.
- Border widths must match the Figma spec exactly — 1px vs 2px is a real defect.
- Font-size **unit** is a channel delta — see the channel file. Font sizes are always tokens; don't hardcode.
- `padding` = inner space; `margin` = outer space between siblings.
- `line-height` unitless (e.g. `1.5`).
- No `!important`. Fix the inline `style` forcing it instead.

### Architecture

- `.cst-page` shadow/border is a channel decision — see the channel file before copying anything from Figma.
- Global element rules → `base.css`. Component-specific rules → `page.css`.
- Define shared component classes (buttons, cards, tags, typography utilities) in `page.css` first. Open `page.css` with a comment block listing the component vocabulary; remove at final delivery.
- No duplicate selectors. No repeated full rulesets in media queries — only changed properties.
- Sections with `id` (TOC anchors) need `scroll-margin-top` matching header height:
  ```css
  section[id] { scroll-margin-top: 70px; }
  ```
  (MediChannel uses `div[id]` — see `medi.md`.)

### Hygiene

- No commented-out CSS. Delete unused rules.
- **Strip every comment from `base.css`/`page.css` before final delivery.** For M3, `index.html` gets the same strip. For MediChannel, `index.html` is excluded.
- **No patch-note blocks.** Merge fixes into the original rule — never append a duplicate/overriding rule at the end of the file.
  ```css
  /* ❌ patch-note anti-pattern */
  .cst-page { padding: 20px; }
  /* fix */
  .cst-page { padding: 16px; }

  /* ✅ correct */
  .cst-page { padding: 16px; }
  ```
- After removing an element, scan for orphaned selectors and delete them.
- Do not declare the same selector in multiple disconnected blocks — consolidate.

### base.css Reference Template

Mandatory: the variable names and reset shape shown below. Values come from the Figma design. Font-size unit follows the channel rule.

```css
:root {
  /* Colors */
  --color-primary: …;
  --color-secondary: …;
  --color-text: …;
  --color-bg: …;

  /* Font sizes — unit per channel (rem for M3, px for MediChannel) */
  --font-caption: …;
  --font-xs: …;
  --font-sm: …;
  --font-base: …;
  --font-md: …;
  --font-lg: …;

  /* Font weights */
  --fw-medium: 500;
  --fw-bold: 700;

  /* Line heights */
  --lh-tight: 1.3;
  --lh-base: 1.5;
  --lh-body: 1.7;

  /* Spacing */
  --space-xs: …;
  --space-sm: …;
  --space-md: …;
  --space-lg: …;

  --max-width: 960px;
}

/* Reset scoped to .cst-page — never a bare unscoped * { margin: 0 } */
.cst-page *, .cst-page *::before, .cst-page *::after {
  margin: 0; padding: 0; box-sizing: border-box;
}
```

---

## 5. Assets & Media

### Images

- All `<img>` need explicit `width` + `height` attributes (prevents layout shift).
- No `<picture>`/`<source>`. Wrap images in `<div class="img-wrapper">`. CSS: `.img-wrapper img { max-width: 100%; height: auto; }`.
- Below-fold → `loading="lazy"`. LCP/hero → `loading="eager" fetchpriority="high"`.
- Export content images at **2x resolution only**. Set `width`/`height` to the intended display size (half the file's pixel dimensions).
- No inline `<svg>` markup in HTML. Icons and logos use `<img src="icon.svg">` — the file can be SVG, but it must be referenced, never embedded.

```html
<div class="img-wrapper">
  <img src="img/image@2x.jpg" alt="description" loading="lazy" width="960" height="540">
</div>

<img src="img/icon-pdf.svg" alt="" width="16" height="16">
```

### Fonts

Always place `<link rel="preconnect">` before Google Fonts:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
```

### Character Encoding Preflight

Scan Figma copy before writing HTML:

| Character | Problem | Fix (M3 / HTML5) |
|---|---|---|
| Roman numeral codepoints U+2160–U+216F (Ⅰ Ⅱ Ⅲ …) | Platform-risky | Replace with plain ASCII Latin (Ⅰ→I, Ⅱ→II) |
| Full-width minus `－` (U+FF0D) / wave-dash `～` (U+FF5E) | Renders inconsistently | Encode as numeric reference (`&#65293;`) |

**MediChannel overrides the Roman numeral rule** — do not strip to ASCII. Convert to the proper numeric entity instead (e.g. `&#8546;` for Ⅲ). Full conversion table in `medi.md › Assets & Media › Character References`.

Flag any platform-dependent characters found in the Figma source back to the design team.

### Asset Hygiene

- `src` values must match exact filename case on disk — mismatches work on Windows but 404 on Linux hosting. Use lowercase filenames.
- Cross-check every file in `images/` against `src` usage; remove unreferenced files before delivery.

### Sup / Sub

```css
.cst-page sub, .cst-page sup { font-size: 75%; line-height: 0; position: relative; vertical-align: baseline; }
.cst-page sup { top: -0.5em; }
.cst-page sub { bottom: -0.25em; }
```

---

## 6. QA

### Content QA

- Compare rendered output against `content-inventory.json` and the Figma reference.
- Check: page title, headings, paragraphs, navigation, buttons, links, captions, numerals, legal copy.
- Unreplaced placeholder copy is a **blocker**: `/test.html` breadcrumbs, `JP-○○○○` approval codes, `Lorem`, `TODO`, `ここに入る`.
- All text matches approved copy exactly — no typos, missing or duplicate text.
- Superscripts, subscripts, and special characters (®, ™, †) render correctly.
- On Japanese pages, verify full-width vs half-width numerals and punctuation match the design.
- Document code and version references (JP number) are correct.
- Page title format: `[Page Name] | [Site Suffix]`.

### UI QA

- Inspect reference, candidate, and difference images at every source viewport.
- Treat only supplied variants as visual-fidelity targets. Unsupplied widths are diagnostic.
- All hex values match brand guidelines.
- Font size, weight, and line-height match Figma specs per section and element type. Minimum font size: 8px.
- Layout and item order match the Figma reference exactly. No overlapping, clipping, or horizontal scroll at any breakpoint.
- Images and icons are sharp, correct size, not stretched or distorted.
- Hover, focus, and active states display correctly. Interactive state verification requires manual browser confirmation.

### Accessibility QA

- Check: landmarks, heading hierarchy, control names, labels, alt text, keyboard reachability, focus order, focus visibility.
- `:focus-visible` must be present and visibly distinct on every interactive element — never `outline: none` with nothing restored, never plain `:focus`, never combined with `:hover`.
- A heading-level component class (e.g. `cst-h1-banner`) must contain that heading level — flag a class implying `<h1>` that wraps a lower level.
- Hidden responsive content must remain available when it is essential.

### Technical QA

- Validate document structure, local asset references, console output, viewport overflow, CSS loading.
- Reject unresolved placeholders, missing files, remote runtime dependencies, and paths that escape the generated directory.
- Scan for orphaned CSS selectors (match nothing in HTML) after any element removal.
- Confirm every file in `images/` is referenced by `src`. Flag unreferenced files.
- Confirm `src` filename case matches the file on disk exactly.
- Delivered `base.css`/`page.css` (both channels) and M3's `index.html` must contain **zero comments**. For MediChannel, only check the editable-area content.
- Page renders without console errors at 1280px (desktop) and 375px (mobile). No horizontal scroll at any viewport width.

---

## 7. Delivery & Release

- Only the primary orchestrator may create `releases/v-###`.
- Release the exact accepted generated directory — do not rewrite it while copying.
- Include the run record, guideline snapshot, final QA summary, and checksums.
- All files stored with correct naming convention per project delivery requirements.

## Why HTML-008 is stated explicitly (provenance)

The H1-as-image-banner rule exists because production deliveries are genuinely
inconsistent: some wrap the banner `<img>` in a real `<h1>`, others ship a
heading-shaped `<div>` with no `<h1>` on the page at all. Both patterns appear in
the same MediChannel sibling series. The shipped rule is
`guidelines/global/coding/html.md` (HTML-008).
