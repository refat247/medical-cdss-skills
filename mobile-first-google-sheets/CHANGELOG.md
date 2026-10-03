# Changelog

## [1.2.1] - 2026-10-03
### Fixed
- Corrected the stale `MANUAL_ACTIVATION.md` title from v1.0.0 to the current release version.
- Corrected duplicate/missing top-level section numbering in `SKILL.md` (`Non-Negotiable Principles` is now section 3).
- Expanded version-drift verification to include manual activation, activation smoke test, and package manifest.
- Added regression coverage for all current version mirrors and sequential unique top-level section numbering.

All notable changes to **mobile-first-google-sheets** are documented here.

## [1.2.0] - 2026-09-28
### Added
- Mandatory native post-conversion re-read before Google Sheets closure.
- Explicit operating-timezone verification after conversion.
- Merged-range integrity check for blank/unwritable post-conversion cells.
- Freeze-state survival verification and native protection verification.
- Stale/duplicated conditional-format rule audit after conversion.
- Functional navigation testing rather than instruction-only navigation.
- Post-mutation re-read rule: successful write/API acknowledgement is not sufficient evidence of effective workbook state.
- Native lifecycle: SOURCE VALIDATED → CONVERTED → NATIVE AUDITED → NATIVE REPAIRED → RE-AUDITED → MOBILE VERIFIED.
- Stronger MOBILE VERIFIED gate requiring applicable native checks, not merely clean formulas.

## [1.1.0] - 2026-09-27
### Added
- Explicit invocation scopes: BUILD, AUDIT, and AUDIT_REPAIR_REAUDIT.
- Mandatory device-use classification: MOBILE-PRIMARY, MOBILE-SECONDARY, or DESKTOP-PRIMARY.
- Conservative default routing for existing-workbook improvement requests to audit → repair → re-audit.
- Guardrail preventing mobile-first criteria from being imposed indiscriminately on legitimate desktop-primary analytical workbooks.
- Required scope/device-class declaration in build and audit outputs.

## [1.0.0] - 2026-09-27
### Added
- Mobile-first Google Sheets operating contract.
- Primary-action-first and tab-order UX architecture.
- Narrow-viewport and minimal-horizontal-scroll rules.
- Single-source-of-truth entry architecture.
- Blank vs zero, partial-entry, future, off-day, and backfill semantics.
- Automatic completeness and non-blocking outlier warning rules.
- Mobile dashboard, navigation, visual semantics, and performance standards.
- XLSX → native Google Sheets conversion gate.
- Audit → repair → re-audit workflow and binary QA gates.
- SemVer/version-manager-compatible verification script.
- Package regression tests, manual activation fallback, and fresh-runtime smoke test.
- Separate release-state reporting for package, install, runtime, Git, and Notion.