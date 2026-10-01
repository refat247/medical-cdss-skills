# Medical CDSS & Antigravity Agent Skills

A modular suite of 19 specialized clinical decision support (CDSS), medical textbook RAG, and autonomous agent orchestration skills designed for Google Antigravity and medical AI agents.

## Repository Overview

This repository houses production-grade clinical AI skills built for multi-textbook internal medicine federation, clinical decision support pipelines, OCR ingestion, clinical claim grounding, and token-optimized execution.

### Master Medical Textbooks Supported
- **Davidson's Principles and Practice of Medicine** (25th Edition)
- **Harrison's Principles of Internal Medicine** (22nd Edition)
- **Fuster & Hurst's The Heart** (15th Edition)
- **Kumar and Clark's Clinical Medicine** (11th Edition 2026)
- **Dr. Kawsar Uddin's Habijabi Bedside Series** (137 clinical heuristics records)

---

## Skills Directory

| Skill | Role / Function |
| :--- | :--- |
| **`medical-cdss-unified-orchestrator`** | Cross-book diagnostic retrieval orchestrator across Davidson, Harrison, Hurst, and Kumar & Clark with zero-hallucination therapy verification. |
| **`clinical-preceptor-cdss-orchestrator`** | Universal clinical preceptor and bedside case CDSS engine (13 clinical modalities including Socratic ward rounds, SBA generation, toxic matrices). |
| **`harrison-cdss-navigator`** | Autonomous CDSS navigator & precision index retrieval across Harrison's 22nd Edition (10,419 clinical chunks). |
| **`hurst-cdss-navigator`** | Autonomous CDSS navigator & precision index retrieval across Fuster & Hurst's The Heart 15th Edition (5,258 cardiology chunks). |
| **`kumar-cdss-navigator`** | Autonomous CDSS navigator & precision index retrieval across Kumar & Clark 11th Edition (9,394 chunks). |
| **`kawsar-habijabi-cdss-navigator`** | Bedside heuristics navigator & FCPS/MRCP exam generator for Dr. Kawsar Uddin's Habijabi internal medicine series. |
| **`davidson-rag-pipeline-antigravity`** | Full 18-stage RAG pipeline for Davidson 25th Edition and clinical practice guidelines (ADA, KDIGO, ESC, NICE). |
| **`davidson-ocr-preready`** | Multi-modal asset normalizer and OCR pre-ready inliner for Mistral OCR and Document AI outputs. |
| **`medical-book-split-ocr-organizer`** | Automated directory structure setup, source PDF organization, and OCR extraction routing. |
| **`medical-index-rag-compiler`** | Back-of-the-book index compiler generating GraphRAG networks, GBNF grammars, and CDSS query routers. |
| **`medical-rag-orchestrator`** | Master build orchestrator and lifecycle chaining runner uniting the 7-stage manufacturing line. |
| **`cdss-bridge-note-publisher`** | Autonomous generator, claim-level grounding verifier, and multi-modal publisher for Davidson Cognitive Bridge Notes (V2.2 Standard). |
| **`cdss-retrieval-packager`** | Autonomous packager, pruner, path patcher, and federated search orchestrator for CDSS corpora. |
| **`cdss-unicode-mojibake-guard`** | Pre-flight Unicode auditor, UTF-8 in-place repair, ISMP clinical safety symbol enforcement, and LaTeX de-delimiter guard. |
| **`antigravity-protocol`** | Execution protocol for high-efficiency planning, token conservation, and fast-path software engineering. |
| **`ultimate-protocol`** | Minified JSON compiler protocol for automated pipelines and non-human agent communication. |
| **`token-audit`** | Token waste, context bloat, prompt caching, and workspace configuration auditor. |
| **`clean-my-ai-harness`** | Agent harness auditor, skill conflict resolver, and safe environment cleanup manager. |
| **`version-manager`** | Universal semantic version bumper, release synchronizer, and Keep a Changelog manager. |

---

## Structure of a Skill

Each skill adheres to the Antigravity Skill Standard:
```
<skill-name>/
├── SKILL.md            # Metadata frontmatter, description, and agent instructions
├── README.md           # Documentation and usage guide
├── CHANGELOG.md        # Version history adhering to Keep a Changelog
├── scripts/            # Executable Python / PowerShell tools & runners
├── tests/              # Pytest verification suites
└── references/         # Clinical schemas, templates, and protocols
```

## Setup & Usage

To use these skills with Google Antigravity:
1. Clone or place this repository into your Antigravity skills configuration path:
   ```bash
   git clone https://github.com/refat247/medical-cdss-skills.git
   ```
2. Skills are automatically detected and activated by their trigger keywords and task domains.
