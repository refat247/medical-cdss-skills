# QA Gates

## Blocking

- PPTX ZIP integrity, slide relationships, and slide count must pass.
- No text box may extend beyond the slide or contain hard overflow.
- User-stated typography thresholds block delivery when measurable. If the user specifies a minimum title or body size, run preflight with that threshold and treat violations as errors unless the item is explicitly classified as an ancillary exception.
- Rendered slides must be visually inspected, including the title, densest slide, tables, diagrams, warnings, and references.
- User-flagged screenshots or slide numbers must be visually reinspected after repair.
- Clinical lint `ERROR` blocks delivery. Clinical lint warnings require disposition.
- Requested take-home, Q&A, thank-you, reference-footnote, humanization, image, diagram, or comparison-evidence items must be reconciled in a coverage ledger before final reporting.

## Non-blocking until reviewed

- Missing title placeholders, small citations, edge margins, density, and backing-shape overlap are warnings because valid decks may use intentional geometry.
- A renderer cannot certify `normAutofit` behavior or substitute font metrics. Treat unmeasured or font-uncertain behavior as `UNDETERMINED`.
- Decorative style preferences are non-blocking only when the user has not objected. Once the user rejects a recurring design element, leaving it in the deck is a blocking user-constraint failure.

## Final status

- `PASS`: no blocking findings and all required evidence is available.
- `PASS-WITH-WARNINGS`: no blockers; warnings are documented and accepted.
- `FAIL`: a blocking finding remains.
- `UNCERTIFIED`: a required check could not run or a renderer/font environment is materially unknown.
