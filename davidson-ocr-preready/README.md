# davidson-ocr-preready (v1.7.6)

Automated Pre-Ready Inliner and Multi-Modal Asset Normalizer for raw OCR outputs of Davidson's Principles and Practice of Medicine (25th Edition) and Clinical Practice Guidelines (ADA, KDIGO, ESC, NICE).

## Overview

This package bridges raw multi-page OCR outputs (e.g. from Mistral OCR, Document AI, or MinerU) into the canonical `markdown_inlined.md` format required by the downstream `davidson-rag-pipeline-antigravity` RAG processing engine.

It universally supports both multi-chapter medical textbooks and society clinical practice monographs.

All outputs are generated **directly in the corresponding input folder** by default.

## Features

- **Automated Table Inlining**: Resolves `[tbl-X.md]` references from `pages/page-*/tbl-*.md` and inlines complete Markdown tables.
- **Decoupled Figure Asset Mapping**: Copies and standardizes `pages/page-*/img-*.jpeg` into `assets/figures/ch{NN}_fig_{MM}.ext` with descriptive captions.
- **OCR Running Header Cleaner**: Strips stray running headers, page numbers, and textbook watermark artifacts.
- **Audit Verification Reports**: Automatically outputs `{PREFIX}_TABLE_AUDIT.md`, `{PREFIX}_FIGURE_AUDIT.md`, and `{PREFIX}_PREREADY_REPORT.md` inside each input directory.
- **Multi-Chapter Batch Processing**: Process multiple chapter directories in a single command.

## CLI Usage

### Single Chapter (Outputs in corresponding input folder by default):
```bash
python -m preready.runner --source-dir "D:\davidson_25_true\TRUE_MD_WITH_IMAGES\Davidson_25_01_Clinical decision-making.pdf"
```

### Multiple Chapters Batch:
```bash
python -m preready.runner --source-dir "D:\davidson_25_true\TRUE_MD_WITH_IMAGES\Davidson_25_01_Clinical decision-making.pdf" "D:\davidson_25_true\TRUE_MD_WITH_IMAGES\Davidson_25_02_Clinical therapeutics and good prescribing.pdf"
```

## Handshake Contract with RAG Pipeline

Output files are guaranteed 100% compliant with `davidson-rag-pipeline-antigravity` v2.20.0:
1. Standard Markdown Tables (`|`) for Stage 1/4B.
2. Decoupled asset URIs (`assets/figures/chNN_fig_MM.*`) for Stage 4B and Stage 6 Invariant 6.5.
3. Clean heading depth hierarchy (`#`, `##`, `###`) for Stage 4A Heading Manifest.
4. Clean compatibility with downstream output placement into `<CHAPTER_DIR>/rag_pipeline_output/`.
