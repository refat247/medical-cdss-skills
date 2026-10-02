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
