# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-09-25

### Changed
- Trust now decided by the RAG pipeline's classify_trust() on the canonical rag_pipeline_output folder (protection markers and the pre-completion Stage 8 flag are not trust evidence); side copies ignored; pipeline folder never left on sys.path

## [1.3.0] - 2026-09-25

### Changed
- Claude audit fixes: RAG READY requires trust marker or Stage 8 trusted_for_downstream_use; untrusted chapters re-run instead of skipped; pipeline exit 3 handled; skills root derived from file location; os.pathsep; --no-skip-completed; refuses multiple inlined files

## [1.2.2] - 2026-09-25

### Changed
- Enforce Stage 8 trust finalization gate check alongside Stage 6 and protect against skipping 0-byte inlined files in cmd_preready and cmd_auto

## [1.2.1] - 2026-09-25

### Changed
- Recognize 'COMPLETED' status in Stage 6 checkpoint audits, verify Stage 6 completion in cmd_rag skip checks, and ignore empty inlined and hidden OCR files.

## [1.2.0] - 2026-09-25

### Changed
- ### Added
- Explicit __version__ declaration tracked in scripts/orchestrator.py.
- Stricter status audit verifying Stage 6 completion / CORPUS_OUTPUT_PROTECTED before reporting RAG READY.
- Fail-closed error propagation across auto lifecycle: halts immediately if Gate 0 Unicode guard, Stage 2 preready, or Stage 3 RAG fail.
- cmd_publish_manifest failure accounting to exit with non-zero code if any note fails.
- Expanded cmd_verify_versions to scan the entire pipeline skill suite without filter restriction.

## [1.1.0] - 2026-09-21

### Added
- Stage 6: Cognitive Bridge Note Publisher integration (`publish-note` and `publish-manifest` subcommands).
- Declarative topic manifest architecture (`references/sample_chapter_16_manifest.json`) for zero-blind-guessing topic resolution.
- Integrated `version-manager` suite engine (`--suite` flag) into `verify-versions` subcommand.
- Automated unit test suite `tests/test_orchestrator.py`.

## [1.0.0] - 2026-09-15

### Added
- Initial release of `medical-rag-orchestrator`.
- 6-Stage manufacturing lifecycle chaining Gate 0 through Stage 5.
