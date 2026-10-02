# Canonical Promotion Decision

Promotion classification: FULLY_CERTIFIED_CANONICAL / CANONICAL_WITH_EXPLICIT_INDEPENDENT_QA_WAIVER / INDEPENDENT-QA-UNCERTIFIED / RENDER-UNCERTIFIED / REPAIR_REQUIRED / REJECTED

Candidate PPTX:
Candidate PPTX SHA-256:
Final repaired PPTX:
Final repaired PPTX SHA-256:
Initial rendered-set SHA-256:
Final rendered-set SHA-256:
100% final visual review complete: YES / NO
Independent QA policy: required / required_unless_explicit_user_waiver / optional
Independent QA execution status: INDEPENDENT_QA_CERTIFIED / INDEPENDENT_QA_WAIVED / INDEPENDENT-QA-UNCERTIFIED / NON_CERTIFYING_REPORT / INDEPENDENT_QA_NOT_RUN_OPTIONAL
Independent QA certification: CERTIFIED / NOT_CERTIFIED
Independent QA waiver reason:
Clinical/provenance gate: PASS / FAIL / NOT_RUN
Mechanical gate: PASS / FAIL / NOT_RUN
Render gate: PASS / RENDER-UNCERTIFIED / FAIL
Clinical content changed: YES / NO
Residual warnings:

## Promotion rules

- `FULLY_CERTIFIED_CANONICAL` requires all clinical, mechanical, render, 100% final-visual-review and independent-QA certification gates to pass.
- `CANONICAL_WITH_EXPLICIT_INDEPENDENT_QA_WAIVER` is permitted only when policy is `required_unless_explicit_user_waiver`, the user waiver is explicit and recorded, all non-independent gates pass, and certification remains `NOT_CERTIFIED`.
- `INDEPENDENT-QA-UNCERTIFIED` is used when independent QA is required/waivable but neither a certifying structured report nor an explicit waiver is present.
- `RENDER-UNCERTIFIED` is used when full-fidelity rendering/100% visual review cannot be certified.
- `REPAIR_REQUIRED` is used when accepted repair findings remain unresolved.
- `REJECTED` is used when release blockers cannot be safely repaired within the current release scope.
- Never call a waived or uncertified deck independent-QA-certified.
