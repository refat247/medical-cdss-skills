# Changelog

All notable changes to the `davidson-ocr-preready` package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.7.5] - 2026-09-25

### Changed
- Sync handover contract reference to davidson-rag-pipeline-antigravity v2.25.1

## [1.7.4] - 2026-09-25

### Changed
- Sync handover contract reference to davidson-rag-pipeline-antigravity v2.25.0

## [1.7.3] - 2026-09-25

### Changed
- Synchronize OCR handover contract with davidson-rag-pipeline-antigravity v2.24.3

## [1.7.2] - 2026-09-25

### Changed
- Sync handover contract reference to davidson-rag-pipeline-antigravity v2.24.2.

## [1.7.1] - 2026-09-25

### Changed
- ### Fixed
- Updated references/ocr_handover_contract.md to reference downstream RAG pipeline v2.24.1.
- Switched text normalization in runner.py to Unicode NFC with explicit ligature replacement (avoiding NFKC decomposing superscripts and fractions).
- Implemented atomic file writing via temporary swap file in runner.py to eliminate risk of partial file corruption on interruption.

## [1.7.0] - 2026-09-14

### Added
- **Universal Document Archetype Support (`preready/runner.py`)**: Added `detect_document_archetype()` to differentiate between multi-chapter textbooks (`TEXTBOOK`) and clinical society practice guidelines/monographs (`GUIDELINE`) like ADA, KDIGO, ESC, NICE, and WHO.
- **Publication Year & Chapter Number Hardening (`preready/runner.py`)**: Isolated 4-digit publication years (`1900-2099`, e.g. `2024`, `2026`) from chapter number extraction regex, preventing guideline years from erroneously being parsed as chapter numbers and defaulting monographs to chapter 1.
- **Alphanumeric & Supplement Page Marker Normalization (`preready/header_normalizer.py`)**: Expanded page marker regex to support supplement pages (`S1`-`S9999`, `Suppl. 12`, `P-12`, `A1`-`A99`) into non-destructive `<!-- page: ... -->` comments.
- **Universal Journal Masthead & URL Cleaning (`preready/header_normalizer.py`)**: Added generalized detection for journal headers, volume/supplement lines, DOI strings, and download URLs to prevent false chunk segmentation.

## [1.6.0] - 2026-09-02

### Added
- **Output Provenance & Version Stamping Standard (`preready/runner.py`, `preready/auditor.py`, `SKILL.md`)**: Enforced mandatory embedded top-level HTML comment provenance metadata blocks (`skill_name`, `skill_version`, `generated_at`, `source_path`) across all canonical markdown outputs (`*.markdown_inlined.md`) and audit reports (`*_TABLE_AUDIT.md`, `*_FIGURE_AUDIT.md`, `*_PREREADY_REPORT.md`), enabling complete version traceability across skill updates.

## [1.5.0] - 2026-09-02

### Added
- **RAG Subfolder Handover Protocol Synchronization (`SKILL.md`, `references/ocr_handover_contract.md`)**: Synchronized contract and pipeline handover specifications to reflect downstream RAG output routing to dedicated `<CHAPTER_DIR>/rag_pipeline_output/` subfolders and automatic asset mirroring.

## [1.4.0] - 2026-09-01

### Fixed
- **Figure Chapter Scope Isolation (`preready/image_normalizer.py`)**: Isolated per-match `fig_ch` variable from the caller's `ch_num` parameter, preventing cross-chapter figure citations (e.g. `Fig. 1.1` cited in Chapter 5) from mutating the chapter number for subsequent figure assets.
- **Forward Document Order Fallback Figure Indexing (`preready/image_normalizer.py`)**: Implemented two-pass match processing to ensure caption-less figure placeholders are assigned incremental indices (`fig_01`, `fig_02`, `fig_03`) in forward document order instead of reverse order.
- **Clinical Uppercase Heading Preservation (`preready/header_normalizer.py`)**: Removed blanket `isupper()` line deletion. Expanded explicit textbook watermark whitelist (`skip_exact`) and preserved standalone uppercase clinical headings (e.g. `ECG FINDINGS`, `MYOCARDIAL INFARCTION`, `CLINICAL FEATURES`).
- **Distributed Per-Chapter Layout Synchronization (`references/figure_naming_standards.md`)**: Synchronized documentation to reflect per-chapter `<CHAPTER_DIR>/assets/figures/` structure matching `preready.runner` and downstream pipeline expectations.

## [1.3.0] - 2026-09-01

### Added
- **Table Heading Deduplication on Lookback**: Replaces title lookback spans in-place rather than appending duplicate title lines.
- **GFM Table Delimiter Auto-Injection**: `ensure_table_delimiters()` automatically injects valid `|---|---|` delimiter rows into tables lacking standard GFM separators.

## [1.2.0] - 2026-09-01

### Added
- **Non-Destructive Page Number Preservation**: Converts isolated page numbers and running header page digits into `<!-- page: N -->` HTML comment anchors rather than deleting them, enabling downstream RAG page provenance.
- **Enhanced Table Lookback**: `inline_tables` looks back up to 5 non-blank lines before detached table placeholders (`[tbl-X.md]`) to capture box and table titles that were separated across OCR blank lines.

## [1.1.0] - 2026-09-01

### Added
- **Default In-Place Output in Input Folders**: Output files (`{PREFIX}.pdf.markdown_inlined.md`, `assets/figures/`, audit reports) now generate directly inside each corresponding input directory by default without requiring `--out-dir`.
- **Multi-Chapter Batch CLI Support**: `preready.runner` supports passing multiple input directories to `--source-dir` for sequential batch processing.

## [1.0.0] - 2026-09-01

### Context

Initial release of the Davidson OCR Pre-Ready Pipeline skill. Automates the ingestion of raw multi-page OCR folders (`Ture_md_with_images/`), inlining detached table markdown files (`pages/page-*/tbl-*.md`), extracting and renaming figure assets into `assets/figures/ch{NN}_fig_{MM}.ext`, cleaning OCR running headers, and generating canonical `markdown_inlined.md` files compatible with `davidson-rag-pipeline-antigravity` (v2.15.0).

### Added

- **Table Inliner (`preready/table_inliner.py`)**: Resolves detached `[tbl-X.md]` placeholders and inlines full markdown tables with standardized `### 1.X` headings.
- **Image Normalizer (`preready/image_normalizer.py`)**: Copies and normalizes `pages/page-*/img-*.jpeg` into canonical `assets/figures/` files and binds descriptive markdown caption tags.
- **Header Normalizer (`preready/header_normalizer.py`)**: Strips running OCR headers and normalizes `#`, `##`, `###` heading hierarchy.
- **Auditor (`preready/auditor.py`)**: Generates `{PREFIX}_TABLE_AUDIT.md`, `{PREFIX}_FIGURE_AUDIT.md`, and `{PREFIX}_PREREADY_REPORT.md`.
- **Unified CLI Runner (`preready/runner.py`)**: Single-command execution entrypoint (`python -m preready.runner`).
- **Comprehensive Reference Documentation (`references/`)**: `ocr_handover_contract.md`, `figure_naming_standards.md`, and `table_inlining_rules.md`.
- **Unit & Integration Test Suite (`tests/`)**: 100% test coverage across all modules.
