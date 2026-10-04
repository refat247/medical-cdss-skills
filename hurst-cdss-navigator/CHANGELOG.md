# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.3] - 2026-10-01

### Changed
- Router failures and stderr are surfaced and set the exit code; undecodable bytes shown (errors=replace) instead of dropped; word budget no longer truncates --json; added hermetic stub-router contract tests; corpus-dependent tests skip when the package is absent.

## [1.0.2] - 2026-09-25

### Fixed
- Claude audit fixes: exit 1 when router missing; CDSS_PACKAGE_DIR override; warning on unpackaged build-router fallback

## [1.0.1] - 2026-09-25

### Changed
- Export ROUTER_PATH and define run_navigator in scripts package, fix Path string comparison in test_navigator_init.

## [1.0.0] - 2026-09-16

### Added
- Initial production release of `hurst-cdss-navigator`.
- Grounded clinical question answering across 5,258 L2 micro-chunks from *Fuster & Hurst's The Heart (15th Edition)*.
- Multi-parametric case vignette decomposer (`--vignette`) with demographics, vitals, shock detection, and drug reconciliation flags.
- Extractive span compression (`--compress`) achieving 96.2% prompt token savings.
- Differential diagnosis look-alike comparator matrix (`--diff`).
- Prompt-ready outline checklists (`--outline`) consuming only 120 tokens.
- Drug therapy indications, contraindications, and safety validation guardrail (`--validate-therapy`).
- Full compliance with `version-manager` SemVer 2.0.0 guidelines and automated test suite.
