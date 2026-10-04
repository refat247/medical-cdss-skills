---
name: cdss-retrieval-packager
version: 1.5.1
description: |
  Autonomous Packager, Pruner, Path Patcher, and Federated Search Orchestrator for medical textbook
  Clinical Decision Support Systems (CDSS). Extracts pure retrieval assets (*_RAG_Optimised.md, *_chunks.md,
  assets/figures/*.jpeg, Index/), prunes build-time QA scorecards/zips, enforces dynamic relative pathing,
  generates federated search CLIs, and verifies sub-millisecond retrieval health.
---

# CDSS Retrieval Packager (v1.5.1)

Production-grade utility for compiling, pruning, and validating lean, high-performance **CDSS Retrieval Packages** from compiled medical textbook libraries (*Davidson*, *Harrison*, *Hurst*, *Braunwald*, *Kumar & Clark*).

---

## 🎯 1. When to Activate This Skill

Activate this skill automatically whenever:
- A medical textbook or guideline has completed the RAG pipeline (`*_RAG_Optimised.md`, `*_chunks.md`) and index intelligence suite (`Index/` router, GraphRAG, BM25 inverted indexes).
- The user asks to:
  - **"Make a retrieval package"** or **"package this book for CDSS"**.
  - **"Audit figure resolutions or upscale low-res OCR images"** (`scripts/enhance_figures.py`).
  - **"Prune non-retrieval files"** or **"clean scorecards while keeping images"**.
  - **"Create a federated search across our books"** or **"unify CDSS routers"**.
  - **"Test/verify if our CDSS package is production ready"**.
  - **"Ensure router paths are relative and portable"**.

---

## 🏗️ 2. Package Architecture & Pure Retrieval Standards

A compliant CDSS Retrieval Package contains **only pure retrieval assets** and strictly adheres to the following layout:

```
CDSS_Retrieval_Package/
├── cdss_federated_search.py            # Unified cross-book search CLI (--json support)
├── README.md                           # Package documentation & API examples
│
├── 01_Davidson_25/
│   ├── Index/cdss_global_index/        # SQLite DB (DAVIDSON_25_CDSS_ENGINE.db), calculators
│   ├── Davidson_25_Ch01_.../
│   │   ├── *_RAG_Optimised.md          # Stage 18 clean markdown
│   │   ├── *_chunks.md                 # Discrete L2/L3 semantic retrieval spans
│   │   └── assets/                     # figures/*.jpeg & tables/*.md (100% PRESERVED)
│   └── ... (all clinical chapters)
│
├── 02_Harrison_22/
│   ├── Index/                          # cdss_qa_router.py, GraphRAG, inverted index, GBNF
│   └── ... (all clinical parts)
│
├── 03_Hurst_The_Heart_15/
│   ├── Index/                          # cdss_qa_router.py, GraphRAG, safety matrix
│   └── ... (all clinical sections)
│
└── 04_Kumar_and_Clark_11/
    ├── Index/                          # cdss_qa_router.py, GraphRAG, inverted index, master catalog
    ├── 01_Chapters/                    # 50 chapters (*_RAG_Optimised.md, *_chunks.md, assets/figures/)
    ├── 02_MCQs_and_Answers/            # Board review MCQs and Answers markdown
    └── 03_Index_and_Reference_Intervals/ # Clinical reference intervals & comprehensive index
```

---

## ⚡ 3. CLI Reference (`scripts/packager.py`)

The skill runner is executed via Python or `uv run`:

### 1. End-to-End Autonomous Optimization (`auto`)
Runs prune, patch-paths, federate, and verification in a single automated step:
```bash
python "C:\Users\User\.gemini\config\skills\cdss-retrieval-packager\scripts\packager.py" auto `
  --package-dir "D:\01_Medical_Study\CDSS_Retrieval_Package"
```

### 2. Prune Build-Time Artifacts (`prune`)
Purges all build-time QA scorecards (`QualityScorecard.*`, `ClinicalFidelity.*`), trust manifests (`CORPUS_OUTPUT_PROTECTED.json`), and cold backup archives (`*.zip`) while **strictly preserving all `.jpeg` and `.png` clinical images**:
```bash
python "C:\Users\User\.gemini\config\skills\cdss-retrieval-packager\scripts\packager.py" prune `
  --package-dir "D:\01_Medical_Study\CDSS_Retrieval_Package"
```

### 3. Patch Paths for Portability (`patch-paths`)
Audits and updates hardcoded absolute paths in Python router scripts to use dynamic relative resolution (`Path(__file__).resolve().parent`):
```bash
python "C:\Users\User\.gemini\config\skills\cdss-retrieval-packager\scripts\packager.py" patch-paths `
  --package-dir "D:\01_Medical_Study\CDSS_Retrieval_Package"
```

### 4. Generate Unified Federated CLI (`federate`)
Generates or updates the root `cdss_federated_search.py` and `README.md`:
```bash
python "C:\Users\User\.gemini\config\skills\cdss-retrieval-packager\scripts\packager.py" federate `
  --package-dir "D:\01_Medical_Study\CDSS_Retrieval_Package"
```

### 5. Automated Health Smoke Tests (`verify`)
Executes live retrieval queries on all packaged routers and confirms sub-millisecond execution:
```bash
python "C:\Users\User\.gemini\config\skills\cdss-retrieval-packager\scripts\packager.py" verify `
  --package-dir "D:\01_Medical_Study\CDSS_Retrieval_Package"
```

---

## 🛡️ 4. Non-Negotiable Architectural Rules

> [!IMPORTANT]
> 1. **Zero-Touch Source Library Rule**: All packaging operations are strictly read-only with respect to source repositories (`SPLIT Pdfs` and golden master folders). Never alter or delete source textbook files.
> 2. **Multimodal Preservation Rule**: Never delete, prune, or omit `.jpeg` or `.png` images located inside chapter `assets/figures/`. Multimodal CDSS retrieval requires diagnostic ECGs, histology micrographs, and flowcharts.
> 3. **Dynamic Path Resolution Rule**: Every router script (`cdss_qa_router.py`, `cdss_retrieval_client.py`) must resolve paths dynamically relative to `__file__`. Never leave hardcoded drive letters or absolute directories.
> 4. **Fail-Closed Verification Rule**: A CDSS retrieval package is not declared production-ready until automated test queries execute with zero errors and return valid clinical micro-spans in < 100 ms.

---

## 🔗 5. Cross-References

| Relationship | Skill | Role |
| :--- | :--- | :--- |
| **Upstream** | `medical-index-rag-compiler` | Produces the CDSS assets this skill packages |
| **Upstream** | `cdss-unicode-mojibake-guard` | Sanitizes corpus encoding before packaging |
| **Downstream** | `medical-cdss-unified-orchestrator` | Consumes the federated retrieval package |
| **Downstream** | `harrison-cdss-navigator`, `hurst-cdss-navigator`, `kumar-cdss-navigator` | Book-specific navigators using packaged routers |
| **Orchestrator** | `medical-rag-orchestrator` | Invokes this skill as Stage 5 of the pipeline |

## Verification Additions (2026-09-25)
- `verify` / `auto` now check that every image link in packaged `*_RAG_Optimised.md` / `*_chunks.md` resolves to a file, and exit 1 if any check fails.
- README counts and status are generated from the package contents and the latest verification. Nothing is hardcoded.
- `compress_excerpt` returns whole sentences only, so exception clauses (`unless`, `except`) are never cut. The generated `cdss_federated_search.py` reuses the same function, and a test checks that it compiles.
