---
name: medical-book-split-ocr-organizer
version: 1.3.1
description: |
  Automates directory structure setup, source PDF organization, and OCR extraction routing
  for medical textbooks and clinical guidelines. Creates section folders from split PDFs, establishes
  'ocr markdown' isolation workspaces, and routes OCR outputs from Downloads or custom paths.
---

# Medical Book Split & OCR Organizer (v1.3.1)

Production-grade pipeline utility for structuring split medical textbook PDFs (Davidson, Hurst, Harrison, Braunwald) and routing raw OCR extractions (Mistral OCR Playground, Document AI) into standardized directory layouts compatible with downstream RAG and CDSS compilers.

---

## Capabilities

1. **Book Split Initialization (`init`)**:
   - Scans a split book directory for `.pdf` files.
   - Creates a dedicated folder for each PDF (matching its base name).
   - Moves the source `.pdf` into its section folder.
   - Generates an `ocr markdown/` subfolder in each section, preventing Windows NTFS directory/file namespace collisions.

2. **OCR Batch Ingestion (`ingest`)**:
   - Discovers OCR output folders from a source directory (defaults to `C:\Users\User\Downloads`, or any custom `--source-dir`).
   - Applies smart normalized name-matching (ignoring spaces vs. underscores, multiple spaces, case differences, and trailing `.pdf`).
   - Moves OCR extraction folders into `<Section>/ocr markdown/<Prefix>.pdf/`.
   - Protects against accidental overwrites by skipping existing populated folders (unless `--force` is passed).
   - Automatically cleans up empty browser download staging directories (e.g., `ocr-playground-download-*`).

3. **Combined Automation (`auto`)**:
   - Executes `init` followed by `ingest` in a single command.

4. **Section Completeness Audit (`status`)**:
   - Generates an audit table summarizing which sections have their source PDF and which have OCR markdown populated.

5. **Individual Section Normalization (`organize-section`)**:
   - Re-structures standalone unorganized guideline folders (e.g. `<Name>.pdf` containing raw OCR and PDF together) into canonical `<Name>/<Name>.pdf` + `ocr markdown/<Name>.pdf/` layout.

6. **Batch Book Normalization (`organize-book`)**:
   - Batch-normalizes all unorganized section folders in an entire book root directory into canonical layout.
   - Automatically discovers, matches, and incorporates source split PDFs from an external directory (`--pdf-source-dir`).
   - Updates RAG pipeline checkpoint JSON paths and runs an automated status audit upon completion.

---

## CLI Reference

The CLI runner is located at `scripts/organizer.py` and can be executed via `uv run` or standard `python`:

### 1. Initialize a Newly Split Book Directory:
```bash
uv run "C:\Users\User\.gemini\config\skills\medical-book-split-ocr-organizer\scripts\organizer.py" init --target-dir "D:\01_Medical_Study\SPLIT Pdfs\my_new_book"
```

### 2. Ingest OCR Extractions from Downloads (Default):
```bash
uv run "C:\Users\User\.gemini\config\skills\medical-book-split-ocr-organizer\scripts\organizer.py" ingest --target-dir "D:\01_Medical_Study\SPLIT Pdfs\my_new_book"
```

### 3. Ingest OCR Extractions from a Custom Folder:
```bash
uv run "C:\Users\User\.gemini\config\skills\medical-book-split-ocr-organizer\scripts\organizer.py" ingest --target-dir "D:\01_Medical_Study\SPLIT Pdfs\my_new_book" --source-dir "D:\OCR_Staging\Batch_1"
```

### 4. Overwrite Existing OCR Data:
```bash
uv run "C:\Users\User\.gemini\config\skills\medical-book-split-ocr-organizer\scripts\organizer.py" ingest --target-dir "D:\01_Medical_Study\SPLIT Pdfs\my_new_book" --force
```

### 5. Run Both Setup & Ingestion in One Step:
```bash
uv run "C:\Users\User\.gemini\config\skills\medical-book-split-ocr-organizer\scripts\organizer.py" auto --target-dir "D:\01_Medical_Study\SPLIT Pdfs\my_new_book" --source-dir "C:\Users\User\Downloads"
```

### 6. Audit Book Section Status:
```bash
uv run "C:\Users\User\.gemini\config\skills\medical-book-split-ocr-organizer\scripts\organizer.py" status --target-dir "D:\01_Medical_Study\SPLIT Pdfs\harrison split"
```

### 7. Batch Organize an Entire Book and Incorporate Split PDFs:
```bash
uv run "C:\Users\User\.gemini\config\skills\medical-book-split-ocr-organizer\scripts\organizer.py" organize-book --target-dir "D:\davidson_25_true\TRUE_MD_WITH_IMAGES(v2.23.0_made)" --pdf-source-dir "D:\davidson_25_true"
```

### 8. Organize Individual Section or Standalone Guideline:
```bash
uv run "C:\Users\User\.gemini\config\skills\medical-book-split-ocr-organizer\scripts\organizer.py" organize-section --target-dir "D:\01_Medical_Study\guideline\GUIDELINES & UPDATES-DR.ANANTO ISLAM-20260217T151836Z-1-001\National Guideline for the Management of Measles_2026.pdf"
```

---

## Downstream Pipeline Handoff

Once folders are organized by this skill:
1. Pass the organized chapter directory directly to **`davidson-ocr-preready`**:
   ```bash
   python -m preready.runner --source-dir "D:\01_Medical_Study\SPLIT Pdfs\harrison split\Harrison_22_PART 1 The Profession of Medicine\ocr markdown\Harrison_22_PART 1 The Profession of Medicine.pdf"
   ```
2. Downstream runners auto-detect chapter numbers and file prefixes without manual configuration.
3. Feed resulting `*.markdown_inlined.md` directly into **`davidson-rag-pipeline-antigravity`** or **`medical-index-rag-compiler`**.
