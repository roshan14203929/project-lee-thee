# XHTML 1.0 Strict — Syntax Rules

> Applies on top of `global/coding/{html,css,assets-media}.md`. See `deviations.md` for exceptions to that baseline.
> XHTML is an XML application: one malformed tag fails the whole page. Side-by-side HTML5 comparison: `docs/xhtml-vs-html5.md`.

## Document Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja" lang="ja">
```

- MCX-001 `<?xml ...?>` on the first line. Full XHTML 1.0 Strict DOCTYPE — not `<!DOCTYPE html>`.
- MCX-002 `<html>` needs `xmlns`, `xml:lang`, and `lang` — values must match; `xml:lang` takes precedence.
- MCX-003 charset via `<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />` as the first element inside `<head>`. `<meta charset="UTF-8">` is invalid here.
- MCX-004 No `<main>`. Use `<div id="main" role="main">…</div>`.
- MCX-005 `.container` inside the section-equivalent `<div>`, not on it.

## Syntax Rules (violations cause XML parse errors)

- MCX-006 Lowercase everything: `<div class="wrapper">`, never `<DIV CLASS="wrapper">`.
- MCX-007 All elements closed; void elements self-close with a space before `/>`: `<br />`, `<img src="…" alt="…" />`.
- MCX-008 All attribute values quoted: `<td rowspan="3">`, never `<td rowspan=3>`.
- MCX-009 Boolean attributes need explicit values: `<input disabled="disabled" />`, never `<input disabled>`.
- MCX-010 Proper nesting: `<b><i>text</i></b>`, never crossed tags.
- MCX-011 Escape all `&`: `<a href="?a=1&amp;b=2">`.
- MCX-012 `id` values must start with a letter or underscore: `id="section-1"`, never `id="1st-section"`.
- MCX-013 `name` is deprecated on `<a>`, `<form>`, `<img>` — use `id`.
- MCX-014 No block element inside an inline element: `<a href="#"><div>…</div></a>` is invalid.
- MCX-015 Nesting prohibitions: `<a>` in `<a>`; `<label>` in `<label>`; `<form>` in `<form>`; `<button>` containing `<input>`/`<select>`/`<textarea>`/`<label>`/`<button>`/`<form>`/`<fieldset>`; `<pre>` containing `<img>`/`<big>`/`<small>`/`<sub>`/`<sup>`.
- MCX-016 Only the five predefined XML entities are safe: `&lt;` `&gt;` `&amp;` `&quot;` `&apos;`. Everything else needs a numeric reference — see `deviations.md` for the conversion table.
- MCX-017 Write `<tbody>` explicitly. XML parsing does not infer it, so `table > tbody > tr` selectors break without it.

## `<script>` / `<style>`

- MCX-018 `type` attribute required: `<script type="text/javascript" src="app.js"></script>`, `<link rel="stylesheet" type="text/css" href="style.css" />`.
- MCX-019 Inline blocks need CDATA wrapping:
  ```xml
  <script type="text/javascript">
  //<![CDATA[
    if (a < b && c > d) { /* ... */ }
  //]]>
  </script>
  ```
- MCX-020 No `async`/`defer` (not in the DTD) — control load order by placing `<script>` at the end of `<body>`.

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

**Removed from XHTML Strict:** `<font>` `<center>` `<strike>` `<big>` `<basefont>` `<frame>` `<frameset>` `<noframes>`.

HTML5 input types (`email`, `url`, `number`, `date`, `range`, …) and form attributes (`placeholder`, `required`, `autofocus`, `pattern`, …) fail DTD validation — browsers accept them, validators reject them.
