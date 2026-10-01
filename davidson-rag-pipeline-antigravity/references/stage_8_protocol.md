# Stage 8 — Source-Lines Precision & Trust Finalization Protocol

## Purpose
Enforces mathematical precision on declared `source_lines` metadata, performs dual-format Markdown/JSON synchronization, and executes fail-closed corpus trust finalization.

## Precision Checking & Adjudication

1. **Run Precision Checker**:
   ```python
   import argparse
   from pipeline.stages.source_lines_precision import run_source_lines_precision, build_precision_summary
   
   cli_args = argparse.Namespace(write=True, in_place=True, backup=False, dry_run=False)
   results = run_source_lines_precision(out_dir, PREFIX, args=cli_args)
   summary = build_precision_summary(results)
   ```

2. **Adjudicate Unresolved Findings**:
   If `summary['unresolved_count'] > 0`, inspect `{PREFIX}_SourceLinesPrecision.md`:
   - `CHECKER_FALSE_POSITIVE`: Short bullet gaps where chunk body is fully verbatim.
   - `HUMAN_CONFIRMED_METADATA_DEFECT`: Genuine missing or extra lines relative to declared bounds. Splice-fix `source_lines` in chunks.md and re-run.

3. **Dual-Format Sync**:
   Render both `{PREFIX}_SourceLinesPrecision.json` and `{PREFIX}_SourceLinesPrecision.md` to ensure zero unresolved discrepancies exist.

## Mandatory Finalization Sequence

To qualify a chapter as `CORPUS_TESTING_READY` and finalize its trust protection marker:
1. Verify Stages 1 through 8 are marked completed in `CHECKPOINT.json`.
2. Ensure `stages.corpus_trust.classify_trust()` returns `CORPUS_TESTING_READY`.
3. Run dry-run finalizer:
   ```bash
   python pipeline/finalize_trusted_chapter.py <out_dir>
   ```
4. Authorize finalization:
   ```bash
   python pipeline/finalize_trusted_chapter.py <out_dir> --write --authorize
   ```
5. Verify corpus invariants across all trusted chapters:
   ```bash
   python pipeline/verify_trusted_corpus_invariants.py <corpus_root>
   ```

## Advisory Status Interpretation Note

A chapter that finishes with Stage 6 **PASS** (0 hard fails) and Stage 7 overall score **1.0** can land on Stage 8 `CORPUS_REVIEW_PENDING` / `trusted_for_downstream_use: false` when minor line-span over-inclusive or under-inclusive variances remain. This is expected advisory disclosure and does not block production CDSS vector payload generation or downstream clinical use.