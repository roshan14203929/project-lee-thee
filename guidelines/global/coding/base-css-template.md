# base.css reference template

> Cross-channel authority for token **naming** and reset **structure**. Mandatory: the variable names below and the shape of the reset — identical in every channel. Not mandatory: the literal values, which come from the Figma design. The font-size *unit* is a channel delta (`m3/coding/html5-delta.md` = `rem`, `medichannel/coding/deviations.md` = `px`). Add a brand token only when the design needs one; this is a starting shape, not a list to populate exhaustively.

## Token names

Values are per-design and deliberately omitted. Keep the names, the families, and the name-to-role mapping (`global/coding/css.md`).

```css
:root{
  /* colors — semantic first; add descriptive brand names (--color-accent-red,
     --color-navy) only when the design needs them. Numbered names are a last resort. */
  --color-text; --color-bg; --color-white; --color-black;
  --color-primary; --color-secondary; --color-caption;

  /* font sizes — unit per channel, never hardcoded in components */
  --font-caption-sm; --font-caption; --font-2xs; --font-xs; --font-lead;
  --font-sm; --font-base; --font-md; --font-md-lg; --font-lg; --font-xl;

  /* weights and line heights — these values ARE fixed */
  --fw-medium: 500; --fw-bold: 700;
  --lh-tight: 1.3; --lh-base: 1.5; --lh-body: 1.7;

  /* spacing */
  --space-min; --space-xxs; --space-xxxs; --space-xs; --space-s; --space-sm;
  --space-sm-plus; --space-md; --space-md-plus; --space-base; --space-lg; --space-xl;

  --max-width;
}
```

## Reset and base structure

Mandatory shape. Every reset selector is scoped to `.cst-page` — never a bare `* { margin: 0 }`.

```css
.cst-page *, .cst-page *::before, .cst-page *::after { margin: 0; padding: 0; box-sizing: border-box; }
.cst-page ul, .cst-page ol { list-style: none; }
.cst-page img, .cst-page picture, .cst-page video { max-width: 100%; display: block; }
.cst-page a { color: inherit; text-decoration: none; }
.cst-page em, .cst-page i, .cst-page cite { font-style: italic; font-synthesis: none; }

html { scroll-behavior: smooth; }
body { font-family: 'Lucida Grande', Meiryo, sans-serif; color: var(--color-text); background: var(--color-bg); }

.cst-page { max-width: var(--max-width); margin-inline: auto; font-size: var(--font-base); line-height: 1.7; }
```

## Notes

- BASE-001 Set `--max-width` from `.cst-page`'s own `max-width`; never hardcode `960px`/`1060px` in the container rule.
- BASE-002 `.cst-page` carries no shadow or border here — that is a channel decision (`global/coding/css.md` Architecture, plus the channel's `coding/` file).
- BASE-003 `sup`/`sub` styling is owned by `global/coding/assets-media.md`. Do not restate it here.
