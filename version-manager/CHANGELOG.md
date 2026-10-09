# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2026-10-04

### Fixed
- Reconcile Claude PR #1 version-manager deltas: SKILL_VERSION detection, newline preservation, and suite mutation guard

## [1.2.0] - 2026-09-23

### Added
- Native OpenAI/ChatGPT skill-package support, including `SKILL.md` nested `metadata.version` and `agents/openai.yaml`.
- Full SemVer 2.0.0 prerelease/build handling for supported declaration patterns.
- `--dry-run` planning mode and explicit failure when zero declarations are found.
- Regression tests for Workspace Curator, Content Auditor, and Research Method Curator package layouts.
- ChatGPT package metadata (`agents/openai.yaml`) and icon asset.

### Changed
- Removed Antigravity/Gemini- and Windows-specific execution assumptions and `file:///C:/...` references.
- Replaced the overstated atomic-write claim with staged, rollback-protected multi-file synchronization and an explicit transaction limitation.
- Suite verification now treats packages with no version declarations as failures rather than healthy packages.

### Fixed
- Research Method Curator-style nested `metadata.version` is no longer missed or falsely reported as a successful zero-declaration audit.
- OpenAI agent metadata version drift can now be detected and repaired.

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
