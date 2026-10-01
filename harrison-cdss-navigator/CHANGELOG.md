# Changelog

All notable changes to the `harrison-cdss-navigator` skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2026-10-01

### Changed
- Router failures and stderr are surfaced and set the exit code; undecodable bytes shown (errors=replace) instead of dropped; word budget no longer truncates --json; added hermetic stub-router contract tests; corpus-dependent tests skip when the package is absent.

## [1.0.1] - 2026-09-25

### Fixed
- Claude audit fixes: exit 1 when router missing; CDSS_PACKAGE_DIR override; warning on unpackaged build-router fallback

## [1.0.0] - 2026-09-19

### Added
- Initial release of Harrison CDSS Navigator (v1.0.0).
- Production interface to 10,419 L2 micro-chunks and 7,811 indexed clinical concepts.
- Multi-turn clinical question answering, case vignette decomposition, and span compression.
- Differential diagnosis and drug therapy validation guardrails.
