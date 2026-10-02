# Migration Notes: v2.1.1 → v2.2.0

Backward-compatible minor release. Existing v2.1.1 projects remain readable, but canonical promotion under v2.2.0 requires the new semantic/source-integrity gates when applicable.

New artifacts:
- source recommendation inventory and extraction-accounting matrix;
- source-boundary validation fields;
- footnote/marker binding ledger;
- source-section attribution validation;
- prompt semantic review ledger;
- text normalization ledger with explicit policy enum;
- repair-fidelity ledger;
- semantic defect register and promotion blocker.

Projects migrated from v2.1.1 should mark new gates `pending` and must not inherit a prior canonical PASS merely from existing node-coverage, render, or independent visual-QA results.
