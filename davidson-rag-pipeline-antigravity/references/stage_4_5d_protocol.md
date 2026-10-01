# Stage 4.5d — Clinical Fidelity Adjudication Protocol

## Purpose
Stage 4.5d prevents clinical semantic mutations between `REPAIRED_S2.md` and `chunks.md` (e.g. dropped dose digits, reversed inequalities, inverted polarity, fragmented sentences, table cell corruptions).

## Two-Phase Execution Design
- **Phase A (Automated Scan)**: Runs 11 zero-token deterministic pattern detectors across numbers, units, inequalities, ranges, doses, durations, frequencies, negations, polarity, sequences, and boundary losses.
- **Phase B (Human/Agent Adjudication)**: Every detector finding is a **candidate**, not an automated verdict. If candidates exist (`action == "pending_manual"`), manual triage is mandatory.

## Adjudication Steps

1. **Export Candidates for Review**:
   ```python
   import json
   from pipeline.stages import stage_4_5d_clinical_fidelity as s45d
   
   candidates_data = json.load(open(f"{out_dir}/{PREFIX}_ClinicalFidelity.json", encoding='utf-8'))['candidates']
   batches = s45d.export_candidates_for_review(candidates_data, batch_size=25)
   for i, batch in enumerate(batches, 1):
       open(f"{out_dir}/fidelity_review_batch_{i:02d}.md", 'w', encoding='utf-8').write(batch)
   print(f"{len(batches)} batches written for manual review")
   ```

2. **Judge Candidates**:
   Inspect each `fidelity_review_batch_NN.md`. Compare the chunk text against `REPAIRED_S2.md`.
   Classify each candidate ID into one of:
   - `"confirmed_corruption"`: A genuine clinical mutation (e.g., `< 50` changed to `> 50`, or missing units).
   - `"false_positive"`: Candidate triggered by non-clinical noise (e.g., figure numbers, page citations).
   - `"legitimate_paraphrase"`: Stylistic or structural shift that preserves exact clinical meaning.

3. **Apply Decisions & Splice Fixes**:
   ```python
   decisions = {
       "4.5d-numeric-L2-038-2": "false_positive",
       "4.5d-inequality-L2-092-1": "confirmed_corruption",
   }
   s45d.apply_adjudication_decisions(candidates_data, decisions)
   json.dump({"candidates": candidates_data}, open(f"{out_dir}/{PREFIX}_ClinicalFidelity.json", 'w', encoding='utf-8'), indent=2)
   ```
   For every `confirmed_corruption`:
   - Splice the exact verbatim text from `REPAIRED_S2.md` into `{PREFIX}_chunks.md`.
   - Mark candidate `re_verified: true`.
   - Clean up temporary batch files and re-run Stage 4.5d gate.