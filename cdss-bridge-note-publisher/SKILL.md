---
name: cdss-bridge-note-publisher
version: 1.3.1
description: |
  Autonomous Generator, Claim-Level Grounding Verifier, and Multi-Modal Publisher for Davidson Cognitive Bridge Notes (V2.2 Standard).
  Orchestrates cross-book retrieval across Davidson 25, Harrison 22, Hurst 15, and Kumar & Clark 11, enforces the 6-layer source hierarchy,
  runs zero-hallucination attribution gates, applies anti-mojibake & LaTeX sanitization, and compiles journal-grade Word (.docx) documents
  featuring Native Word Card Grid Tables (zero ASCII staircase art) and 4x Lanczos-enhanced figures.
---

# CDSS Bridge Note Publisher (v1.3.1)

Production-grade clinical document synthesis and publishing engine for medical Clinical Decision Support Systems (CDSS). Closes the operational gap between raw textbook retrieval chunks and verified, publication-grade clinical bridge notes.

---

## 🎯 1. When to Activate This Skill

Activate this skill automatically whenever:
- The user or physician asks to **"make a comprehensive clinical note"**, **"generate a bridge note"**, or **"create a topic dossier"** from the CDSS textbook package.
- Creating clinical study materials according to the **Davidson Bridge Note Generation Prompt V2.2**.
- Converting clinical markdown notes into **executive Word (.docx) documents** with high-resolution figures and structured visual card tables.
- Auditing a clinical note for **claim-level grounding and zero-hallucination verification** against local textbook chunks.
- Requiring **Native Word Card Tables** and **Border-Accented Alert Cards** to replace ugly, broken ASCII diagrams.

---

## 🏛️ 2. The Davidson Bridge Note V2.2 Architecture

Every bridge note produced by this skill adheres strictly to the 6-layer cognitive hierarchy:

| Layer / Section | Governing Source | Operational Rule |
| :--- | :--- | :--- |
| **Coverage Declaration** | Metadata Box | Declares assigned chapter, core concepts, and target book scope in a border-accented callout card. |
| **Visual Assets Packet** | All 4 Textbooks | Table cataloging all figures, source plates, captions, and clinical relevance before text begins. |
| **Layer 0: Physiology Foundation** | Biophysics & Wiggers | Mechanical and fluid dynamics foundation (valve orifices, pressure gradients, turbulence). |
| **Layer 1: Pre-Training Terms** | Medical Dictionary | Explicit terminology definitions to prevent comprehension gaps. |
| **Layer 2: Protected Davidson Core Spine** | **Strictly Davidson 25th Ed** | **Inviolable source truth.** Text, clinical boxes, and figures from Davidson Ch 16. Zero external book adulteration allowed. |
| **QB Awareness / Exam Trap Warning** | Harrison 22 & Hurst 15 | Dedicated border-accented alert card highlighting acute lethal exceptions and board exam traps (e.g. acute MR lack of pansystolic murmur, Brockenbrough sign). |
| **Layer 3: Pharmacology Context** | Hurst 15 & Harrison 22 | Pharmacodynamic mechanisms for bedside dynamic maneuvers (amyl nitrite, phenylephrine, beta-blockers). |
| **Layer 4: Beyond Davidson Multi-Book** | Harrison, Hurst, K&C | Differential diagnoses, phonocardiograms, and pediatric shunt dynamics that Davidson mentions but does not illustrate. |
| **Clinical Evidence Notes** | ESC & AHA Guidelines | Guideline recommendations (Class I/II/III) validating clinical management and echocardiography triggers. |
| **Layer 5: Active Recall & Quick Revision** | Multi-Book Synthesis | Question-prompt flashcards and a 10-bullet rapid review summary box with explicit chunk citations. |

### 2.1 The 5-Point Discrepancy Resolution Protocol
1. **Dual-Truth Architecture**: Davidson 25th Edition provides the Curricular Baseline Truth; Harrison 22nd and Hurst 15th Edition provide the Acute Lethal Exceptions (quarantined in QB Awareness).
2. **Format Parity**: Zero ASCII art (`+---`, `|`) in either Markdown or Word. Both use clean, responsive table card grids.
3. **Biophysical Provenance Guard**: Layer 0 fluid mechanics are qualitative only; mathematical derivations are barred unless in source chunks.
4. **Vocabulary Provenance**: Layer 1 vocabulary table requires a mandatory `Textbook Provenance` column.
5. **Universal Chunk Anchoring**: Layer 5 flashcards and revision bullets must cite their originating textbook chunk ID.

