# Medical Book Split & OCR Ingestion Layout Specification

## Canonical Directory Structure

```
<Book Split Root>\
└── <Section_or_Part_BaseName>\
    ├── <Section_or_Part_BaseName>.pdf          # Source PDF
    └── ocr markdown\
        └── <Section_or_Part_BaseName>.pdf\     # Isolated OCR extraction directory
            ├── markdown.md                     # Raw OCR markdown
            └── pages\                          # Sliced page assets (tbl-*.md, img-*.jpeg)
```

## Downstream Pipeline Compatibility

### 1. NTFS Collision Isolation
On Windows (NTFS), file and directory names share a single namespace. A file named `Index.pdf` and a folder named `Index.pdf` cannot coexist within the same parent folder. Placing the OCR extraction directory inside `ocr markdown/` completely eliminates collision risk.

### 2. `davidson-ocr-preready` Integration
The downstream runner `preready.runner.py` uses `resolve_chapter_number` and `resolve_prefix` by parsing the directory's basename.
- Because the directory inside `ocr markdown/` retains its original name (`<Prefix>.pdf`), `runner.py` automatically detects:
  - Roman numerals (`SECTION I`, `SECTION II`, `SECTION IV`, etc.)
  - Arabic part numbers (`Harrison_22_PART 1`, `PART 12`, etc.)
  - Publication year ignores (`2026`, `2024`, etc.)
- Table inlining and figure image decoupling (`assets/figures/`) execute seamlessly in-place.

### 3. Downstream CDSS / RAG Indexing
Once pre-ready generation completes, the resulting `*.markdown_inlined.md` files feed into:
- `davidson-rag-pipeline-antigravity`
- `medical-index-rag-compiler`
- `harrison-cdss-navigator` / `hurst-cdss-navigator`
