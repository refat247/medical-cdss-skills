# Changelog

> **Distribution status notice — 2026-10-05:** this public v1.1.1 package is a preserved **lagging distribution**. Canonical authority is `refat247/Private_repo/skills/version-manager/` v1.2.1. Claude PR #1's relevant deltas were reconciled into the private lineage at commit `1da21d2f6d700deeb40ebfddfb0a54aa27a78fab`; do not infer authority from this monorepo copy.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Comprehensive reference guides for Semantic Versioning 2.0.0 (`references/semver_rules.md`) and Keep a Changelog specification (`references/changelog_spec.md`).
- Automated unit test suite `tests/test_bump_version.py`.
