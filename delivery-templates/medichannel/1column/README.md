# MediChannel delivery template — 1column

`shell.html` is a byte-for-byte copy of a real MediChannel "1 column" AEM
page template, captured from `_example-medichannel` (see `manifest.json`'s
`capturedFrom`). It is the "distributed `MediChannel_template`" that
`guidelines/medichannel/general-rules.md` refers to.

Treat this file as **read-only, structural authority** outside its three
marker regions (see `manifest.json.markers`):

- **Head CSS marker** — deterministic; `materialize-medichannel.py` rewrites
  only the `base.css`/`page.css` `<link>` `href`s inside this slice from the
  target project's `cssRoot`/`articlePath`. Everything else in the slice
  (the shared `navless_sidebar.css` link) stays untouched.
- **Body marker** — the target of the splice. `materialize-medichannel.py`
  replaces the content strictly between these two comments with the flat
  candidate's own `<body>...</body>` content (asset paths rewritten to the
  DAM location).
- **JS marker** — reserved, normally empty. `materialize-medichannel.py`
  fails loudly if the flat candidate's body contains a `<script>` tag,
  rather than guessing where it belongs.

`shell.html`'s `<title>` is also replaced (with the flat candidate's own
`<title>` text) even though it sits outside any marker — it is the one
non-marker, per-article substitution the transform makes.

Never hand-edit `shell.html` outside these regions. If it must change,
recapture it from a real template and update `manifest.json`'s `sha256`
(a test asserts they match, to catch accidental drift).
