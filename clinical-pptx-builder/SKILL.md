---
name: clinical-pptx-builder
description: "Create, edit, merge, and audit clinical or academic PowerPoint decks with source-traceable content, geometry-first layouts, and explicit structural, clinical, and render QA. Use for CME, teaching, grand-rounds, journal-club, and other evidence-based medical presentations; do not use as a marketing-deck generator."
---

# Clinical PPTX Builder

Use this skill for clinical and academic `.pptx` work. Read the built-in Presentations skill first and use its artifact-tool workflow for authoring. Keep the deck usable from a projector and safe for clinician review.

## Operating contract

1. Retrieve the canonical source files, prior QA, audience, jurisdiction, duration, and output filename before editing.
2. Classify the request as `INSPECT`, `PATCH`, `BUILD`, or `MERGE`. For `MERGE`, extract content into a slide specification and rebuild; do not raw-concatenate PPTX package parts.
3. Freeze every user-stated delivery constraint before editing. Font floors, required slide types, requested citations, visual additions, image policy, and style exclusions become explicit QA targets, not preferences.
4. Separate `VERIFIED` source evidence, `OBSERVED` artifact findings, `INFERRED` interpretation, and `UNKNOWN` items. Never silently convert uncertainty into a clinical claim.
5. Build one main message per slide with a consistent academic layout. Use explicit point sizes, short bullets, high contrast, readable labels, and citations in notes plus a small footer when appropriate.
6. Keep guideline recommendations, trial data, expert opinion, interpretation, and recommendation visibly distinct. Include contraindications, red flags, safety issues, exceptions, and jurisdiction-specific labeling only when supported.
7. Run all gates in `references/qa-gates.md`. A renderer is evidence of appearance, not proof of text fit; geometry checks and rendered inspection are both required.
8. Report `PASS`, `PASS-WITH-WARNINGS`, `FAIL`, or `UNCERTIFIED`. `UNDETERMINED` checks must never be reported as passing.

## Required loop

`spec -> build/edit -> export -> structural preflight -> clinical lint -> render every slide -> inspect contact sheet and risk slides -> repair -> rerun -> persist -> reconcile canonical documentation`

Use `scripts/pptx_preflight.py` and `scripts/clinical_lint.py`. The preflight checker is advisory for accessibility, density, margins, and intentional backing-shape overlap; any hard geometry overflow or structural error blocks delivery. The clinical linter is a surface-pattern screen, not a clinical correctness certificate.

## Authoring details

- Use the installed presentation runtime and mark authoring operations as required by the Presentations skill.
- In this runtime, exported OOXML may treat artifact-tool numeric `fontSize` as pixels; when explicit run sizing is needed, use approximately `fontSize = points / 0.75`. Verify the exported XML rather than trusting the source object.
- Give every slide an explicit title or an intentional section-divider treatment. Keep body text at or above 18 pt unless it is an unavoidable citation or label.
- When the user states a stricter typography rule, enforce that rule in the build and in preflight. For projector teaching decks, default to title >=32 pt and main audience text >=24 pt unless the user chooses otherwise; if content cannot fit, split or redesign the slide instead of shrinking the text. Footers, citations, slide numbers, axis labels, and other ancillary labels may use a separately declared exception threshold.
- Remove decorative elements that are not part of the user-requested design or source deck unless they serve a clear navigation or comprehension purpose. Repeated title underlines, divider bars, and theme accents require either an existing template precedent or explicit acceptance.
- Treat sparse slides and dense slides as layout defects to review. Sparse slides should use larger type, stronger spacing, a diagram, or a meaningful visual; dense slides should be split or summarized before reducing font size.
- Make charts self-labeling; do not rely on color alone. Prefer colorblind-safe dark green, navy, slate, and muted amber/red for warnings.
- Do not claim regulatory approval, accreditation requirements, or local CPD rules without a current authoritative source. Label local label checks as `UNKNOWN` when not verified.

## Coverage ledger

Before delivery, reconcile requested items as `DONE`, `PARTIAL`, `UNRESOLVED`, or `NOT IN SCOPE`. Include design, font floors, overflow, reference placement, required closing slides, humanized wording, image/diagram requests, comparison evidence, and slide-specific screenshots or user callouts. Do not describe the deck as finished when any requested item remains unresolved.

## Regression

Run `scripts/run_regression.py` after changing the checkers. The fixtures in `tests/fixtures` are intentionally small and include a good deck, hard overflow, low contrast, missing font, dense citations, and unsafe clinical phrasing. Expected failures prove the gates detect defects; they are not evidence that a clinical deck is safe.

Supporting policy and schemas:

- `references/qa-gates.md` for severity and delivery decisions.
- `references/merging.md` for combining decks.
- `references/spec-schema.md` for a compact source-of-truth slide spec.
- `deck.spec.yaml` as a copyable starting specification.
- `references/regression-corpus.md` for the regression contract.
