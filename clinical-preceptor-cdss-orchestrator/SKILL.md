---
name: clinical-preceptor-cdss-orchestrator
version: 1.2.1
description: |
  Universal Clinical Preceptor & Bedside Case CDSS Orchestrator for physician-authored clinical series,
  medical vignettes, and preceptor corpora. Automates full-lifecycle corpus manufacturing (workspace pre-scaffolding,
  SingleFile HTML ingestion, decoupled media extraction, semantic comment chatter pruning, structured English clinical
  synthesis, clinical claims extraction, and bidirectional textbook bridging) and provides a 13-modality clinical
  runtime engine (Socratic Preceptor, Exam SBA Generator, Prescribing Safety Guard, 4-Textbook Federation,
  Tropical Ward Calculator, Bilingual Retrieval, OSCE Visual Spotters, Residency Progression Curriculum,
  GraphRAG Causal Graphs, Acute SBAR Handovers, Bengali Patient Leaflets, Anki Cloze Decks, and Never-Events Toxic Matrix).
  Use for building/running a general preceptor corpus; for Habijabi-series-only queries use kawsar-habijabi-cdss-navigator, and for a federated textbook query use medical-cdss-unified-orchestrator.
---

# Clinical Preceptor CDSS Orchestrator (v1.2.1)

A universal, modular Clinical Decision Support System (CDSS) orchestrator and manufacturing pipeline designed for **physician-authored medical education series, bedside clinical case collections, and ward preceptorship archives**.

This skill provides **two integrated capabilities**:
1. **The Autonomous Manufacturing Pipeline**: From raw SingleFile HTML captures to clean, pruned, English-synthesized, audited CDSS RAG packages, and 7 extended clinical/educational artifacts.
2. **The 13-Modality Clinical Runtime Engine**: Morning report preceptor, postgraduate exam SBA generator, bedside prescribing safety interceptor, federated 4-textbook grounding, tropical ward calculations, hybrid bilingual retrieval, OSCE visual spotters, tiered residency curriculum, GraphRAG causal decision graphs, acute SBAR handovers, Bengali patient counseling leaflets, Anki spaced-repetition cloze decks, and ward toxic drug pharmacovigilance matrices.

---

## 🏗️ 1. Workspace Pre-Scaffolding (`--init-workspace`)

Before processing any new doctor's case captures, initialize the workspace to establish the standardized 12-directory CDSS architecture:

```powershell
python "C:\Users\User\.gemini\config\skills\clinical-preceptor-cdss-orchestrator\scripts\orchestrator.py" `
  --workspace "D:\NEW_CLINICIAN_CASES" `
  --init-workspace `
  --clinician-name "Dr. Jane Doe" `
  --series-name "Internal Medicine Bedside Vignettes"
```

### Standardized 12-Directory Architecture Created:
```
<workspace>/
├── 00_CONTROL/               <-- Control registries (manifest, provenance ledger, capture tracker, claim & normalized schemas)
├── 01_RAW_SINGLEFILE/        <-- Immutable SingleFile HTML captures organized into per-record folders (<rec_id>__FULL.html)
├── 02_RAW_MEDIA/             <-- Decoupled clinical media store (ECGs, X-rays, case photos, flowcharts, image_catalog.csv)
├── 03_NORMALIZED_CORPUS/     <-- Clean extracted objects:
│   ├── POSTS/                <-- Normalized post JSONs
│   ├── COMMENTS/             <-- Verified clinical comment JSONs
│   ├── REPLIES/              <-- Verified clinical reply JSONs
│   ├── MEDIA_METADATA/       <-- Media catalog with SHA-256 digests
│   ├── THREADS/              <-- Hierarchical thread tree JSONs
│   ├── MARKDOWN/             <-- Clean clinical markdown documentation
│   ├── JSON/                 <-- Consolidated record archives
│   ├── TABLES/               <-- Clinical claims, topic indices, causal graph triplets, curriculum tiers
│   ├── CLINICAL_COMMENTS/    <-- Filtered high-yield discussion items
│   └── ENGLISH_SYNTHESIS/    <-- Structured English clinical translations
├── 04_PERSONA/               <-- Teaching profile, heuristics, analogies, corrections, and language patterns
├── 05_TEXTBOOK_BRIDGE/       <-- Bidirectional links to Davidson 25th Edition and international guidelines
├── 06_DIAGNOSTICS/           <-- Fail-closed audit dossiers for missing captures (MANUAL_REVIEW/)
├── 07_AUDIT/                 <-- Authorship, completeness, media SHA-256, and master corpus audit summaries
├── 08_EXPORTS/               <-- Production CDSS RAG JSONL, clinical claims, and extended educational suites:
│   ├── RAG/                  <-- habijabi_english_cdss.jsonl, habijabi_kawsar_cdss.jsonl
│   ├── OSCE/                 <-- visual_spotters.jsonl
│   ├── CURRICULUM/           <-- residency_progression_guide.md
│   ├── GRAPH/                <-- causal_knowledge_graph.jsonl
│   ├── SBAR_HANDOVERS/       <-- ward_sbar_handover_cards.md / .jsonl
│   ├── PATIENT_LEAFLETS/     <-- patient_counseling_leaflets_bengali.md
│   ├── ANKI/                 <-- habijabi_high_yield_anki_deck.tsv
│   └── PHARMACOVIGILANCE/    <-- never_events_toxic_drug_matrix.csv / .md
├── 99_BACKUP/                <-- Safety backups with SHA-256 manifests prior to any write/pruning operations
├── raw html/                 <-- Drop zone for incoming SingleFile HTML files
└── tools/                    <-- Local mirror scripts and helper runners
```

