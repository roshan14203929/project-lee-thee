# XHTML 1.0 Strict vs HTML5 — Reference

> Human and conversion-time reference. **Not** delivered to agents: a native
> MediChannel candidate is authored as XHTML from the start, so a builder never
> needs a "what HTML5 permits" comparison. The normative authoring rules live in
> `guidelines/medichannel/coding/xhtml-syntax.md` (IDs `MCX-*`); this file is the
> side-by-side lookup for resolving an XHTML-vs-HTML5 habit conflict, and for the
> manual comparison step during an HTML5 -> XHTML conversion.


## DOCTYPE & Root Element

| | XHTML 1.0 Strict | HTML5 |
|---|---|---|
| DOCTYPE | `<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">` | `<!DOCTYPE html>` |
| Root element | `<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja" lang="ja">` | `<html lang="ja">` |
| XML namespace / `xml:lang` | Required | Not used |

**Note:** XHTML is an XML application — one malformed tag breaks the whole page. HTML5 recovers gracefully.

## Syntax Rules

| Rule | XHTML 1.0 Strict | HTML5 |
|---|---|---|
| Tag case | Lowercase only | Case-insensitive |
| Closing tags | All required | Many optional (`</p>`, `</li>`) |
| Void elements | Self-close required | Slash optional |
| Attribute values | Must be quoted | Unquoted allowed |
| Boolean attributes | `disabled="disabled"` | `disabled` |

## Script and Style

- `type="text/javascript"` / `type="text/css"` required in XHTML; optional in HTML5.
- `async`/`defer` cause DTD validation errors in XHTML; standard in HTML5.

## Meta Charset

- XHTML: `<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />`. `<meta charset="UTF-8">` is invalid.
- HTML5: `<meta charset="UTF-8">`, first element inside `<head>`.

## Content Model

Block inside inline is illegal in XHTML Strict (`<a href="#"><div>...</div></a>` invalid; HTML5 allows it via the transparent content model).

Removed in XHTML Strict: `<font>`, `<center>`, `<strike>`, `<big>`, `<basefont>`, `<frame>`, `<frameset>`, `<noframes>`.

Nesting prohibitions: `<a>` in `<a>`; `<button>` containing `<input>`/`<select>`/`<textarea>`/`<label>`/`<button>`/`<form>`/`<fieldset>`; `<label>` in `<label>`; `<form>` in `<form>`; `<pre>` containing `<img>`/`<big>`/`<small>`/`<sub>`/`<sup>`.

HTML5 input types (`email`, `url`, `number`, `date`, `range`, …) and form attributes (`placeholder`, `required`, `autofocus`, `pattern`, …) cause DTD validation errors in XHTML — browsers handle them, validators reject them.

## Ampersand & Entities

- `&` always `&amp;`, including in URLs.
- Only the five predefined XML entities are safe without a DTD: `&lt;` `&gt;` `&amp;` `&quot;` `&apos;`. Use numeric refs for everything else: `&nbsp;` → `&#160;`, `&copy;` → `&#169;`, `&mdash;` → `&#8212;`.
- `&apos;` is valid in XHTML; use `&#39;` for HTML4 compatibility.

## `id` vs `name`

`name` is deprecated on `<a>`, `<form>`, `<img>` in XHTML — use `id`. `id` must start with a letter or underscore.

## `lang` / `xml:lang`

XHTML requires both, matching, `xml:lang` takes precedence. HTML5 uses `lang` only.

## `<tbody>` Must Be Explicit

XML parsing does not auto-infer `<tbody>` — write it explicitly or `table > tbody > tr` selectors break.

## Quick Reference

```html
<!-- XHTML invalid — HTML5 allows -->
<INPUT type="hidden" value="foo">     <!-- uppercase tag -->
<br>                                   <!-- no self-close -->
<img src="x.gif">                     <!-- no self-close, no alt -->
<input disabled>                      <!-- minimized boolean -->
<td rowspan=3>                        <!-- unquoted attribute -->
<a href="?a=1&b=2">                   <!-- bare & -->
<p>First<p>Second                     <!-- unclosed p -->
<a href="#"><div>block</div></a>      <!-- block in inline -->

<!-- HTML5 valid — XHTML would not allow -->
<!DOCTYPE html>
<meta charset="UTF-8">
<script>...</script>
<input required>
<input type="email">
<video src="movie.mp4" controls></video>
<article><section>...</section></article>
```
