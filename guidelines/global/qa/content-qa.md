# Content QA defaults

- Compare the rendered output, DOM text, accessible names, and metadata against
  `content-inventory.json` and the Figma reference.
- Detect missing, duplicated, truncated, reordered, fabricated, or altered
  content.
- Verify page title, headings, paragraphs, navigation, buttons, links, form
  labels, errors, captions, prices, numerals, and legal copy.
- Verify image alternative text describes purpose rather than appearance when
  informative.
- Cite the content item identifier and relevant output selector for every
  failure.
- Unreplaced placeholder copy is a blocker, not an info note: breadcrumb links
  to `/test.html`, approval-code placeholders like `JP-○○○○`, and obviously
  temporary text (`Lorem`, `TODO`, `PLACEHOLDER`, `ここに入る`).

## Copy Accuracy

- All text matches wireframe or approved copy exactly — no typos, missing, or
  duplicate text.
- CTAs, disclaimers, footnotes, superscripts, and symbols are all present and
  correctly placed.
- Superscript, subscript, and special characters (®, ™, †) render correctly
  in the browser.
- On Japanese pages, verify full-width vs half-width numerals and punctuation
  match the design.

## Document References

- Document code and version references (JP number) are correct and up to date.
- Page title follows the format: `[Page Name] | [Site Suffix]`.
