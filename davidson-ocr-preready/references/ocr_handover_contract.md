# OCR Pre-Ready Handover Contract with davidson-rag-pipeline-antigravity

This specification defines the 5 structural invariants guaranteed by `davidson-ocr-preready` when producing the input `{PREFIX}.pdf.markdown_inlined.md` for `davidson-rag-pipeline-antigravity` (v2.25.1).

---

## 1. File Path & Directory Layout Invariant

The pre-ready output files reside directly in the corresponding input chapter directory, and downstream RAG pipeline artifacts are stored in a dedicated `rag_pipeline_output/` subfolder:
```
<CHAPTER_DIR>/
├── markdown.md                            <-- Raw OCR Input
├── pages/                                 <-- Page directories (tbl-*.md, img-*.jpeg)
├── {PREFIX}.pdf.markdown_inlined.md       <-- Primary Pipeline Input (Inlined Canonical)
├── assets/figures/                        <-- Decoupled Figure Assets Store
│   ├── ch01_fig_01.jpeg
│   └── ch01_fig_02.jpeg ...
├── {PREFIX}_TABLE_AUDIT.md                <-- Inlined Table Verification
├── {PREFIX}_FIGURE_AUDIT.md               <-- Decoupled Figure Alignment
├── {PREFIX}_PREREADY_REPORT.md            <-- Master Scorecard
└── rag_pipeline_output/                   <-- Dedicated RAG Pipeline Output Subfolder
    ├── assets/figures/                    <-- Mirrored Figure Assets Store
    ├── {PREFIX}_CHECKPOINT.json
    ├── {PREFIX}_REPAIRED_S2.md
    ├── {PREFIX}_chunks.md
    └── {PREFIX}_RAG_Optimised.md ...
```

---

## 2. Table Inlining Invariant

All OCR placeholders (`[tbl-X.md](tbl-X.md)`) are replaced with full Markdown tables:
* Standard markdown pipe syntax (`| Header | Header |`).
* Explicit table / box title with `###` level heading:
  ```markdown
  ### 1.1 Root causes of diagnostic error in studies

  | Error category | Examples |
  |---|---|
  | No fault | Unusual presentation of a disease |
  ```
* Guaranteed to satisfy **Stage 1 (Forensic Audit)** and **Stage 4.5 (Table Parity)**.

---

## 3. Decoupled Multi-Modal Figure Asset Invariant (Rule R)

All image placeholders (`![img-X.jpeg](img-X.jpeg)`) are replaced with standardized decoupled asset tags:
* Relative path pointing to `assets/figures/ch{NN}_fig_{MM:02d}.ext`.
* Descriptive caption extracted from the textbook figure legend:
  ```markdown
  ![Fig 1.1: Likelihood ratio of Kernig sign](assets/figures/ch01_fig_01.jpeg)
  ```
* Guaranteed to satisfy **Stage 4B (`extract_figure_metadata`)** and **Stage 6 (Invariant 6.5)**.

---

## 4. Heading Hierarchy & Watermark Stripping Invariant

* Chapter title formatted as `# {Title}`.
* Primary sections formatted as `## {Section}`.
* Subsections and Boxes formatted as `### {Subsection}`.
* All isolated OCR running headers (`Medical HIGHER STUDY`, stray single digits) stripped cleanly to prevent false-positive chunk cuts.

---

## 5. Mathematical & Numerical Preservation Invariant

100% of textbook words, drug doses, numerical equations, and probability expressions are preserved byte-for-byte to guarantee passing **Stage 4.5c (Source Coverage Gate)** and **Stage 4.5d (Clinical Fidelity Gate)**.
