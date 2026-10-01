---
name: kumar-cdss-navigator
version: 1.0.1
description: |
  Autonomous Clinical Decision Support System (CDSS) and zero-token precision index retrieval navigator for
  Kumar and Clark's Clinical Medicine (11th Edition 2026). Use when querying Kumar & Clark as a single standalone book
  (for multi-book federated queries across all textbooks, use medical-cdss-unified-orchestrator).
  Provides multi-turn clinical QA, case vignette decomposition, and 120-word span compression across 9,394 chunks.
---

# Kumar & Clark CDSS Navigator (v1.0.1)

Production-grade Clinical Decision Support System and Index Retrieval Engine grounded directly in the 11th Edition of *Kumar and Clark's Clinical Medicine (2026)* (50 clinical chapters, 9,394 L2 micro-chunks, 1,803 visual figure assets, and 33,454 indexed vocabulary terms).

> [!IMPORTANT]
> **Zero-Hallucination & Provenance Guarantee**:
> All medical acronyms, clinical classifications, drug indications, and concept hierarchies are strictly derived from the 50 parsed chapters and synthesized index of Kumar and Clark's 11th Edition. Every recommendation is traceable to concrete textbook chunks, chapters, and cited page numbers.

---

## 🎯 When to Activate This Skill

Activate this skill automatically whenever:
- The user or physician asks an **evidence-based clinical question**, disease overview, or diagnostic inquiry intended specifically for *Kumar and Clark's Clinical Medicine*.
- Solving or analyzing **clinical case vignettes** (e.g. FCPS Part 1/2, USMLE Step 2/3, MRCP PACES/Part 1/2, or internal medicine residency exams).
- Resolving **differential diagnoses and look-alikes** in clinical medicine.
- Validating **drug therapy indications, contraindications, or safety** across medical specialties.
- Requiring **token-efficient prompt checklists** (`--outline`) or **span-compressed micro-windows** (`--compress`).
- The user asks to query **Kumar & Clark as a single standalone book** rather than federated cross-book retrieval.

---

## 💻 Engine CLI Quick-Start

The dedicated navigator CLI runner is located at `scripts/navigator.py`:

```powershell
python "C:\Users\User\.gemini\config\skills\kumar-cdss-navigator\scripts\navigator.py" [OPTIONS]
```

### 1. Complex Clinical Case Vignette Decomposition
Decompose multi-sentence patient presentations with clinical vitals, lab findings, and symptoms:
```powershell
python "C:\Users\User\.gemini\config\skills\kumar-cdss-navigator\scripts\navigator.py" `
  --vignette "54-year-old female presents with acute jaundice, right upper quadrant pain, and fever with rigors. Bilirubin is elevated and ultrasound shows dilated common bile duct."
```

### 2. Extractive Span-Compressed Retrieval (-80% Token Cost)
Extracts targeted 120-word clinical windows directly surrounding the query terms:
```powershell
python "C:\Users\User\.gemini\config\skills\kumar-cdss-navigator\scripts\navigator.py" `
  --query "Atrial fibrillation anticoagulation" `
  --compress
```

### 3. Prompt-Ready Medical Outline Checklist
Fetches structured concept hierarchy and subfacets from the textbook's back-of-the-book index:
```powershell
python "C:\Users\User\.gemini\config\skills\kumar-cdss-navigator\scripts\navigator.py" `
  --outline "Acute coronary syndromes"
```

### 4. Machine-Readable JSON Output
Integrate directly with external tools and automated evaluation pipelines:
```powershell
python "C:\Users\User\.gemini\config\skills\kumar-cdss-navigator\scripts\navigator.py" `
  --query "Diabetic ketoacidosis management" `
  --json
```

### 5. Therapy Safety Guardrail
Validates drug indications, safety precautions, and electrolyte monitoring:
```powershell
python "C:\Users\User\.gemini\config\skills\kumar-cdss-navigator\scripts\navigator.py" `
  --validate-therapy "Sacubitril" "heart failure"
```

### 6. Differential Diagnosis & "Vs." Comparator
Extracts differential entries and distinguishing criteria:
```powershell
python "C:\Users\User\.gemini\config\skills\kumar-cdss-navigator\scripts\navigator.py" `
  --diff "Conjunctivitis"
```

---

## 🏛️ Knowledge Architecture Reference

The navigator operates directly over Kumar & Clark's **23 production CDSS assets** in `04_Kumar_and_Clark_11/Index/`:
- `kumar_clark_chunks_master_catalog.json`: 9,394 discrete L2 clinical micro-chunks.
- `kumar_clark_inverted_chunk_index.json`: 33,454 indexed vocabulary terms with BM25 inverted postings.
- `kumar_clark_early_exit_section_index.json`: Sub-millisecond hierarchical routing anchors (< 2 ms latency).
- `kumar_clark_canonical_semantic_cache.json`: Pre-computed canonical intent cache (0 ms latency).
- `kumar_clark_polysemy_disambiguation.json`: Multi-meaning medical term disambiguation resolver.
- `kumar_clark_concept_subtrees.json`: Prompt-ready medical checklists and concept hierarchies.
- `kumar_clark_entity_grammar.gbnf`: Formal GBNF grammar for zero-hallucination constrained decoding.
- `kumar_clark_typographical_anchors.json`: Typographical table, box, and figure anchors.
- `kumar_clark_clinical_cooccurrence_graph.json`: Syndromic co-occurrence edges across clinical specialties.
- `kumar_clark_drug_disease_safety_matrix.json`: Drug safety precautions and clinical indications.
- `cdss_qa_router.py`: Production-grade CDSS execution engine.
- `BENCHMARK_SCORECARD.md`: Hard-negative retrieval benchmark report.

---

## 📋 CDSS Execution Protocol for AI Agents

When acting as a medical assistant or answering clinical queries:
1. **Analyze Clinical Intent**:
   - Patient case vignette $\longrightarrow$ Use `--vignette`.
   - Disease overview / clinical checklist $\longrightarrow$ Use `--outline` first, then retrieve specific evidence chunks with `--compress`.
   - Differential diagnosis $\longrightarrow$ Use `--diff`.
   - Drug therapy / prescribing $\longrightarrow$ Use `--validate-therapy`.
2. **Inject Compressed Micro-Spans**: Never dump thousands of tokens of raw prose into conversation context. Use `--compress` to inject targeted 120-word evidence excerpts.
3. **Always Cite Textbook Coordinates**: Always cite the Chapter Base, Topic, Chunk ID (`[L2-XXX]`), and Page numbers.

## Package Location (2026-09-25)
- Set `CDSS_PACKAGE_DIR` to override the default package path.
- The navigator exits 1 when the router is missing.
- A fallback to an unpackaged build router is announced with `[WARN]` on stderr.
