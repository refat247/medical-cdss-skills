# Changelog

All notable changes to the `cdss-retrieval-packager` skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.1] - 2026-10-01

### Changed
- Review fixes: federated search exits 1 when no book index

## [1.5.0] - 2026-10-01

### Changed
- Generated federated search loads each book's router under a unique module name (no cross-book contamination), surfaces per-book failures and exits non-zero, validates top_k; compress_excerpt no longer cuts after i.v./approx./vs. (dose was dropped); prune gains --dry-run and --keep-trust-evidence; verify exits non-zero on empty/missing package; patch-paths reports residual hard-coded paths.

## [1.4.0] - 2026-09-25

### Changed
- Packager now writes the package runtime cdss_encoding_guard.py from the guard skill (sync_encoding_guard, run by federate/auto) - the old package copy still had the NFKC bug turning 10⁹ into 109 in every answer; federated excerpts are output-normalised then clause-safe compressed

## [1.3.1] - 2026-09-25

### Fixed
- Davidson DB fallback path in patched clients points at D:\davidson_25_true\TRUE_MD_WITH_IMAGES(v2.23.0_made) (override DAVIDSON_CORPUS_DIR); previous path did not exist

## [1.3.0] - 2026-09-25

### Changed
- Claude audit fixes: generated cdss_federated_search.py was a SyntaxError (raw-string escapes) - fixed with compile test; clause-safe whole-sentence compression shared by template; figure link verification; README generated from real counts and verification; verify/auto exit 1 on failed checks; enhance_figures keeps output format matching extension

## [1.2.2] - 2026-09-25

### Changed
- Implement sentence- and word-boundary aware compression in federated retrieval to preserve clinical safety without cutting mid-word or mid-sentence

## [1.2.1] - 2026-09-25

### Changed
- Add --compress argument and span compression support to generated cdss_federated_search.py script template.

## [1.2.0] - 2026-09-25

### Changed
- ### Fixed
- Added missing 'import subprocess' in scripts/packager.py.
- Strictly protected CORPUS_OUTPUT_PROTECTED.json and CORPUS_TRUST_STATUS files from pruning deletion.
- Anchored pruning regex to end-of-string ($) so files with mid-name substrings (e.g. notes.bak.md) are preserved.
- Enhanced figure processing in enhance_figures.py to support LA (luminance-alpha), RGBA, and paletted images with white background blending.

## [1.1.0] - 2026-09-20

### Changed
- Add Figure DPI audit gate and automated Lanczos-4 super-resolution asset generator

## [1.0.0] - 2026-03-15
### Added
- Initial production release of CDSS Retrieval Packager.
- Extraction of pure retrieval assets (*_RAG_Optimised.md, *_chunks.md, assets/figures/).
- Scorecard and zip pruning.
- Portable relative path patching for CDSS routers.
- Federated search CLI generator (`cdss_federated_search.py`).
