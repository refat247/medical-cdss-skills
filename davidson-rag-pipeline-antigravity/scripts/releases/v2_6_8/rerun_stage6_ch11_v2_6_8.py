"""v2.6.8 -- re-run Stage 6 for Chapter 11 after the related_chunks
restoration (Stage 5.4/5 regenerated with related_chunks added back).

This script calls ONLY canonical, unmodified logic
(`stages.stage_6_validation.run_stage_6`) -- it does not reimplement any
check. Stage 6 does not read `related_chunks` at all (confirmed by
CH11_RELATED_CHUNKS_CONTRACT_AUDIT.md section 1 and by direct grep), so this
re-run is expected to reproduce the same PASS/106 verdict Chapter 11 already
had -- it exists only to keep Stage6_Validation.md and the checkpoint's
Stage 6 evidence in sync with the regenerated RAG_Optimised.md (whose file
hash changed even though its Stage-6-relevant fields did not), consistent
with this corpus's existing practice of re-validating after any content
regeneration (see rerun_stage6_ch11_ch15_v2_6_7.py precedent).

Default invocation is READ-ONLY (dry-run: prints the verdict/counts without
writing anything). Requires --write --in-place --backup (Chapter 11 is
corpus-output-protected) to mutate for real.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from pipeline.checkpoint_utils import load_checkpoint_for_run, mark_stage_complete, checkpoint_path_for, record_manual_edit
from pipeline.stages.stage_6_validation import run_stage_6
from pipeline.stages.mutation_guard import require_authorization_for_in_place_mutation, MutationRefused

OUT_DIR = r"D:\davidson_25_full_pipeline\11"
PREFIX = "Davidson_25_Ch11_Poisoning"
EXPECTED_COUNT = 106


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--in-place", action="store_true", dest="in_place")
    parser.add_argument("--backup", action="store_true")
    args = parser.parse_args()

    rag_text = open(f"{OUT_DIR}\\{PREFIX}_RAG_Optimised.md", encoding="utf-8").read()
    gaps_text = open(f"{OUT_DIR}\\{PREFIX}_L1L2_CoverageGaps.md", encoding="utf-8").read()
    gate = json.load(open(f"{OUT_DIR}\\{PREFIX}_ClinicalFidelityGate.json", encoding="utf-8"))

    result = run_stage_6(rag_text, gaps_text, gate)
    print(f"Stage 6 verdict: {result['verdict']} | chunks_checked: {result['chunks_checked']} "
          f"| failures: {result['failures']}")

    assert result["chunks_checked"] == EXPECTED_COUNT, (
        f"expected {EXPECTED_COUNT} chunks_checked, got {result['chunks_checked']}"
    )
    assert result["verdict"] == "PASS", "Stage 6 did not pass -- not updating evidence"

    # L2-105-GAP visibility check: confirm the v2.6.7 parser still sees the
    # gap stub after the related_chunks restoration (unrelated fix, should
    # be unaffected).
    assert "L2-105-GAP" in rag_text, "L2-105-GAP unexpectedly missing from RAG_Optimised.md"
    from pipeline.stages.stage_6_validation import _split_blocks
    blocks, malformed = _split_blocks(rag_text)
    gap_block_found = any("L2-105-GAP" in b for b in blocks)
    print(f"L2-105-GAP visible to parser as its own block: {gap_block_found} | malformed: {malformed}")
    assert gap_block_found, "L2-105-GAP not parsed as its own block"
    assert not malformed, f"unexpected malformed blocks: {malformed}"

    log_path = os.path.join(OUT_DIR, f"{PREFIX}_Stage6_Validation.md")
    out_lines = [f"# Stage 6 Validation — {PREFIX}", f"Chunks checked: {result['chunks_checked']}",
                 f"VERDICT: {result['verdict']}"]
    if result["failures"]:
        out_lines += ["", "FAILURES:"] + [f"  - {f}" for f in result["failures"]]
    out_lines += [
        "",
        "v2.6.8 NOTE: re-run after the related_chunks restoration (Stage 5.4/5 regenerated). "
        "Stage 6 does not read related_chunks at all (confirmed by "
        "CH11_RELATED_CHUNKS_CONTRACT_AUDIT.md) -- this re-run reproduces the same PASS/106 "
        "verdict Chapter 11 already had; it exists only to keep this evidence file in sync with "
        "RAG_Optimised.md's changed hash. L2-105-GAP confirmed still visible to the v2.6.7-fixed "
        "parser (unaffected by this unrelated restoration).",
    ]
    report_text = "\n".join(out_lines) + "\n"

    try:
        require_authorization_for_in_place_mutation(
            OUT_DIR, PREFIX, args,
            target_description=f"{PREFIX}'s checkpoint (Stage 6 entry) and Stage6_Validation.md",
        )
    except MutationRefused as e:
        print(f"READ-ONLY mode: checkpoint and Stage6_Validation.md NOT written ({e}). "
              "Re-run with --write --in-place --backup to apply for real.")
        return result

    if args.backup and os.path.exists(log_path):
        import shutil
        from datetime import datetime, timezone
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        shutil.copy2(log_path, f"{log_path}.pre-v2.6.8-stage6-rerun-{ts}.bak")

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    checkpoint, checkpoint_path = load_checkpoint_for_run(OUT_DIR, PREFIX)
    mark_stage_complete(checkpoint, checkpoint_path, "6",
                         output_file=f"{PREFIX}_Stage6_Validation.md",
                         chunks_checked=result["chunks_checked"],
                         hard_fails=len(result["failures"]),
                         verdict=result["verdict"])
    record_manual_edit(checkpoint, checkpoint_path, "6",
                        os.path.join(OUT_DIR, f"{PREFIX}_RAG_Optimised.md"),
                        "Stage 6 re-run after related_chunks restoration (Stage 5.4/5 regenerated "
                        "RAG_Optimised.md with related_chunks added). Verdict unchanged: PASS, "
                        "chunks_checked=106. L2-105-GAP confirmed still visible to the v2.6.7-fixed "
                        "parser.")
    print("Stage 6 evidence updated.")
    return result


if __name__ == "__main__":
    main()
