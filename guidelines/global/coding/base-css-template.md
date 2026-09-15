# base.css reference template

> Canonical token-naming and reset structure for `base.css`, shared by every channel. **What's mandatory:** the variable names shown and the shape of the reset. **What's not:** the literal values — those come from the Figma design — and the font-size *unit* in this example (`rem`) does **not** override the channel rule (`m3/coding/html5-delta.md` = `rem`, `medichannel/coding/deviations.md` = `px`). Brand-specific tokens (e.g. an extra accent color not shown here) are added only when the design actually needs them — this template is a starting shape, not an exhaustive list every project must fully populate.

```css
/* =============================================================================
   BASE.CSS — design tokens · reset · layout
   Shared across all pages. No component-specific styles live here.
   ============================================================================= */

/* ─── DESIGN TOKENS ──────────────────────────────────────────────────────── */

:root {
  --color-secondary: #FCF4DD;
  --color-yellow: #F0B323;
  --color-article-header: #4d4d4d;
  --color-h1-bg: #949494;
  --color-h3-border: #7f7f7f;
  --color-text: #000000;
  --color-white: #ffffff;
  --color-teal: #2CD5C4;
  --color-bg: #ffffff;
  --color-hero-bg: #666666;
  --color-caption: #333333;
  --color-gold: #D79D14;
  --color-solid-grey: #4D4D4D;
  --color-dark-grey: #373A36;
  --color-light-yellow: #FBC953;
  --color-dark-blue: #006AFF;

  --font-caption-sm: 0.625rem;  /* 10px */
  --font-caption: 0.75rem;      /* 12px */
  --font-2xs: 0.9375rem;        /* 15px */
  --font-xs: 1rem;              /* 16px */
  --font-lead: 1.125rem;        /* 18px — lead copy, sub-headings, labels, chart titles */
  --font-sm: 1.25rem;           /* 20px */
  --font-base: 1.5rem;          /* 24px */
  --font-md: 1.75rem;           /* 28px */
  --font-xl: 1.9375rem;         /* 31px — H1 banner title */
  --font-md-lg: 2.25rem;        /* 36px */
  --font-lg: 2.5rem;            /* 40px */

  --fw-medium: 500;             /* sub-headings, captions */
  --fw-bold: 700;               /* H1/H2/H3, intro copy */

  --lh-tight: 1.3;              /* large headings */
  --lh-base: 1.5;               /* body text and most components */
  --lh-body: 1.7;               /* long-form intro/copy paragraphs */

  --space-min: 2px;
  --space-xxs: 4px;
  --space-xxxs: 6px;
  --space-xs: 8px;
  --space-s: 12px;
  --space-sm: 16px;
  --space-sm-plus: 18px;
  --space-md: 24px;
  --space-md-plus: 30px;
  --space-base: 32px;
  --space-lg: 40px;
  --space-xl: 60px;

  --max-width: 960px;
}

/* ─── RESET ──────────────────────────────────────────────────────────────── */

.cst-page *,
.cst-page *::before,
.cst-page *::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.cst-page sup {
  font-size: 0.65em;
  line-height: 0;
  position: relative;
  top: -0.4em;
  vertical-align: baseline;
}

.cst-page ul,
.cst-page ol {
  list-style: none;
}

.cst-page img,
.cst-page picture,
.cst-page video {
  max-width: 100%;
  display: block;
}

.cst-page a {
  color: inherit;
  text-decoration: none;
}

/* ─── BASE ───────────────────────────────────────────────────────────────── */

html {
  scroll-behavior: smooth;
}

body {
  font-family: 'Lucida Grande', Meiryo, sans-serif;
  color: var(--color-text);
  background: var(--color-bg);
}

.cst-page em,
.cst-page i,
.cst-page cite {
  font-style: italic;
  font-synthesis: none;
}

/* ─── CONTAINER ──────────────────────────────────────────────────────────── */

.cst-page {
  max-width: var(--max-width);
  margin-inline: auto;
  font-size: var(--font-base);
  line-height: 1.7;
}
```

## Notes

- `--max-width` is set from `.cst-page`'s own `max-width` — don't hardcode `960px`/`1060px` directly in the container rule; use the token so channel/project variants stay consistent.
- The reset scopes everything to `.cst-page` (`.cst-page *`, `.cst-page ul`, `.cst-page img`, …) — never a bare unscoped `* { margin: 0; }`.
- `.cst-page` itself carries no shadow or border in this template — see `global/coding/css.md`'s Architecture section and the active channel's `coding/` file for whether either applies.
- `sup`/`sub` styling here is the canonical version of the rule in `global/coding/assets-media.md`'s Sup/Sub section — keep them consistent if either changes.
