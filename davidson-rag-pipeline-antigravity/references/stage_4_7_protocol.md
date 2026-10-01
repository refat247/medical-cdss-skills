# Stage 4.7 & 5.2 — Clinical Completeness Gate Protocol

## Purpose
Ensures disease entities mentioned across the chapter have complete clinical coverage across the 5 core categories:
1. `causes`
2. `clinical_presentation`
3. `investigation`
4. `treatment`
5. `complication_or_safety`

## Category Inference Hierarchy
1. **Tier 1 (Topic Keywords)**: High-confidence literal title triggers (`Causes of`, `Management of`, `Investigations in`).
2. **Tier 2 (Semantic Type Fallback)**: Multi-category mapping based on verified semantic tags.
3. **Tier 3 (Body Text Pattern Scan)**: Regex identification of inline clinical patterns (e.g. `treatment is with...`, `caused by...`).

## Triage & Synthesis Protocol (Stage 5.2)

1. **Evaluate SCATTERED Clusters**:
   Inspect `{PREFIX}_SCATTERED.json`. For disease clusters flagged as `SCATTERED`:
   - Filter out non-disease headings (e.g. `shoulder_pain`, `joint_aspiration`).
   - Verify if missing content is present in neighboring paragraphs in `REPAIRED_S2.md`.

2. **Synthesize Missing Overviews (Tier 2)**:
   For confirmed disease gaps with fragmented chunks:
   - Assemble a 150–300 word summary strictly from the chapter's existing fragments (zero outside fabrication).
   - Append to `{PREFIX}_chunks.md` with frontmatter `synthesized: true` and a clear `gap_note`.

3. **Persist Triage Disposition**:
   Always record the clinical rationale table in `{PREFIX}_CompletenessChecklist.md` and update the checkpoint:
   ```python
   checkpoint["stage_completions"]["4.7"]["unresolved_completeness_clusters"] = 0
   mark_stage_complete(checkpoint, checkpoint_path, "5.2", ...)
   ```