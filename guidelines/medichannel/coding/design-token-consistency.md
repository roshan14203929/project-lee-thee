# MediChannel — Design-token consistency across sibling articles

MediChannel articles are frequently delivered as a sibling series (same
pattern, different design variations — e.g. `article01`/`02`/`03`).

- **Value variation between siblings is expected** — different pages, different Figma designs.
- **Semantic role mapping must stay consistent across the series.** If `--color-primary` names one brand-color role in one article, it must name the same role in every sibling article — don't swap which name refers to which role (found in production: one sibling called a color `--color-secondary`, another called the same role `--color-primary`).
- Cross-check token *names* (not values) across sibling articles before delivery.
