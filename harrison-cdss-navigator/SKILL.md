---
name: harrison-cdss-navigator
version: 1.0.2
description: |
  Autonomous Clinical Decision Support System (CDSS) and zero-token precision index retrieval navigator for
  Harrison's Principles of Internal Medicine (22nd Edition). Use when querying Harrison as a single standalone book
  (for multi-book federated queries across all textbooks, use medical-cdss-unified-orchestrator).
  Provides multi-turn clinical QA, case vignette decomposition, and 120-word span compression across 10,419 chunks.
---

# Harrison CDSS Navigator (v1.0.2)

Production-grade Clinical Decision Support System and Index Retrieval Engine grounded directly in the 22nd Edition of *Harrison's Principles of Internal Medicine* (3,900+ pages, 20 clinical parts, 10,419 L2 micro-chunks, 7,811 indexed clinical concepts, and 57,015 indexed vocabulary terms).

> [!IMPORTANT]
> **Zero-Hallucination & Provenance Guarantee**:
> All medical acronyms, clinical classifications, drug indications, and concept hierarchies are strictly derived from the 20 parsed chapters and synthesized index of Harrison's 22nd Edition. Every recommendation is traceable to concrete textbook chunks and sections.

---

## 🎯 When to Activate This Skill

Activate this skill whenever:
- The user or physician asks an **internal medicine clinical question**, disease overview, or diagnostic inquiry.
- Solving or analyzing **clinical case vignettes** (e.g. FCPS, USMLE Step 2/3, MRCP, ABIM, or internal medicine residency/fellowship exams).
- Validating **drug therapy indications, contraindications, or safety** across cardiovascular, infectious, endocrine, renal, respiratory, rheumatologic, or neurological disorders.
- Resolving **differential diagnoses and mimickers** (*DKA vs HHS*, *NSTEMI vs STEMI*, *Crohn vs Ulcerative Colitis*, *Bacterial vs Viral Meningitis*).
- Requiring **token-efficient prompt checklists** (`--outline`) or **span-compressed micro-windows** (`--compress`).

---

## 💻 Engine CLI Quick-Start

The underlying engine script is located at:
`C:\Users\User\.gemini\config\skills\harrison-cdss-navigator\scripts\navigator.py`
*(The navigator internally resolves the CDSS Retrieval Package or source split paths with automatic fallback.)*

### 1. Complex Clinical Case Vignette Decomposition
```powershell
python "C:\Users\User\.gemini\config\skills\harrison-cdss-navigator\scripts\navigator.py" --vignette "65-year-old male with type 2 diabetes presents with acute crushing chest pain, BP 85/55 mmHg, HR 115 bpm, diaphoresis, and elevated troponin."
```

### 2. Extractive Span-Compressed Retrieval (-80% Token Cost)
```powershell
python "C:\Users\User\.gemini\config\skills\harrison-cdss-navigator\scripts\navigator.py" --query "Acute myocardial infarction management" --compress
```

### 3. Prompt-Ready Medical Outline Checklist (120 Tokens)
```powershell
python "C:\Users\User\.gemini\config\skills\harrison-cdss-navigator\scripts\navigator.py" --outline "Diabetic Ketoacidosis"
```

### 4. Differential Diagnosis & "Vs." Comparator Lookup
```powershell
python "C:\Users\User\.gemini\config\skills\harrison-cdss-navigator\scripts\navigator.py" --diff "Meningitis"
```

### 5. Therapy Validation Guardrail
```powershell
python "C:\Users\User\.gemini\config\skills\harrison-cdss-navigator\scripts\navigator.py" --validate-therapy "Aspirin" "myocardial infarction"
```

### 6. Syndromic Comorbidity & Co-Occurrence Lookup
```powershell
python "C:\Users\User\.gemini\config\skills\harrison-cdss-navigator\scripts\navigator.py" --comorbidities "Diabetes mellitus"
```

### 7. Interactive Physician Shell
```powershell
python "C:\Users\User\.gemini\config\skills\harrison-cdss-navigator\scripts\navigator.py" --interactive
```

---

## 🏛️ Knowledge Architecture Reference

The navigator operates over **26 interconnected clinical assets**:
- `harrison_chunks_master_catalog.json`: 10,419 L2 clinical micro-chunks.
- `harrison_inverted_chunk_index.json`: 57,015 indexed vocabulary terms.
- `harrison_early_exit_section_index.json`: 4,154 sub-millisecond routing anchors (< 0.2 ms latency).
- `harrison_canonical_semantic_cache.json`: 161 pre-computed canonical intents (0 ms latency).
- `harrison_polysemy_disambiguation.json`: 254 disambiguated medical hubs.
- `harrison_concept_subtrees.json`: 161 prompt-ready medical checklists.
- `harrison_entity_grammar.gbnf`: Formal GBNF grammar for zero-hallucination constrained decoding.
- `harrison_typographical_anchors.json`: 9,567 typographical and table anchors.
- `harrison_clinical_cooccurrence_graph.json`: Page-level syndromic co-occurrence edges.
- `harrison_drug_disease_safety_matrix.json`: Drug indications and safety guardrails.
- `cdss_qa_router.py`: Production-grade CDSS execution engine.
- `BENCHMARK_SCORECARD.md`: 768-triplet retrieval benchmark report.

---

## 📋 CDSS Execution Protocol for AI Agents

When acting as a medical assistant or answering clinical queries:
1. **Analyze Clinical Intent**:
   - If the user provides a full patient story -> Use `--vignette`.
   - If the user asks for guidelines/overview -> Use `--outline` first to get the checklist, then query specific chunks with `--compress`.
   - If the user is debating between two look-alike conditions -> Use `--diff`.
   - If the user asks whether a drug can be prescribed -> Use `--validate-therapy`.
2. **Inject Compressed Micro-Spans**: Never dump thousands of tokens of textbook prose into the context window. Use the span compressor (`--compress`) to inject targeted 120-word excerpts.
3. **Always Cite Textbook Coordinates**: Always cite the Section, Part Name, Topic Heading, and Chunk ID.

## Package Location (2026-09-25)
- Set `CDSS_PACKAGE_DIR` to override the default package path.
- The navigator exits 1 when the router is missing.
- A fallback to an unpackaged build router is announced with `[WARN]` on stderr.
