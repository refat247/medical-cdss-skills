# Changelog

## 1.2.0 — 2026-10-03

### Added
- Governed end-to-end production state machine from finite source-set lock through release closure.
- Explicit blocker ledger and internal-evidence exhaustion / external-research authorization gate.
- Chapter/evidence-packet drafting eligibility gate.
- Production-route abstraction for direct builds, external builders, and specialist builders.
- Explicit separation of publication freeze from release packaging/canonical-baseline recording.
- `references/governed-production-orchestration.md`.

### Compatibility
- Backward compatible with v1.1.0 workflows.
- Release type: MINOR.
- Complete v1.1.0 governed package recovered and used as the exact release baseline.
- `agents/openai.yaml` version/default prompt mirror updated deliberately; all unrelated v1.1.0 files preserved unless listed in this release.
- Full package smoke/diff/archive verification required before promotion.


## 1.1.0 — 2026-09-25

### Added
- MODE F — Jargon Coverage Audit.
- Reader-critical jargon classification and alias grouping.
- Locked glossary-patch workflow with exact post-build entry/count verification.
- Actual-export verification rule: builder claims and source HTML are not treated as proof of the final PDF.
- Stale revision / stale export detection guidance.
- Artifact-diff gate for page/text/render/navigation changes against the immediately previous artifact.
- Regression gate requiring recheck of previously closed blockers after later repairs.
- Mature-artifact patch ratchet from broad build to increasingly surgical micro-patches.
- Explicit freeze semantics: artifact freeze does not imply revalidation of all historical source claims.
- First-class manual protocol loading workflow.
- `references/jargon-coverage-audit.md`.
- `references/builder-verification.md`.
- `references/artifact-diff-regression.md`.
- `references/package-maintenance.md`.

### Changed
- Strengthened MODE C, MODE D, and MODE E with exported-artifact and regression verification.
- Strengthened freeze gates and builder prompt compiler.
- Updated output templates for jargon and artifact-diff reporting.
- Synchronized package version metadata across `SKILL.md`, `agents/openai.yaml`, README, changelog, manual loader, and smoke test.

### Fixed
- Replaced the v1.0.0 package's body-only version declaration as the canonical source with Version Manager-compatible `metadata.version`.
- Added stable-status metadata and a default prompt that explicitly names `$notion-bilingual-book-curator`.

### Compatibility
- Backward compatible with v1.0.0 workflows.
- Release type: MINOR.

## 1.0.0 — 2026-09-25

Initial release distilled from the Davidson RAG/CDSS book-production workflow.

Included:
- preservation-first source audit;
- evidence-state invariants;
- bilingual convention;
- current-vs-historical reconciliation;
- Humanizer-style semantic-drift controls;
- typography/color rules;
- readability audit;
- external-builder prompt compiler;
- repair-only micro-patch workflow;
- binary freeze gates;
- clinical/evidence-sensitive mode.
