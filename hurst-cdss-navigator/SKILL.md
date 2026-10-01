---
name: hurst-cdss-navigator
version: 1.0.2
description: |
  Autonomous Clinical Decision Support System (CDSS) and zero-token precision index retrieval navigator for
  Fuster & Hurst's The Heart (15th Edition). Use when querying Hurst as a single standalone book
  (for multi-book federated queries across all textbooks, use medical-cdss-unified-orchestrator).
  Provides multi-turn clinical QA, case vignette decomposition, and 150-word span compression across 5,258 chunks.
---

# Hurst CDSS Navigator (v1.0.2)

Production-grade Clinical Decision Support System and Index Retrieval Engine grounded directly in the 15th Edition of *Fuster & Hurst's The Heart* (4,006 pages, 12 clinical sections, 541 tables, 2,166 figures, and 5,258 L2 micro-chunks).

> [!IMPORTANT]
> **Zero-Hallucination & Provenance Guarantee**:
> All medical acronyms, clinical trials, drug indications, and concept hierarchies are strictly derived from the textbook's curated back-of-the-book index. Every recommendation is traceable to concrete textbook chunks and cited page numbers.

---

## 🎯 When to Activate This Skill

Activate this skill whenever:
- The user or physician asks a **cardiology clinical question**, disease overview, or diagnostic inquiry.
- Solving or analyzing **clinical case vignettes** (e.g. FCPS, USMLE Step 2/3, MRCP, or cardiology fellowship exams).
- Looking up or verifying **landmark cardiology clinical trials** (e.g. *PARADIGM-HF*, *Look AHEAD*, *DAPT*, *COAPT*, *CABANA*, *ISCHEMIA*).
- Validating **drug therapy indications, contraindications, or safety** in specific cardiovascular conditions.
- Resolving **differential diagnoses and mimickers** (*Athlete's Heart vs HCM*, *Takotsubo vs AMI*, *Constrictive vs Restrictive*).
- Requiring **token-efficient prompt checklists** (`--outline`) or **span-compressed micro-windows** (`--compress`).

---

## 💻 Engine CLI Quick-Start

The underlying engine script is located at:
`C:\Users\User\.gemini\config\skills\hurst-cdss-navigator\scripts\navigator.py`
*(The navigator internally resolves the CDSS Retrieval Package or source split paths with automatic fallback.)*

### 1. Complex Clinical Case Vignette Decomposition
```powershell
python "C:\Users\User\.gemini\config\skills\hurst-cdss-navigator\scripts\navigator.py" --vignette "65-year-old male with prior anterior STEMI and EF 28% presents with acute pulmonary edema, BP 88/54 mmHg, HR 115 bpm, and Creatinine 2.6 mg/dL. Current drugs: Sacubitril/valsartan, spironolactone, and furosemide."
```

### 2. Extractive Span-Compressed Retrieval (-80% Token Cost)
```powershell
python "C:\Users\User\.gemini\config\skills\hurst-cdss-navigator\scripts\navigator.py" --query "Acute heart failure with renal dysfunction" --compress
```

### 3. Prompt-Ready Medical Outline Checklist (120 Tokens)
```powershell
python "C:\Users\User\.gemini\config\skills\hurst-cdss-navigator\scripts\navigator.py" --outline "Acute heart failure"
```

### 4. Differential Diagnosis & "Vs." Comparator Lookup
```powershell
python "C:\Users\User\.gemini\config\skills\hurst-cdss-navigator\scripts\navigator.py" --diff "Takotsubo"
```

### 5. Therapy Validation Guardrail
```powershell
python "C:\Users\User\.gemini\config\skills\hurst-cdss-navigator\scripts\navigator.py" --validate-therapy "Sacubitril/valsartan" "heart failure"
```

### 6. Syndromic Comorbidity & Co-Occurrence Lookup
```powershell
python "C:\Users\User\.gemini\config\skills\hurst-cdss-navigator\scripts\navigator.py" --comorbidities "Bicuspid aortic valve"
```

### 7. Interactive Physician Shell
```powershell
python "C:\Users\User\.gemini\config\skills\hurst-cdss-navigator\scripts\navigator.py" --interactive
```

---

## 🏛️ Knowledge Architecture Reference

The navigator operates over **24 interconnected clinical assets**:
- `hurst_chunks_master_catalog.json`: 5,258 L2 clinical micro-chunks.
- `hurst_canonical_semantic_cache.json`: 581 pre-computed canonical intents (0 ms latency).
- `hurst_differential_comparators.json`: 29 direct mimicker comparators with table links.
- `hurst_clinical_cooccurrence_graph.json`: 22,774 syndromic co-occurrence edges across 1,652 pages.
- `hurst_index_salience_bm25_weights.json`: 4,796 boosted token multipliers (up to $3.0\times$).
- `hurst_entity_grammar.gbnf`: Formal GBNF grammar for zero-hallucination constrained decoding.
- `cardiology_synonyms_and_acronyms.json`: 626 medical acronym/synonym pairs.
- `landmark_clinical_trials_registry.json`: 827 landmark randomized controlled trials.
- `index_concept_hierarchy.json`: 4,842 structured disease concept hierarchies.

---

## 📋 CDSS Execution Protocol for AI Agents

When acting as a medical assistant or answering cardiology queries:
1. **Analyze Clinical Intent**:
   - If the user provides a full patient story $\rightarrow$ Use `--vignette`.
   - If the user asks for guidelines/overview $\rightarrow$ Use `--outline` first to get the checklist, then query specific chunks with `--compress`.
   - If the user is debating between two look-alike conditions $\rightarrow$ Use `--diff`.
   - If the user asks whether a drug can be prescribed $\rightarrow$ Use `--validate-therapy`.
2. **Inject Compressed Micro-Spans**: Never dump thousands of tokens of textbook prose into the context window. Use the span compressor (`--compress`) to inject targeted 150-word excerpts.
3. **Always Cite Textbook Coordinates**: Always provide the Section, Chapter Topic, Chunk ID, and Book Page Number.

## Package Location (2026-09-25)
- Set `CDSS_PACKAGE_DIR` to override the default package path.
- The navigator exits 1 when the router is missing.
- A fallback to an unpackaged build router is announced with `[WARN]` on stderr.
