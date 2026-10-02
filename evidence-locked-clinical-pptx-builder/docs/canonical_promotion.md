# Canonical Promotion

A build candidate becomes canonical only after a distinct release/promotion decision. Record candidate hash, semantic defect counts, all required gate statuses, render certification, independent visual status/waiver, residual warnings, repair summary, promoted filename/hash and whether any clinical content changed.

All unresolved CRITICAL/HIGH defects block promotion by default, including new or unknown defect families. Every non-independent required gate is non-waivable and accepts only PASS/CERTIFIED. The only explicit waiver path is independent visual QA, and only when `independent_visual_qa_policy=required_unless_explicit_user_waiver` with an explicit recorded user waiver.

`FULLY_CERTIFIED_CANONICAL` requires `SOURCE_INVENTORY_CERTIFICATION`, `SOURCE_EXTRACTION_COMPLETENESS`, downstream coverage, all semantic/clinical/provenance/mechanical/render/hash gates, and certified independent QA.

Never overwrite a canonical file silently. Clinical changes require upstream evidence/spec revalidation and verified approved-source support; presentation-only repairs can create a controlled canonical successor/copy with documented scope.
