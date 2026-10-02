# Slide brief prompt contract

For each rendered slide, create one structured brief compatible with `schemas/slide_briefs.schema.json`.

Inventory every information-bearing element. For each independent claim/number/relationship/qualifier, record a coverage disposition:
- spoken
- intentionally_omitted (with reason)
- unresolved

Do not treat decorative elements, page numbers, logos, or layout chrome as content.

For charts/tables, identify the decisive comparison/trend and material uncertainty rather than listing every row or axis.

In clinical/CME mode, assign a claim status and risk level conservatively.
