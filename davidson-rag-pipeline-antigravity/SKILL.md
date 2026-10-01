---
name: davidson-rag-pipeline-antigravity
version: 2.25.1
description: |
  Full 18-stage RAG pipeline for Davidson 25th Edition chapters and clinical practice guidelines (ADA, KDIGO, ESC, NICE),
  optimised for Google Antigravity local Windows sessions and Google Gemini 3.7 Flash High model.
  Direct filesystem access, no cowork sandbox, no bash VM. Takes one markdown_inlined.md
  and produces REPAIRED_S2, chunks, and RAG_Optimised outputs. Features a slim progressive-disclosure
  hub architecture, automated pipeline chaining (--stage auto), deterministic hybrid code-slicing parser (Stage 4B),
  exhaustive verbatim spot-check, blocking source-span coverage gate (Stage 4.5c), clinical fidelity gate (Stage 4.5d),
  semantic type remap (Stage 4.6), completeness checklist (Stage 4.7/5.2), dual-format precision synchronization (Stage 8),
  hard-fail validation gate (Stage 6), fail-closed finalization, and Rule T-V proof disciplines.
---

# Davidson RAG Pipeline — Antigravity & Gemini Edition (v2.25.1)

Production RAG extraction pipeline optimized for direct Windows filesystem execution.
Features a modular Hub-and-Spoke progressive disclosure architecture with automated CLI stage chaining.

---

## Pareto-Optimal Token & Accuracy Protocol

1. **Zero-Token Local Execution**: Stages 0 through 8 execute purely on local Python runtime via `pipeline.run_stage` with **0 LLM token cost**.
2. **Automated Chaining by Default**: Run `--stage auto` to execute all consecutive deterministic stages continuously, pausing only when interactive candidate triage is required.
3. **Just-in-Time (JIT) Reference Loading**: Do not read `references/` upfront. Only view a protocol file when a stage triggers `pending_manual` or `priority_review`.
4. **25-Item Review Batches**: Always inspect exported batch review files (`fidelity_review_batch_NN.md`) for candidate triage; never dump 500-chunk files into context.
5. **Verbatim Splice-Fixing (Rule D/F)**: Correct anomalies by splicing exact text from `REPAIRED_S2.md` directly into `chunks.md`. Never regenerate prose with LLMs.

---

## Environment & Execution Rules

- Use `python` (not `python3`).
- UTF-8 console streams enforced across all stages (`io.TextIOWrapper`).
- Never trust stdout alone for gating: inspect generated `.md` and `.json` log files.
- All stage commands are executed via the unified CLI dispatcher `pipeline.run_stage`.

