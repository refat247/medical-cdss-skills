# Audit Gates

## Corpus gates
- evidence lock valid;
- independent source-structure/recommendation census complete or semantically adjudicated;
- `SOURCE_INVENTORY_CERTIFICATION` PASS;
- `SOURCE_EXTRACTION_COMPLETENESS` PASS;
- downstream node coverage PASS;
- recommendation boundaries/footnotes/source hierarchy checked as applicable;
- reconciliation complete without silent harmonization;
- case fidelity/deduplication/coverage pass;
- Master Case Library frozen.

## Build gates
- slide spec frozen;
- semantic source-binding and prompt-semantic gates pass;
- repair-fidelity and normalization-fidelity gates pass;
- clinical/provenance audit pass;
- automated structural preflight pass or non-blocking warnings adjudicated;
- speaker notes complete and evidence-locked;
- slide/source/case mapping complete.

## Visual polish gate (only when VISUAL_POLISH was applied)
- `VISUAL_POLISH_CONTENT_LOCK` PASS (`scripts/visual_polish/verify.py`): identity, verbatim text, no non-token additions, notes, layout/master chrome, floors, fit, repo preflight;
- every `SPLIT_REQUIRED` slide routed upstream and every `SKIPPED` slide accepted as built;
- dense profile only with recorded owner approval;
- not waivable; the promotion gate requires PASS when `visual_polish_applied` is true.

## Final visual gate
- 100% slides rendered;
- 100% slides individually reviewed;
- repair ledger resolved;
- 100% rerender and re-review after material repair;
- `RENDER-UNCERTIFIED` if rendering/fidelity impossible.

## Promotion gate
- every unresolved CRITICAL/HIGH defect blocks by default, regardless of defect-family name;
- every non-independent required gate is PASS/CERTIFIED only and cannot be waived;
- independent visual QA may be explicitly waived only when policy permits and the waiver is recorded;
- hashes and residual warnings recorded;
- canonical immutability begins after promotion.
