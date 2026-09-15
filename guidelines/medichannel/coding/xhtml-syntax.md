# XHTML 1.0 Strict — Syntax Rules

> Applies on top of `global/coding/{html,css,assets-media}.md`. See `deviations.md` for exceptions to that baseline.

## Document Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja" lang="ja">
```

- `<?xml ...?>` on the first line. Full XHTML 1.0 Strict DOCTYPE — not `<!DOCTYPE html>`.
- `<html>` needs `xmlns`, `xml:lang`, and `lang` — values must match.
- charset via `<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />` as the first element inside `<head>`. `<meta charset="UTF-8">` is invalid here.
- No `<main>`. Use `<div id="main" role="main">…</div>`.
- `.container` inside the section-equivalent `<div>`, not on it.

## Syntax Rules (violations cause XML parse errors)

- Lowercase everything: `<div class="wrapper">`, never `<DIV CLASS="wrapper">`.
- All elements closed; void elements self-close with a space before `/>`: `<br />`, `<img src="…" alt="…" />`.
- All attribute values quoted: `<td rowspan="3">`, never `<td rowspan=3>`.
- Boolean attributes need explicit values: `<input disabled="disabled" />`, never `<input disabled>`.
- Proper nesting: `<b><i>text</i></b>`, never crossed tags.
- Escape all `&`: `<a href="?a=1&amp;b=2">`.
- `id` values must start with a letter or underscore: `id="section-1"`, never `id="1st-section"`.

## `<script>` / `<style>`

- `type` attribute required: `<script type="text/javascript" src="app.js"></script>`, `<link rel="stylesheet" type="text/css" href="style.css" />`.
- Inline blocks need CDATA wrapping:
  ```xml
  <script type="text/javascript">
  //<![CDATA[
    if (a < b && c > d) { /* ... */ }
  //]]>
  </script>
  ```
- No `async`/`defer` (not in the DTD) — control load order by placing `<script>` at the end of `<body>`.

## Available Structural Elements

| HTML5 | XHTML Alternative |
|---|---|
| `<main>` | `<div id="main" role="main">` |
| `<section>` | `<div class="section" role="region">` |
| `<article>` | `<div class="article" role="article">` |
| `<nav>` | `<div class="nav" role="navigation">` |
| `<header>` | `<div class="header" role="banner">` |
| `<footer>` | `<div class="footer" role="contentinfo">` |
| `<aside>` | `<div class="aside" role="complementary">` |
| `<figure>` | `<div class="figure">` |
| `<figcaption>` | `<p class="figcaption">` |
| `<mark>` | `<span class="mark">` |
| `<time>` | `<span class="time">` |

**Prohibited, no alternative:** `<picture>` `<source>` `<video>` `<audio>` `<canvas>` `<details>` `<summary>` `<dialog>` `<datalist>` `<output>` `<progress>` `<meter>` `<template>`.

## Checklist

| Item | ✓ |
|---|---|
| Full XHTML 1.0 Strict DOCTYPE | |
| `<html>` has `xmlns`, `xml:lang`, `lang` (values match) | |
| charset via `<meta http-equiv="Content-Type" ...>` | |
| All tag/attribute names lowercase | |
| All void elements self-closed with ` />` | |
| All attribute values quoted | |
| Boolean attributes have explicit values | |
| All `&` escaped as `&amp;` | |
| Inline `<script>`/`<style>` wrapped in CDATA | |
| No HTML5-only elements | |
| `id` values start with letter or underscore | |
| No block elements inside inline elements | |
