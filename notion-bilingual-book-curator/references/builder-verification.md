# Builder Verification

An external builder's report is a claim about execution, not proof of the exported artifact.

## Required distinction

BUILDER CLAIMED FIXED ≠ VERIFIED FIXED  
SOURCE HTML VERIFIED ≠ EXPORTED PDF VERIFIED  
PATCH APPLIED IN SOURCE ≠ PATCH PRESENT IN EXPORTED ARTIFACT  
EXPORTED FILE EXISTS ≠ CURRENT REVISION EXPORTED

## Verification order

When a repaired artifact is returned:

1. Identify the actual exported file and page count.
2. Verify each requested repair directly in the exported artifact.
3. Use text extraction for exact wording/counts.
4. Use rendered-page inspection for visual/layout claims.
5. Inspect PDF outline/bookmarks separately from printed TOC links when relevant.
6. Compare against the prior artifact when available.
7. Recheck earlier blockers that were already closed.

## Stale-export failure

A common failure mode is:

source edited  
→ source not republished / exporter uses stale revision  
→ repair report says complete  
→ exported PDF remains unchanged.

Detect this by:
- checking requested text/headwords in the PDF;
- comparing page count cautiously;
- comparing extracted text;
- comparing rendered pages;
- comparing file/hash metadata where useful.

Do not accept a changed binary file as proof of changed visible content; PDF metadata or bookmark objects can change while all rendered pages remain identical.

## Honest result language

Use:
- VERIFIED IN EXPORTED ARTIFACT
- NOT PRESENT IN EXPORTED ARTIFACT
- BUILDER CLAIM ONLY — NOT YET VERIFIED
- VERIFICATION LIMITED — <missing capability>

Do not infer success from the builder's confidence.
