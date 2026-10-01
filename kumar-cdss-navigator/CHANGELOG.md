# Changelog

All notable changes to the `kumar-cdss-navigator` skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-09-25

### Fixed
- Claude audit fixes: exit 1 when router missing; CDSS_PACKAGE_DIR override; warning on unpackaged build-router fallback

## [1.0.0] - 2026-09-20

### Added
- Initial release of the dedicated `kumar-cdss-navigator` skill.
- Production CLI interface wrapping `04_Kumar_and_Clark_11/Index/cdss_qa_router.py`.
- Support for clinical queries (`--query`), clinical case vignettes (`--vignette`), span compression (`--compress`), and JSON output (`--json`).
- Direct integration with Kumar & Clark concept subtrees (`--outline`), differential comparators (`--diff`), and drug safety guardrails (`--validate-therapy`).
- Automated unit test suite verifying sub-millisecond retrieval, chunk compression, and vignette execution.
