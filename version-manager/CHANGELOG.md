# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-10-01

### Changed
- Scans SKILL_VERSION constants (the missed ocr-preready drift); full SemVer incl. pre-releases; nested/quoted frontmatter version handled consistently; --dry-run; atomic newline-preserving writes (no CRLF churn); --notes used verbatim; --suite with --bump is an error.

## [1.1.1] - 2026-09-25

### Fixed
- Fixed argparse % formatting crash when displaying --help.

## [1.1.0] - 2026-09-21

### Added
- Universal multi-skill workspace suite orchestrator (--suite and --filter flags) for single-command zero-drift governance across all skills.

## [1.0.0] - 2026-09-14

### Added
- Initial production release of `version-manager` skill.
- Core Python automation engine `scripts/bump_version.py` for automated version discovery, atomic multi-file synchronization, and drift verification.
- Support for Agent Skills (`SKILL.md`), Python (`pyproject.toml`, `setup.cfg`, `setup.py`, `__init__.py`), Node/TypeScript (`package.json`), documentation (`README.md`), changelogs (`CHANGELOG.md`), and test suites (`tests/test_*version*.py`).
- Automatic `CHANGELOG.md` entry generation with standard Keep a Changelog categories (`Added`, `Changed`, `Fixed`).
- Comprehensive reference guides for Semantic Versioning 2.0.0 (`references/semver_rules.md`) and Keep a Changelog (`references/changelog_spec.md`).
- Automated unit test suite `tests/test_bump_version.py`.
