# CDSS Master Architectural Decisions & Visual Conversion Standards

This document establishes the permanent architectural foundations, visual conversion standards, and medical meaning preservation guarantees for the Davidson RAG Pipeline in downstream Clinical Decision Support Systems (CDSS).

---

## 1. The 5-Archetype Medical Visual Conversion Standard

Every figure in Davidson 25th Edition falls into one of five distinct clinical archetypes. Each archetype is handled with a dedicated conversion protocol to guarantee maximum retrieval accuracy, sub-350ms point-of-care latency, and zero token waste.

```
                                  [All Medical Textbook Figures]
                                                │
         ┌───────────────┬──────────────────────┼──────────────────────┬───────────────┐
         ▼               ▼                      ▼                      ▼               ▼
   [Archetype 1]   [Archetype 2]          [Archetype 3]          [Archetype 4]   [Archetype 5]
    Decision &      Data Tables &          Physiological          Procedural &    Perceptual
    Flowcharts      Matrices               Cascades               Anatomical      Morphology
    (Algorithms)    (Drug/Score grids)     (RAAS / Coagulation)   Techniques      (ECG/X-ray/Rash)
         │               │                      │                      │               │
         ▼               ▼                      ▼                      ▼               ▼
    [100% Text]     [100% Text]            [100% Text]            [100% Text]     [Hybrid Strategy]
    IF ➔ THEN       Markdown Tables        Sequential Chains      Stepwise Rules  Structured Criteria (AI)
    Logic Rules     & JSON Schemas         & Bio-mechanisms       & Landmarks     + Visual Link (Doctor)
```

### Archetype 1: Clinical Flowcharts & Decision Trees
* **Examples**: Acute asthma emergency escalation, jaundice workup, chest pain triage algorithms.
* **Conversion Rule**: Transcribe 100% into structured Markdown conditional logic ($IF \to THEN \to ELSE$) or Stepwise rules.
* **Metadata Classification**: `is_clinical_algorithm: true`, `algorithm_type: "decision_tree" | "stepwise_escalation"`.
* **CDSS Rationale**: Text-based decision rules can be deterministically parsed and executed by CDSS clinical pathway engines in <200 tokens without vision model overhead.

### Archetype 2: Graphic Tables & Scoring Matrices
* **Examples**: CURB-65 pneumonia severity score, Wells criteria for PE, Child-Pugh liver staging, NYHA functional classes.
* **Conversion Rule**: Transcribe 100% into standard Markdown tables (`| Variable | Criteria | Points |`) with explicit point thresholds.
* **Metadata Classification**: `is_clinical_algorithm: true`, `algorithm_type: "scoring_system"`, `contains_tables: true`.
* **CDSS Rationale**: Enables structured EHR risk calculator integration and instant numerical threshold matching.

### Archetype 3: Biological Pathways & Mechanism Cascades
* **Examples**: Renin-Angiotensin-Aldosterone System (RAAS), Coagulation cascade, Cardiac action potential phases.
* **Conversion Rule**: Transcribe 100% into numbered sequential causal chains (Trigger $\to$ Secretion $\to$ Conversion $\to$ Physiological Response).
* **Metadata Classification**: `semantic_type: "pathophysiology"`.
* **CDSS Rationale**: Preserves complete causal logic required for deep biomedical reasoning and pharmacological mechanism queries.

### Archetype 4: Procedural Protocols & Anatomical Landmarks
* **Examples**: Pleural aspiration needle trajectory (above superior border of lower rib), Lumbar puncture needle angle.
* **Conversion Rule**: Transcribe 100% into numbered procedural instructions with explicit anatomical landmark safety warnings.
* **Metadata Classification**: `semantic_type: "management_step" | "laboratory_investigation"`, `algorithm_type: "stepwise_escalation"`.
* **CDSS Rationale**: Guarantees zero missed safety contraindications during invasive point-of-care procedures.

### Archetype 5: Perceptual Morphology & Waveforms (ECGs, X-rays, Rashes, Biopsies)
* **Examples**: 12-lead ECG in acute STEMI / pericarditis, Chest X-ray lobar consolidation, Erythema chronicum migrans rash photo.
* **Conversion Rule (Decoupled Multi-Modal Invariant - Rule R)**:
  1. **For AI Vector Search**: Transcribe 100% of diagnostic criteria and visual hallmarks into the text chunk.
  2. **For Human Clinician Confirmation**: Store high-resolution image in `assets/figures/` (or CDN) and attach URI pointer in frontmatter (`figure_assets: ["assets/figures/ch18_fig_04.png"]`, `figure_captions: [...]`).
* **CDSS Rationale**: Prevents $2,000+$ vision tokens per query and eliminates point-of-care latency while providing the clinician with instant visual evidence on the UI sidebar.

---

## 2. The 5 Meaning Preservation Pillars (Deterministic Code Slicing)

The pipeline rejects naive character-splitting in favor of an Abstract Syntax Tree (AST) parser governed by 5 pillars:

1. **Rule P (Parent Disease Slug Inheritance)**: Every micro-chunk deterministically inherits its parent disease focus (`disease_focus: "asthma"`, `topic: "Asthma — Management"`), preventing orphan sub-headings.
2. **Stage 5.4 (Relational Graph Auto-Linking)**: Builds a bidirectional graph linking presentation, diagnostics, and management chunks (`related_chunks: ["L2-045", "L2-046"]`).
3. **Rule Q & J (Overview & Flat Section Capture)**: Captures intro prose into `Overview` chunks and parses deep `####` subsections without dropping a word.
4. **Stage 4.6 (7-Type Semantic Routing Taxonomy)**: Enforces strict classification (`drug_info`, `laboratory_investigation`, `management_step`, `clinical_feature`, `diagnostic_criteria`, `pathophysiology`, `epidemiology_concept`) for hard vector DB pre-filtering.
5. **Stage 4.7 / 5.2 (Clinical Completeness Synthesis)**: Detects scattered disease mentions across chapters and synthesizes unified Tier 2 overview chunks.

---

## 3. Zero-Token Deterministic Execution & Hard-Fail Quality Gates

* **Zero-Token Local Execution**: Stages 0 through 8 execute on the local Python runtime with **0 LLM tokens**.
* **Hard-Won Rule D (Verbatim Splice-Fixing)**: LLMs are strictly forbidden from rewriting chunk text. All repairs are exact byte-copies from `REPAIRED_S2.md`.
* **Blocking Gates**:
  * **Stage 4.5**: Byte-for-byte exact spot check against source text.
  * **Stage 4.5c**: Blocking source-span coverage gate (0 dropped bytes allowed).
  * **Stage 4.5d**: 11-pattern clinical anomaly audit (drug doses, inequalities, units, negations).
  * **Stage 6 (Invariant 6.5)**: Validates frontmatter completeness for figures and clinical algorithms.
  * **Stage 8**: Computes exact `source_lines` provenance for 100% clinician audit trails.
