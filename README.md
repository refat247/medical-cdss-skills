# Medical CDSS & Antigravity Agent Skills

A modular suite of 29 production-grade clinical decision support (CDSS), medical textbook RAG pipelines, clinical presentation systems, knowledge curation tools, and autonomous agent orchestration skills designed for Google Antigravity and medical AI agents.

## Repository Overview

This repository houses verified skills built for multi-textbook internal medicine federation, clinical decision support pipelines, OCR ingestion, clinical claim grounding, evidence-locked presentations, Notion knowledge curation, and token-optimized execution.

### Master Medical Textbooks Supported
- **Davidson's Principles and Practice of Medicine** (25th Edition)
- **Harrison's Principles of Internal Medicine** (22nd Edition)
- **Fuster & Hurst's The Heart** (15th Edition)
- **Kumar and Clark's Clinical Medicine** (11th Edition 2026)
- **Dr. Kawsar Uddin's Habijabi Bedside Series** (137 clinical heuristics records)

---

## Skills Catalog (29 Skills)

### 1. Clinical Decision Support & Textbook Navigation
| Skill | Role / Function |
| :--- | :--- |
| **`medical-cdss-unified-orchestrator`** | Cross-book diagnostic retrieval orchestrator across Davidson, Harrison, Hurst, and Kumar & Clark with zero-hallucination therapy verification. |
| **`clinical-preceptor-cdss-orchestrator`** | Universal clinical preceptor and bedside case CDSS engine (13 clinical modalities including Socratic ward rounds, SBA generation, toxic matrices). |
| **`harrison-cdss-navigator`** | Autonomous CDSS navigator & precision index retrieval across Harrison's 22nd Edition (10,419 clinical chunks). |
| **`hurst-cdss-navigator`** | Autonomous CDSS navigator & precision index retrieval across Fuster & Hurst's The Heart 15th Edition (5,258 cardiology chunks). |
| **`kumar-cdss-navigator`** | Autonomous CDSS navigator & precision index retrieval across Kumar & Clark 11th Edition (9,394 chunks). |
| **`kawsar-habijabi-cdss-navigator`** | Bedside heuristics navigator & FCPS/MRCP exam generator for Dr. Kawsar Uddin's Habijabi internal medicine series. |
| **`cdss-retrieval-packager`** | Autonomous packager, pruner, path patcher, and federated search orchestrator for CDSS corpora. |

### 2. Medical Textbook RAG & OCR Manufacturing Pipeline
| Skill | Role / Function |
| :--- | :--- |
| **`davidson-rag-pipeline-antigravity`** | Full 18-stage RAG pipeline for Davidson 25th Edition and clinical practice guidelines (ADA, KDIGO, ESC, NICE). |
| **`davidson-ocr-preready`** | Multi-modal asset normalizer and OCR pre-ready inliner for Mistral OCR and Document AI outputs. |
| **`medical-book-split-ocr-organizer`** | Automated directory structure setup, source PDF organization, and OCR extraction routing. |
| **`medical-index-rag-compiler`** | Back-of-the-book index compiler generating GraphRAG networks, GBNF grammars, and CDSS query routers. |
| **`medical-rag-orchestrator`** | Master build orchestrator and lifecycle chaining runner uniting the 7-stage manufacturing line. |
| **`cdss-bridge-note-publisher`** | Autonomous generator, claim-level grounding verifier, and multi-modal publisher for Davidson Cognitive Bridge Notes (V2.2 Standard). |
| **`cdss-unicode-mojibake-guard`** | Pre-flight Unicode auditor, UTF-8 in-place repair, ISMP clinical safety symbol enforcement, and LaTeX de-delimiter guard. |

### 3. Clinical Presentations & Study Guides
| Skill | Role / Function |
| :--- | :--- |
| **`clinical-pptx-builder`** | Create, edit, merge, and audit clinical/academic PowerPoint decks with source-traceable content, geometry-first layouts, and QA. |
| **`evidence-locked-clinical-pptx-builder`** | Evidence-locked clinical presentation system with source/correction control, decision nodes, and full-render visual QA (v2.3.0). |
| **`speaker-notes-builder`** | Evidence-bounded, deck-aware speaker notes builder from PPTX/PDF with rehearsal companion DOCX generation. |
| **`offline-study-guide`** | Self-contained offline HTML study guide generator with chapter navigation, search, section bookmarks, and A4 print layout. |

### 4. Notion Workspace, Knowledge Curation & Research
| Skill | Role / Function |
| :--- | :--- |
| **`notion-workspace-curator`** | Audit, design, repair, and maintain Notion workspaces, hubs, dashboards, databases, and mobile documentation systems. |
| **`notion-content-auditor`** | Audit substantive Notion knowledge for completeness, accuracy, provenance, contradictions, and reality alignment. |
| **`research-method-curator`** | Design high-integrity research outputs, claim verification, deep research prompts, and anti-hallucination research workflows. |
| **`humanizer-niqs-bridge`** | Prose-cleanup engine enforcing the Khaled Knowledge OS NIQS preservation boundary for evidence-bearing, clinical, and legal text. |
| **`humanizer`** | Rewrite AI-sounding text to read naturally like human writing while strictly preserving all facts, claims, and data. |
| **`mobile-first-google-sheets`** | Design, audit, repair, and QA phone-first Google Sheets workflows with low-friction entry, mobile navigation, validation, performance, protection, and native conversion verification. |

### 5. Antigravity Agent Protocols, Auditing & Maintenance
| Skill | Role / Function |
| :--- | :--- |
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
1. Clone this repository into your Antigravity skills configuration path:
   ```bash
   git clone https://github.com/refat247/medical-cdss-skills.git
   ```
2. Skills are automatically detected and activated by their trigger keywords and task domains.