---

## 🛡️ 3. Quality Assurance & Publishing Pipeline

```
[1. Context Packet Retrieval] ──> [2. Multi-Tier Note Synthesis] ──> [3. Zero-Hallucination Gate] ──> [4. Anti-Mojibake Filter] ──> [5. Executive Docx Compilation]
```

1. **Grounded Retrieval**: Queries `medical-cdss-unified-orchestrator --build-context-packet` to retrieve verbatim chunks.
2. **Zero-Hallucination Gate (`scripts/verify_grounding.py`)**: Enforces "No Chunk, No Result". Flags any formula or claim lacking chunk attribution.
3. **Anti-Mojibake & LaTeX Gate (`cdss-unicode-mojibake-guard`)**: Pipes markdown through Layer 8 to ensure zero unrendered LaTeX (`$\ge$`, `$S_3$`, `\text{--}`) enters output.
4. **Figure Super-Sampling (`scripts/enhance_figures.py`)**: Automatically detects low-resolution OCR crops (< 600 px) and applies Lanczos-4 sub-pixel upscaling + unsharp masking.
5. **Native Word Card Grid Engine (`scripts/publish_executive_docx.py`)**: Converts clinical frameworks into native Word multi-column tables with `#0A2540` navy headers and solid `#F8FAFC` cell backgrounds, permanently eliminating broken ASCII staircase boxes.

---

## 💻 4. CLI Quick-Start

### 1. End-to-End Bridge Note Synthesis & Publishing
```powershell
python "C:\Users\User\.gemini\config\skills\cdss-bridge-note-publisher\scripts\synthesize_bridge_note.py" `
  --topic "Cardiac Murmurs" `
  --output-dir "D:\01_Medical_Study\CDSS_human_test"
```

### 2. Verify Grounding & Attribution (Audit Mode)
```powershell
python "C:\Users\User\.gemini\config\skills\cdss-bridge-note-publisher\scripts\verify_grounding.py" `
  --note "D:\01_Medical_Study\CDSS_human_test\Davidson_Bridge_Note_Cardiac_Murmurs_V2.2.md" `
  --package-dir "D:\01_Medical_Study\CDSS_Retrieval_Package"
```

### 3. Compile Executive Word Document (.docx) with Native Card Grids
```powershell
python "C:\Users\User\.gemini\config\skills\cdss-bridge-note-publisher\scripts\publish_executive_docx.py" `
  --input-md "D:\01_Medical_Study\CDSS_human_test\Davidson_Bridge_Note_Cardiac_Murmurs_V2.2.md" `
  --output-docx "D:\01_Medical_Study\CDSS_human_test\Davidson_Bridge_Note_Cardiac_Murmurs_V2.2_Executive.docx"
```

## Grounding Gate & Citation Format (2026-09-25)
- The publisher does not write note content. It publishes an existing note that matches `--note-id` / `--topic`.
- `verify_grounding.py` is fail-closed and reads the package (`--package-dir`, env `CDSS_PACKAGE_DIR`). Every claim line in Layer 1, Layer 2, QB Awareness, Layer 3, Layer 4 and Layer 5 must cite a source that exists in the package:
  - `[Anchor: Davidson-16-L2-045]` (book-chapter-chunk; preferred)
  - `[chunk: L2-045]`
  - Free-text provenance, e.g. `Davidson Ch. 16 (Chunk L2-064)` or `[Anchor: Harrison Ch. 44, Fig. 44.4 / Chunk L2-024]`
  - `Box 16.89` / `Table 16.3` / `Figure 16.2`: attributed to the nearest book name before it (Davidson by default in Layer 2), and the box/table/figure must exist in that book's package text
  - Harrison and Hurst are packaged by Part/Section, so a "Ch. N" cannot be mapped to a file. Those chunk ids are matched by id only and reported as `weak_citations`.
- Layer 2 may cite Davidson only. Coverage Declaration, Visual Assets, Layer 0 and Clinical Evidence Notes are exempt.
- Cleanroom output goes to `<output-dir>/cleanroom/`; the source note is never rewritten.
- Publishing fails if any referenced image is missing (`publish_executive_docx.py --allow-missing-images` overrides this).
