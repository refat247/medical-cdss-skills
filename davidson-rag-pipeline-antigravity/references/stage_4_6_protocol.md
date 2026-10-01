# Stage 4.6 — Semantic Type Verification & Triage Protocol

## Purpose
Stage 4.6 enforces rigorous semantic categorization across all emitted L2 chunks to ensure accurate retrieval routing for downstream clinical RAG systems.

## Permitted Semantic Types
- `drug_info`: Dosage, pharmacokinetics, adverse drug reactions, contraindications, drug interactions.
- `laboratory_investigation`: Diagnostic tests, blood work, ECG, imaging modalities, biopsy, biomarkers.
- `management_step`: Treatment plans, surgical interventions, lifestyle modifications, emergency resuscitation, clinical pathways.
- `clinical_feature`: Symptoms, signs, clinical presentations, physical examination findings, natural history.
- `diagnostic_criteria`: Formal scoring systems (e.g. NYHA, Duke, CURB-65), diagnostic algorithms, diagnostic thresholds.
- `pathophysiology`: Disease etiology, cellular mechanisms, anatomical anomalies, pathological progression.
- `epidemiology_concept`: Prevalence, incidence, risk demographics, global burden, prognostics.

## In-Session Manual Review Protocol (When Triage is Flagged or Degraded)

1. **Parse & Filter L2 Chunks**:
   ```python
   from pipeline.stage_4_6_gemini_verification import (
       _split_chunks, _get_chunk_level, _get_semantic_type,
       _get_topic, _get_body, _flag_review_priority
   )

   chunks_data = open(chunk_path, encoding='utf-8').read()
   parts = _split_chunks(chunks_data)
   l2_chunks = [p for p in parts if _get_chunk_level(p) == 2]
   ```

2. **Evaluate & Adjudicate All L2 Chunks**:
   - Inspect each L2 chunk's topic, current semantic type, and body.
   - Helper signature: `_flag_review_priority(topic, body, current_type)` (3 positional args — `topic` first).
   - Apply clinical adjudication heuristics (title beats body keywords).
   - Build a list/dict of corrections:
     ```python
     corrections = [
         ("L2-014", topic, "clinical_feature", "drug_info"),
         ("L2-088", topic, "clinical_feature", "laboratory_investigation")
     ]
     ```

3. **Apply Corrections, Provenance Header & Finalize Checkpoint**:
   - Update frontmatter `semantic_type: <new_type>` in place in `chunks.md`.
   - Write `{PREFIX}_Remap_Log.md` with provenance header (`format_markdown_provenance_header(source_path, "4.6")`).
   - Call `mark_stage_complete(checkpoint, checkpoint_path, "4.6", output_file=f"{PREFIX}_Remap_Log.md", **decision_metadata)`.
   - Re-run `--stage auto` to continue.

## Section-Header Adjudication Heuristics (Title beats body keywords)

- **`pathophysiology`**: Anatomy/physiology, lung mechanics, control of breathing, V/Q matching, airway defences, Aetiology, Pathology and pathogenesis, `Causes of ...` tables.
- **`laboratory_investigation`**: All imaging modalities and radiological signs (shadowing, translucency, hilar abnormalities), endoscopy (bronchoscopy, thoracoscopy, EBUS), cytology/histopathology, microbiology/serology, function tests, blood gases, lab specimens (FBC, U&E, LFTs, CRP, cultures, pleural fluid), `Investigations`.
- **`management_step`**: Management/Treatment/Therapy, ventilation and oxygen therapy, rehabilitation, physiotherapy, surgery, Prevention, Discharge/follow-up, antibiotic-regimen tables, `Indications for ...` (transplant, assisted ventilation, ICU referral).
- **`drug_info`**: Adverse-reaction tables, drug-resistance sections, `Drugs` as a cause of disease.
- **`diagnostic_criteria`**: Named criteria/scores/indices (Light's criteria, BODE index, CURB-65), diagnostic algorithms/thresholds, `Diagnosis`.
- **`epidemiology_concept`**: Epidemiology, `Risk factors for ...` / predisposing-factor tables, Prognosis, disease in old age/adolescence.
- **`clinical_feature`**: Disease-overview headers, symptom/feature tables, examination / clinical-assessment sections, MCQ vignettes.

*Watch-outs*:
- 'Cytology and histopathology' is `laboratory_investigation` (not pathophysiology).
- 'Non-invasive ventilation' is `management_step` (not pathophysiology).
- `Features suggesting ...` is `clinical_feature` even when the topic mentions a mechanism.

## Headless / No-API Environments & Completeness Rule (v2.6.5)

In sandboxes or cloud containers where `GEMINI_API_KEY` is unavailable, `stage_4_with_verification()` returns `needs_manual_verification: True` and pauses as `pending_manual`.
- **Completeness Rule (v2.6.5)**: To achieve `action="complete"`, `chunks_reviewed` must be $\ge$ `total_flagged`. Always set `chunks_reviewed` and `total_flagged` to the total L2 count.
- When calling `mark_stage_complete()`, pass `**decision_metadata` directly without duplicating explicit kwargs (`chunks_reviewed`, `total_flagged`) to prevent keyword argument collisions.