---

## 🚀 2. Autonomous Manufacturing Pipeline (`--pipeline`)

Once SingleFile HTML files are dropped into `<workspace>\raw html\`, execute the complete automated manufacturing line with a single command:

```powershell
python "C:\Users\User\.gemini\config\skills\clinical-preceptor-cdss-orchestrator\scripts\orchestrator.py" `
  --workspace "D:\HABIJABI_FULL" `
  --pipeline auto
```

### Automated Stages Executed:
1. **Stage 1 (Inbound & Preflight)**: Resolves permalinks, matches titles/hashtags, and logs missing/duplicate files.
2. **Stage 2 (Deterministic Extraction)**: Extracts body text, reactions, and decodes base64 clinical media into `02_RAW_MEDIA/`.
3. **Stage 3 (Semantic Noise Pruning)**: Deletes redundant social chatter (*"thanks"*, *"nice post"*, emojis), preserving only substantive clinical questions, differential discussions, and author teaching.
4. **Stage 4 (English Clinical Synthesis)**: Generates structured English medical documentation for each record (vignette, cellular pathophysiology, diagnostic algorithm, therapeutic protocol, prescribing contraindications, and clinical pearls).
5. **Stage 5 (Claims & Heuristics)**: Extracts discrete clinical claims with non-evaluated validity status (`NOT_ASSESSED`).
6. **Stage 6 (Textbook Bridging)**: Maps records to corresponding textbook chapters (*Davidson 25th Edition*, *Harrison 22nd Edition*).
7. **Stage 7 (Extended Modalities)**: Auto-manufactures OSCE visual spotters, curriculum tiers, GraphRAG causal triplets, SBAR handover cards, Bengali patient leaflets, Anki decks, and toxic drug matrices.
8. **Stage 8 (CDSS RAG & Audits)**: Compiles semantic retrieval chunks and executes authorship and media SHA-256 audits.

---

## 🩺 3. The 13 Full-Spectrum Clinical Runtime Modalities

### Core 6 Modalities:
1. **Interactive Socratic Ward Preceptor (`--preceptor <query>`)**:
   Simulates morning report / ward rounds, decomposing patient cases into mechanisms-first reasoning:
   ```powershell
   python ...\orchestrator.py --workspace "D:\HABIJABI_FULL" --preceptor "Young 20yo male with severe HTN and hypokalemia"
   ```

2. **Postgraduate Exam SBA Generator (`--exam-sba [record_id|random]`)**:
   Generates Single Best Answer (SBA) questions for **FCPS Part 1, MRCP UK, MD Residency** with dual citations:
   ```powershell
   python ...\orchestrator.py --workspace "D:\HABIJABI_FULL" --exam-sba "HABIJABI-003"
   ```

3. **Bedside Prescribing Safety Interceptor (`--prescribing-safety <query>`)**:
   Intercepts dangerous defensive prescribing traps (e.g. allopurinol during acute gout, blind fluids in dengue):
   ```powershell
   python ...\orchestrator.py --workspace "D:\HABIJABI_FULL" --prescribing-safety "Acute gout: start allopurinol"
   ```

4. **Federated 4-Textbook Cross-Grounding (`--federated <topic>`)**:
   Cross-references bedside teaching against *Davidson 25*, *Harrison 22*, *Hurst 15*, and *Kumar & Clark 11*:
   ```powershell
   python ...\orchestrator.py --workspace "D:\HABIJABI_FULL" --federated "Mitral stenosis"
   ```

5. **Tropical & Resource-Constrained Ward Companion (`--tropical-calc`, `--ward-facilities`)**:
   Gravity IV drop calculators, dengue fluid deficit formulas, Mentzer index, and Dhaka laboratory routing:
   ```powershell
   python ...\orchestrator.py --workspace "D:\HABIJABI_FULL" --tropical-calc dengue --calc-args 55
   python ...\orchestrator.py --workspace "D:\HABIJABI_FULL" --ward-facilities "Aldosterone Renin Ratio"
   ```

6. **Hybrid Bilingual Semantic Retrieval Engine (`--search <query>`)**:
   Sub-millisecond hybrid search across verbatim Bengali, English synthesis, and filtered clinical discussions:
   ```powershell
   python ...\orchestrator.py --workspace "D:\HABIJABI_FULL" --search "Thalassemia hemosiderosis" --lang en
   ```

---

### Extended 7 Modalities:
7. **Clinical OSCE Visual Spotter Stations (`--visual-spotter [station_id|query|random]`)**:
   Displays decoupled clinical media (ECGs, blood films, clinical photos) with 3-part OSCE questions and answer keys:
   ```powershell
   python ...\orchestrator.py --workspace "D:\HABIJABI_FULL" --visual-spotter "HABIJABI-001"
   ```

8. **Residency Progression Curriculum (`--curriculum [tier1|tier2|tier3|all]`)**:
   Filters and browses cases stratified by training milestone:
   - **Tier 1 (Intern / House Officer)**: Emergency triage, fluid drop arithmetic, routine panels.
   - **Tier 2 (Medical Officer / GP)**: Acute flares, outpatient pitfalls, safe polypharmacy.
   - **Tier 3 (Postgraduate / FCPS / MRCP)**: Rare channelopathies, syndromic differentials, high-risk pharmacology.
   ```powershell
   python ...\orchestrator.py --workspace "D:\HABIJABI_FULL" --curriculum tier1
   ```

9. **GraphRAG Pathophysiological Causal Knowledge Graph (`--causal-graph [query|all]`)**:
   Navigates structured causal triplets `(Subject) -[PREDICATE]-> (Object)` to inspect biochemical logic:
   ```powershell
   python ...\orchestrator.py --workspace "D:\HABIJABI_FULL" --causal-graph "Liddle"
   ```

10. **Acute On-Call Ward SBAR Handover Cards (`--sbar [condition|all]`)**:
    Generates standardized Situation-Background-Assessment-Recommendation cards for night-duty handovers:
    ```powershell
    python ...\orchestrator.py --workspace "D:\HABIJABI_FULL" --sbar "Dengue"
    ```

11. **Patient Health Literacy & Folk Counseling Leaflets (`--patient-leaflet [query|all]`)**:
    Outputs patient-facing counseling sheets in colloquial Bengali using Dr. Kawsar's documented allegories:
    ```powershell
    python ...\orchestrator.py --workspace "D:\HABIJABI_FULL" --patient-leaflet "বকুল"
    ```

12. **High-Yield Anki Spaced-Repetition Cloze Decks (`--anki-deck [query|all]`)**:
    Previews and exports high-yield Anki flashcard decks with cloze deletions ready for exam cramming:
    ```powershell
    python ...\orchestrator.py --workspace "D:\HABIJABI_FULL" --anki-deck "Linezolid"
    ```

13. **Ward Pharmacovigilance & "Never-Events" Toxic Drug Matrix (`--never-events [drug|all]`)**:
    A pocket clinical safety reference documenting lethal combinations, pathophysiology, and safe alternatives:
    ```powershell
    python ...\orchestrator.py --workspace "D:\HABIJABI_FULL" --never-events "Linezolid"
    ```

---

## 🔒 4. Clinical Governance & Fail-Closed Guardrails

1. **Non-Overriding Precept**: Clinical preceptor teachings provide historical, pedagogical, and bedside heuristic models; they **never** override current authoritative clinical evidence or institutional guidelines.
2. **Temporal Awareness**: Pandemic-era empirical therapies (e.g. spring/summer 2020 COVID-19 regimens) carry mandatory `HISTORICAL_ONLY` provenance tags and are never recommended for active clinical care.
3. **Evidence Class Segregation**: The engine maintains absolute separation between authoritative textbooks (Class A), clinician teaching (Class B), clinician persona/heuristics (Class C), peer learner discussions (Class D), and model translations (Class E).
4. **Pre-Prune Backup Policy**: Any write or pruning operation automatically requires a complete pre-pruning safety backup with a verified SHA-256 manifest in `99_BACKUP/`.
