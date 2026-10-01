# Changelog

All notable changes to the `cdss-bridge-note-publisher` skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2026-09-25

### Changed
- Grounding gate accepts the V2.2 spec's free-text provenance (Book Ch. N (Chunk ID), [Anchor: Book Ch. N, Fig. X / Chunk ID]); figure/box refs checked against the cited book; table header rows skipped; chapter mismatch strict for chapter-numbered books, weak for Part/Section books; figure/asset folders skipped when indexing

## [1.2.0] - 2026-09-25

### Changed
- Claude audit fixes: fail-closed grounding gate resolves every claim-line citation against the package; cleanroom writes to cleanroom/ and never rewrites the source note; missing images fail publishing; enhance_figures rewritten (was failing on every image) and kept identical with packager; guard path derived from skills root

## [1.1.2] - 2026-09-25

### Changed
- Enforce regex word boundary on note_id matching, require all-words matching for topic queries, and fail closed when candidates cannot be resolved

## [1.1.1] - 2026-09-25

### Changed
- Fail closed when multiple markdown candidates exist in output directory and none match topic or note_id.

## [1.1.0] - 2026-09-25

### Changed
- ### Added
- Added --note-id CLI argument to synthesize_bridge_note.py to support targeted note orchestration.
- Implemented intelligent candidate note resolution by note_id and topic keywords, preventing arbitrary file selection.
- Enforced fail-closed behavior for verify_grounding: halts publication and returns non-zero code on grounding check failure.

## [1.0.1] - 2026-09-20

### Fixed
- Resolve 5 CDSS bridge note discrepancies: Dual-Truth Architecture, format parity (responsive markdown & native Word card grid tables), biophysical provenance guard, vocabulary provenance, and universal chunk anchoring.

## [1.0.0] - 2026-03-20
### Added
- Initial production release of CDSS Bridge Note Publisher.
- Davidson Bridge Note Generation Protocol V2.2 enforcement engine (`synthesize_bridge_note.py`).
- Claim-level attribution and zero-hallucination auditor (`verify_grounding.py`).
- Multi-modal Word (.docx) publisher with Native Word Card Grid Tables and Alert Cards (`publish_executive_docx.py`).
- Lanczos-4 sub-pixel image upscaling engine (`enhance_figures.py`).
- Full test suite and SemVer consistency verification (`test_consistency.py`).
