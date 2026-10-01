# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-09-25

### Changed
- Add organize-book batch command, external source PDF discovery, and CDSS package ignore filters

## [1.1.0] - 2026-09-24

### Added
- Direct single-folder OCR extraction ingestion (`organizer.py ingest --source <single_ocr_folder> --target <section_dir>`).
- Direct single-section detection in `ingest` when target directory itself contains the matching source PDF.
- Aliases `--source` / `-s` for `--source-dir` and `--target` / `-t` for `--target-dir` across all subcommands.
- Single-section audit reporting in `status`.
- Filtered out `ocr markdown` from being mistakenly detected as a book section candidate in `is_ignorable_dir`.

## [1.0.0] - 2026-09-19

### Added
- Initial release of `medical-book-split-ocr-organizer` skill.
- Core CLI engine `scripts/organizer.py` supporting `init`, `ingest`, `auto`, and `status`.
- Automated book split directory initialization with isolated `ocr markdown/` workspaces.
- Smart normalized name-matching for OCR folder ingestion from Downloads or custom paths.
- Overwrite safety protocols and cleanup of empty browser staging folders.
- Section completeness audit reporting.
- References and layout specifications for downstream RAG and CDSS pipelines.
