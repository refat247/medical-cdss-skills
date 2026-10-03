# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2026-10-01

### Changed
- validate_run_trace: non-UTF-8 input exits 2 cleanly; a COMPLETE trace must have funnel stages; scan command documented with --model; added tests.

## [1.0.1] - 2026-09-25

### Fixed
- Claude audit fixes: skills directory derived from script location (CDSS_SKILLS_ROOT override) instead of hardcoded path

## [1.0.0] - 2026-09-25

### Added
- Initial production release of `clean-my-ai-harness`.
- Standalone scanner `scripts/scan_visible_harness.py`.
- Read-only environment discovery across Antigravity and Codex configurations.
- Structured report generator (`YOUR-AI-SETUP.html` and evidence packet).