> [!IMPORTANT]
> **Output Location & Provenance Rules**:
> 1. **Output Location**: All RAG pipeline outputs (`REPAIRED_S2.md`, `chunks.md`, `RAG_Optimised.md`, `_CHECKPOINT.json`, gates, and scorecards) MUST ALWAYS be saved in a dedicated `rag_pipeline_output` subfolder under the source chapter directory:
>    `<SOURCE_DIR>\rag_pipeline_output\`
>    (e.g. `D:\davidson_25_true\TRUE_MD_WITH_IMAGES\Davidson_25_05_Nutritional factors in disease.pdf\rag_pipeline_output`)
> 2. **Mandatory Provenance Metadata**: Every markdown output (`REPAIRED_S2.md`, `chunks.md`, `RAG_Optimised.md`, report `.md` files) MUST embed a top-level HTML comment provenance block:
>    ```markdown
>    <!--
>    PROVENANCE METADATA:
>      skill_name: "davidson-rag-pipeline-antigravity"
>      skill_version: "2.25.1"
>      generated_at: "YYYY-MM-DDTHH:MM:SSZ"
>      source_path: "<PATH>"
>    -->
>    ```
>    All JSON reports and scorecards MUST attach a top-level `_provenance` dictionary with the same metadata fields.


---

## Primary Execution: Automated Pipeline Chaining

Run the entire pipeline continuously until completion or until an interactive gate pause (if `--out` is omitted, it automatically defaults to `<SOURCE_DIR>\rag_pipeline_output`):
```bash
python -m pipeline.run_stage --stage auto --source "<SOURCE_PATH>" --out "<SOURCE_DIR>\rag_pipeline_output"
```
- If Stage 4.5d or 4.6 pauses with `pending_manual`, follow the on-demand reference protocol to adjudicate candidates, apply decisions, and re-run `--stage auto` to resume seamlessly.

---

## Step 0 — Parse Inputs & Derive Identifiers

Identify source paths before beginning:
- `SOURCE_PATH`: Full absolute path to `markdown_inlined.md` (e.g. `r"D:\davidson_25_true\TRUE_MD_WITH_IMAGES\Davidson_25_05_Nutritional factors in disease.pdf\Davidson_25_05_Nutritional_factors_in_disease.pdf.markdown_inlined.md"`)
- `OUTPUT_DIR`: Dedicated subfolder named `rag_pipeline_output` under the source directory (e.g. `r"D:\davidson_25_true\TRUE_MD_WITH_IMAGES\Davidson_25_05_Nutritional factors in disease.pdf\rag_pipeline_output"`)

Derivation helper:
```python
import re, os
source = r"<SOURCE_PATH>"
out_dir = os.path.join(os.path.dirname(os.path.abspath(source)), "rag_pipeline_output")
m = re.search(r'Davidson_25_(\d+)_(.+?)\.pdf', source) or re.search(r'Davidson_25_Ch(\d+)_(.+?)(?:_|$|\.)', os.path.basename(source))
CH_NUM = m.group(1) if m else "??"
CH_SLUG = m.group(2).replace(' ', '_') if m else "Unknown"
CH_DISPLAY = m.group(2).replace('_', ' ') if m else "Unknown"
PREFIX = f"Davidson_25_Ch{CH_NUM}_{CH_SLUG}"
os.makedirs(out_dir, exist_ok=True)
print(f"Chapter: Ch{CH_NUM} | {CH_DISPLAY} | PREFIX: {PREFIX} | OUT: {out_dir}")
```

---

## Individual Stage Runners (Manual / Debug Mode)

### Stage 1 — Forensic Audit
Audits structural integrity, table rows, image links, duplicate paragraphs, and piracy watermark patterns.
```bash
python -m pipeline.run_stage --stage 1 --source "<SOURCE_PATH>" --out "<OUTPUT_DIR>"
```
- **Review**: Read `{PREFIX}_AUDIT_REPORT.md`.
- **Verdict**: If `production_safe`, Stage 2 may pass through. Otherwise, Stage 2 is **REQUIRED**.

---

### Stage 2 — Autonomous Repair
Repairs formatting anomalies, cleans header artifacts, and strips piracy markers while preserving clinical MCQs.
```bash
python -m pipeline.run_stage --stage 2 --source "<SOURCE_PATH>" --out "<OUTPUT_DIR>"
```
- **Output**: `{PREFIX}_REPAIRED_S2.md` and `{PREFIX}_Corrections_Log.md`.

---

### Stage 3 — Post-Repair Re-Audit
Computes $O(N)$ tokenized diff comparison between original source and repaired output.
```bash
python -m pipeline.run_stage --stage 3 --source "<SOURCE_PATH>" --out "<OUTPUT_DIR>"
```
- **Gate**: `PASSED` -> proceed to Stage 4. `ISSUES` -> checkpoint blocks until issues are rectified.

---

### Stage 4 — Structure Parsing & Hybrid Slicer Engine

#### 4A: Pre-Flight Heading-Depth Manifest
Generates heading hierarchy and depth strategy manifest (Rule J3):
```bash
python -m pipeline.run_stage --stage 4a --source "<SOURCE_PATH>" --out "<OUTPUT_DIR>"
```

#### 4B: Deterministic Hybrid Slicer Engine
Slices byte-verbatim L1 container sections and L2 micro chunks with parent disease slug inheritance (Rule P):
```bash
python -m pipeline.run_stage --stage 4b --source "<SOURCE_PATH>" --out "<OUTPUT_DIR>"
```
- **Output**: `{PREFIX}_chunks.md`.

---

### Stage 4.5 — Exhaustive Verbatim Spot-Check
Verifies 100% of emitted L2 chunks against `REPAIRED_S2.md` and validates figure parity:
```bash
python -m pipeline.run_stage --stage 4.5 --source "<SOURCE_PATH>" --out "<OUTPUT_DIR>"
```
- **Gate**: `CLEARED` -> proceed. `FAIL` -> splice-fix failed chunks from `REPAIRED_S2.md`.

---

### Stage 4.5c — L1/L2 Source-Span Coverage Gate (BLOCKING)
Detects any un-chunked spans between L1 container sections and child L2 chunks:
```bash
python -m pipeline.run_stage --stage 4.5c --source "<SOURCE_PATH>" --out "<OUTPUT_DIR>"
```
- **Gate**: **BLOCKING**. If gaps are found, splice-fix verbatim spans per Rule D before proceeding.

---

### Stage 4.5d — Clinical Fidelity Gate (BLOCKING)
Scans 11 pattern detectors (dosing, units, inequalities, negations, sequence order) for semantic corruption:
```bash
python -m pipeline.run_stage --stage 4.5d --source "<SOURCE_PATH>" --out "<OUTPUT_DIR>"
```
- **Action `pending_manual`**: 👉 **MANDATORY**: Read [`references/stage_4_5d_protocol.md`](references/stage_4_5d_protocol.md) to adjudicate candidates before completing this stage.

---

### Stage 4.5b — Clinical Flag Coverage (Pharma Scan)
Checks dosing and clinical threshold retention on pharmacology-heavy chapters:
```bash
python -m pipeline.run_stage --stage 4.5b --source "<SOURCE_PATH>" --out "<OUTPUT_DIR>"
```

---

### Stage 4.6 — Semantic Type Verification
Enforces retrieval routing classification (`drug_info`, `clinical_feature`, `management_step`, etc.):
```bash
python -m pipeline.run_stage --stage 4.6 --source "<SOURCE_PATH>" --out "<OUTPUT_DIR>"
```
By default, Stage 4.6 executes zero-token offline deterministic clinical adjudication (`offline_adjudicate_all`).
Opt-in external LLM API verification is available via `--use-llm` when `GEMINI_API_KEY` is configured.
- **Action `pending_manual`**: If `--use-llm` is used without an API key or candidate review is needed, read [`references/stage_4_6_protocol.md`](references/stage_4_6_protocol.md) for batch triage instructions.

---

### Stage 4.7 & 5.2 — Clinical Completeness Gate & Synthesis
Evaluates multi-category disease coverage across causes, presentation, investigation, treatment, and safety:
```bash
python -m pipeline.run_stage --stage 4.7 --source "<SOURCE_PATH>" --out "<OUTPUT_DIR>"
```
- If `SCATTERED` disease clusters require Tier 2 synthesis:
  👉 **MANDATORY**: Follow [`references/stage_4_7_protocol.md`](references/stage_4_7_protocol.md) to synthesize overviews and persist the disposition table.

---

### Stage 5.4 — Related Chunks Auto-Link
Bidirectionally links same-disease L2 chunks via `related_chunks`:
```bash
python -m pipeline.run_stage --stage 5.4 --source "<SOURCE_PATH>" --out "<OUTPUT_DIR>"
```

---

### Stage 5 — Generate RAG_Optimised.md
Serializes final production micro-chunk markdown output with attached coverage metadata:
```bash
python -m pipeline.run_stage --stage 5 --source "<SOURCE_PATH>" --out "<OUTPUT_DIR>"
```
- **Output**: `{PREFIX}_RAG_Optimised.md`.

---

### Stage 6 — Hard-Fail Validation Gate
Executes comprehensive automated validation checks (6.1, 6.2, 6.4, 6.4b):
```bash
python -m pipeline.run_stage --stage 6 --source "<SOURCE_PATH>" --out "<OUTPUT_DIR>"
```
- **Gate**: `PASS` is required to ship. `HARD-FAIL` blocks completion.

---

### Stage 7 — Quality Scorecard (Advisory)
Computes multi-dimensional composite quality scores without adding API tokens:
```bash
python -m pipeline.run_stage --stage 7 --source "<SOURCE_PATH>" --out "<OUTPUT_DIR>"
```
- **Output**: `{PREFIX}_QualityScorecard.md` and `{PREFIX}_QualityScorecard.json`.

---

### Stage 8 — Source-Lines Precision & Trust Finalization
Performs mathematical precision verification on line bounds and synchronizes reports:
```bash
python -m pipeline.run_stage --stage 8 --source "<SOURCE_PATH>" --out "<OUTPUT_DIR>"
```
- **Action `CORPUS_REVIEW_PENDING`**: 👉 **MANDATORY**: Follow [`references/stage_8_protocol.md`](references/stage_8_protocol.md) to adjudicate findings, synchronize dual-format reports, and finalize the chapter trust protection marker.

---

## HyperAgent & Cloud Execution Runtime Notes

When executing inside HyperAgent, Cowork, or headless cloud sandboxes:

1. **Package Bootstrap in Flat Environments**:
   If skill scripts are delivered flatly into the skill root rather than nested under `pipeline/`, ensure scripts are copied into `pipeline/`, `pipeline/stages/`, and `scripts/maintenance/` before invoking `python -m pipeline.run_stage`.
2. **Uploaded Source Filename Prefixes**:
   Sandbox file uploads often prepend IDs (`<fileId>_<name>`). The runner's `derive_chapter_info()` automatically strips these prefixes to preserve canonical `Davidson_25_ChNN_Slug` naming.
3. **Stage 3 HTML Comment & Provenance Neutrality**:
   `compute_reaudit()` strips ALL HTML comments from both sides via `re.sub(r'<!--[\s\S]*?-->\n?', '', text)` before diff ratio calculation to prevent leading `<!-- PROVENANCE METADATA: ... -->` headers from falsely penalizing preservation percentages.
4. **Stage 3 Decoupled Figure Immunity**:
   Raw OCR image tags (`!\[img-\d+\.jpeg\]\(img-\d+\.jpeg\)`) are specifically stripped and checked in re-audit, strictly exempting canonical decoupled assets (`assets/figures/chNN_fig_*.jpeg`).
5. **Stage 4B Heading-Prefixed MCQ Stems**:
   The MCQ slicer supports question stems with heading prefixes (`### 13.1 <stem>`) as well as standard numeral forms (`13.1. <stem>`), preventing monolithic L1 bundling and Stage 4.5c coverage drops.
