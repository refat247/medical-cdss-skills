# QA gates

## Engineering gates
1. Source hash recorded.
2. Source never overwritten.
3. Slide/page count extracted.
4. Rendered image exists for every source slide/page.
5. Duplicate detection completed.
6. Script mapping is one-to-one for included slides.
7. DOCX opens and renders.
8. PPTX with notes, when requested, opens and preserves slide count/order.

## Content gates
1. Whole-deck analysis exists before scripts.
2. Slide briefs exist for all included slides.
3. Coverage ledger has no unexplained unresolved items.
4. Main scripts are non-empty and not merely slide transcription.
5. Timing reconciles to target within tolerance.
6. Clinical profile has no unresolved blockers.

## Certification
- `PASS`: all required gates pass.
- `PASS_WITH_WARNINGS`: engineering gates pass, non-blocking warnings remain.
- `FAIL`: at least one required gate fails.
- `UNCERTIFIED`: a required gate could not be checked.
