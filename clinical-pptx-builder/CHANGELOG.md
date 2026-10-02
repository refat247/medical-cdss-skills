# Changelog

All notable changes to this skill are recorded here. Dates use ISO 8601 format.

## [Unreleased]

- Future improvements should be backed by a reproducible failure or a clearly documented workflow need.

## [0.2.1] - 2026-09-08

- Added a user-constraint freeze rule so explicit font floors, required closing slides, references, humanization, visuals, and comparison evidence are tracked before delivery.
- Added projector-teaching defaults of title >=32 pt and main audience text >=24 pt when the user gives no stricter rule.
- Made user-stated typography thresholds blocking in QA, with a separate exception threshold for citations, footers, slide numbers, and small ancillary labels.
- Added guidance to split or redesign slides instead of shrinking text below the requested audience-visibility floor.
- Added a coverage ledger requirement so image, diagram, head-to-head evidence, reference-footnote, and user-flagged screenshot requests cannot be silently skipped.
- Added a rule that rejected recurring decorative elements, such as title accent lines, become blocking user-constraint failures if left in the deck.

## [0.2.0] - 2026-09-06

- Added `deck.spec.yaml` as a compact source-of-truth example.
- Added six regression fixtures and a runnable regression suite.
- Added explicit QA statuses, render limitations, merge guidance, and regression policy.
- Documented exported font-unit behavior and environment-dependent font metrics.
- Standardized fixture baseline typography to `DejaVu Sans`; retained `Papyrus` for missing-font detection.
- Completed the repaired clinical Tirzepatide deck workflow with structural, clinical, render, and package checks.
- Added Git-style release documentation and package icon.

## [0.1.0] - 2026-09-06

- Created the initial reusable Clinical PPTX Builder skill.
- Added geometry-aware structural preflight and clinical surface lint.
- Added source/evidence classification and clinical presentation boundaries.
- Added merge, schema, and QA references.
