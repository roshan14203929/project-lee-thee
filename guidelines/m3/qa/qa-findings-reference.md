# M3 / ThirdParty / CareNet — verified production defects

From the M3 simple-set reference tickets (AGENCY15-363 / -306). Prioritisation
signal only: the normative rule is the cited ID. -306 is the positive example
for correct `:focus-visible` implementation. Full write-ups in `docs/m3.md`.

| Finding | Ticket | Rule | Severity |
|---|---|---|---|
| Heading level skip: `<h1>` straight to `<h3>` | -363 | HTML-007 | High |
| `<title>` still empty or missing at delivery | -363 | HTML-002 | High |

Pattern risks for this channel, not yet ticketed: M3D-001 (`px` instead of
`rem`), M3D-002 (`box-shadow` on `.cst-page`, seen in real deliveries),
HTML-015 (`:focus` instead of `:focus-visible`), AM-005 (footer logo as inline
SVG), AM-009 / AM-010 (filename case, unused images), CSS-008 (spacing token as
font-size), CSS-009 (border width), CSS-025 (patch-note block), CSS-026
(orphaned selectors).
