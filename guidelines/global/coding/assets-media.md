# Assets & Media Rules (channel-agnostic baseline)

> Channel deltas (e.g. relaxed lazy-loading mandate, stricter character-reference requirement) live in `<channel>/coding/` — read that alongside this file.

## Images

- All `<img>` need explicit `width` + `height` attributes (prevents CLS).
- No `<picture>`/`<source>`. Wrap in `<div class="img-wrapper">` (or `.cst-img-wrapper` inside a template/CMS). CSS keeps images fluid: `.img-wrapper img { max-width: 100%; height: auto; }`. Never set a fixed CSS `width`/`height` on an image.
- Below-fold → `loading="lazy"`. LCP/hero → `loading="eager" fetchpriority="high"`.
- **Every content image asset is exported at 2x resolution only** — no separate 1x file, no `srcset`. Set `width`/`height` to the intended *display* size (half the file's actual pixel dimensions), so the browser downscales the 2x file for a sharp render. This does not apply to QA reference screenshots (`extractor.md`'s reference PNGs stay 1x — a different artifact, used for pixel-diffing, not for display).
- **Icons and logos:** `<img src="icon.svg">` is fine — the icon/logo *file* can be an `.svg`. What's banned is inline `<svg>…</svg>` markup embedded directly in the HTML. Footer logos and compound/icon assets (e.g. a PDF/document-link icon) are always referenced via `<img>`, never reconstructed from multiple positioned inline SVG fragments.

```html
<!-- standard, 2x source, half-size display dimensions -->
<div class="img-wrapper">
  <img src="img/image@2x.jpg" alt="nearest h3/h4 text" loading="lazy" width="960" height="540">
</div>

<!-- icon/logo via img, svg file is fine -->
<img src="img/icon-pdf.svg" alt="" width="16" height="16">
```

## Fonts

Always place `<link rel="preconnect">` before the Google Fonts `<link>`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
```

## Reusable component reference — PDF / approval code / footer logos

This pattern recurs on most delivery pages. Document what's fixed vs. per-ticket rather than templatizing it:

- **Fixed CMS boilerplate** (do not touch): site-wide footer chrome and legal/copyright code injected by the host template.
- **Legitimately per-ticket** (must be updated each delivery): approval-code text, e-PI/PDF `href` (starts as `href="#"` on initial build, `target="_blank"` set from the start — see `html.md`), icon asset path, brand-logo `src` values.
- The PDF/approval-code link needs the same `:focus-visible` treatment as every other interactive element (see `html.md`) — this is the element most often shipped with a broken or suppressed focus ring.

## Character Encoding Preflight

Scan extracted Figma copy before writing HTML:

| Character type | Problem | Fix (M3 / HTML5) |
|---|---|---|
| Roman numeral codepoints U+2160–U+216F (Ⅰ Ⅱ Ⅲ …) | Platform-risky | Replace with plain ASCII Latin (Ⅰ→I, Ⅱ→II) |
| Full-width minus `－` (U+FF0D) / wave-dash `～` (U+FF5E) | Renders inconsistently | Encode as a numeric character reference (e.g. `&#65293;`) |

**MediChannel overrides the Roman numeral rule** — do not strip to ASCII; convert to the proper numeric entity instead (e.g. `&#8546;` for Ⅲ). See the full conversion table in `medichannel/coding/deviations.md`.

Flag any such characters found in the Figma source itself back to the design team.

## Asset Hygiene

- `src` values must match the exact filename case on disk — mismatches work on Windows but 404 on case-sensitive Linux hosting. Standardize filenames to lowercase.
- Cross-check every file in `images/` against `src` usage; remove unreferenced files before delivery.

## Sup / Sub

- `<sup>` is for footnote/citation markers, not exponents or decoration.
- `<sub>` is reserved for genuine scientific/chemical subscript (e.g. FEV₁), not decoration.
- Apply a scoped reset:
  ```css
  .cst-page sub, .cst-page sup { font-size: 75%; line-height: 0; position: relative; vertical-align: baseline; }
  .cst-page sup { top: -0.5em; }
  .cst-page sub { bottom: -0.25em; }
  ```