6. **Stage 4.6 In-Session Manual Adjudication (Headless / No `GEMINI_API_KEY`)**:
   When Stage 4.6 returns `action=pending_manual` (because `GEMINI_API_KEY` is absent), the gate pauses. Even if `references/stage_4_6_protocol.md` is inaccessible in flat-delivery sandboxes, follow this deterministic working procedure (verified across large chapters):
   
   **Procedure**:
   1. **Parse Chunks**: Use `from pipeline.stage_4_6_gemini_verification import _split_chunks, _get_chunk_level, _get_semantic_type, _get_topic, _get_body, _flag_review_priority`.
      Filter on `_get_chunk_level(part) == 2`. Note helper signature: `_flag_review_priority(topic, body, current_type)` (3 positional args — `topic` first).
   2. **Adjudicate All L2 Chunks**: Review EVERY L2 chunk against clinical heuristics. *Completeness Rule (v2.6.5)*: `decide_checkpoint_action(meta, total_flagged=...)` only returns `"complete"` when `chunks_reviewed >= total_flagged`. Always pass `total_flagged=total_L2_count` and set `chunks_reviewed=total_L2_count`.
   3. **Rewrite In-Place**: Update the `semantic_type: <new_type>` line in `chunks.md` (single replacement per chunk) and save back to disk.
   4. **Build Metadata & Provenance Log**:
      - Metadata: `{"needs_manual_verification": False, "chunks_unparsed": 0, "verification_method": "manual_in_session_adjudication", "corrections_applied": corrections_list, "semantic_type_distribution": dist}`.
      - Write `{PREFIX}_Remap_Log.md` with `format_markdown_provenance_header(source_path, "4.6")`.
      - Call `mark_stage_complete(checkpoint, checkpoint_path, "4.6", output_file=f"{PREFIX}_Remap_Log.md", **decision_metadata)`.
      - Re-run `python -m pipeline.run_stage --stage auto ...` to finish Stages 4.7 through 8 seamlessly.

   **Section-Header Adjudication Heuristics (Title beats body keywords)**:
   - `pathophysiology`: Anatomy/physiology, lung mechanics, control of breathing, V/Q matching, airway defences, Aetiology, Pathology and pathogenesis, `Causes of ...` tables.
   - `laboratory_investigation`: All imaging modalities and radiological signs (shadowing, translucency, hilar abnormalities), endoscopy (bronchoscopy, thoracoscopy, EBUS), cytology/histopathology, microbiology/serology, function tests, blood gases, lab specimens (FBC, U&E, LFTs, CRP, cultures, pleural fluid), `Investigations`.
   - `management_step`: Management/Treatment/Therapy, ventilation and oxygen therapy, rehabilitation, physiotherapy, surgery, Prevention, Discharge/follow-up, antibiotic-regimen tables, `Indications for ...` (transplant, assisted ventilation, ICU referral).
   - `drug_info`: Adverse-reaction tables, drug-resistance sections, `Drugs` as a cause of disease.
   - `diagnostic_criteria`: Named criteria/scores/indices (Light's criteria, BODE index, CURB-65), diagnostic algorithms/thresholds, `Diagnosis`.
   - `epidemiology_concept`: Epidemiology, `Risk factors for ...` / predisposing-factor tables, Prognosis, disease in old age/adolescence.
   - `clinical_feature`: Disease-overview headers, symptom/feature tables, examination / clinical-assessment sections, MCQ vignettes.
   - *Watch-outs*: 'Cytology and histopathology' is `laboratory_investigation` (not pathophysiology); 'Non-invasive ventilation' is `management_step` (not pathophysiology); `Features suggesting ...` is `clinical_feature` even when topic mentions a mechanism.
7. **Provenance Backfill on Final Artifacts**:
   Before final packaging, ensure every artifact (`chunks.md`, `SpotCheck.md`, `CompletenessChecklist.md`, `SourceLinesPrecision.md/.json`, `SCATTERED.json`, `SUSPECTED_GAP.json`, `COMPLETE_DISEASES.json`, `CHECKPOINT.json`) embeds the canonical provenance header or `_provenance` metadata.
8. **Forcing a Gated Stage Re-run**:
   `should_run_stage()` checks `checkpoint['stage_completions']`. Writing 'pending' to `checkpoint['stages']` is a no-op. To re-run a completed stage, delete its key from `stage_completions`, rewind `pipeline_state.last_completed_stage`, and re-invoke `--stage auto`.
9. **Stage 8 Advisory Status**:
   Finishing with Stage 6 **PASS** (0 hard fails) and Stage 7 **Score 1.0** while Stage 8 lands on `CORPUS_REVIEW_PENDING` (`trusted_for_downstream_use: false`) due to unresolved line spans is standard and expected—it indicates advisory precision review, not a pipeline failure.

---

## Chapter Completion Report Format

When reporting a finalized chapter, format the summary as follows:

```
Ch[N] — [TITLE]
Stage 1:    verdict | piracy hits | heading errors
Stage 2:    repairs list | lines before->after
Stage 3:    preservation % | PASSED/ISSUES
Stage 4:    L1 count | L2 count
Stage 4.5:  passed/total | figures OK/MISMATCH
Stage 4.5c: L1 checked | gaps found | PASS/BLOCKING-FAIL
Stage 4.5d: candidates found | confirmed corruptions | PASS/BLOCKED
Stage 4.5b: dosing% | threshold% | drug_info ratio (or SKIP)
Stage 4.6:  type distribution | chunks corrected
Stage 4.7:  SCATTERED count | SUSPECTED_GAP count
Stage 5:    final L2 count | path
Stage 6:    PASS/HARD-FAIL | failure count
Stage 7:    overall_score | dimensions scored
Stage 8:    precision-checked | unresolved findings | trust classification
```

---

## Modular References Directory

- **[Hard-Won Rules Reference](references/hard_won_rules.md)**: Rules A through V (MCQs, Rule P slugs, Rule R decoupled figures, Rule S algorithms, Rule T read-back invariant, Rule U proof discipline, Rule V stop-points).
- **[CDSS Master Architectural Decisions](references/cdss_architectural_decisions.md)**: 5 visual archetypes, 5 meaning preservation pillars, and zero-token deterministic guarantees.
- **[Post-Mortem & Prevention Strategy](references/post_mortem_and_prevention.md)**: Failure catalogue and 4-tier permanent prevention architecture.
- **[Stage 4.5d Clinical Fidelity Protocol](references/stage_4_5d_protocol.md)**: Candidate triage and corruption resolution.
- **[Stage 4.6 Semantic Verification Protocol](references/stage_4_6_protocol.md)**: Semantic classification rules and batch review protocol.
- **[Stage 4.7 Completeness Protocol](references/stage_4_7_protocol.md)**: Disease category analysis and synthesis.
- **[Stage 8 Trust Finalization Protocol](references/stage_8_protocol.md)**: Source-lines precision and fail-closed chapter protection.
- **[CDSS Downstream Integration Guide](references/cdss_rag_integration_guide.md)**: Specifications for downstream CDSS ingestion, hybrid search, and decoupled multi-modal UI rendering.

## Exit Codes & Assets (2026-09-25)
- `--stage auto` exit codes: `0` = complete and trusted; `1` = blocked, failed or pending review; `3` = finished but Stage 8 did not mark the chapter `trusted_for_downstream_use`.
- Chapter `assets/` are merged into `rag_pipeline_output/assets` on every run. A failed copy aborts the run instead of silently continuing.
- The Stage 4.6 remap log records the real gate outcome (`Status: complete|pending_manual|blocked|failed`).
