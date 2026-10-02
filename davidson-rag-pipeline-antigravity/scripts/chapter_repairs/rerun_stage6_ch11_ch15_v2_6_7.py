"""v2.6.7 -- re-run Stage 6 for Chapters 11 and 15 using the fixed
check_6_1_6_2() parser (REPOSITORY_PRODUCTION_READINESS_AUDIT.md Blocker 2).

Neither chapter's RAG_Optimised.md, chunks.md, or any other stage's evidence
is touched -- this only re-runs Stage 6 itself (now correctly inspecting the
final coverage_gap stub in each file) and, if it genuinely passes clean,
updates Stage6_Validation.md and the checkpoint's stage_completions["6"]
entry, plus a record_manual_edit() audit-trail entry explaining why.

Default invocation is READ-ONLY (prints the would-be verdict/counts without
writing anything). Requires --write --in-place --backup to mutate for real,
same pattern as rerun_stage6_ch05.py.
"""
import argparse
import sys
import os
import json
import shutil
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pipeline.checkpoint_utils import load_checkpoint_for_run, mark_stage_complete, checkpoint_path_for, record_manual_edit
from pipeline.stages.stage_6_validation import run_stage_6
from pipeline.stages.mutation_guard import require_authorization_for_in_place_mutation, MutationRefused

CHAPTERS = [
    {
        "out_dir": r"D:\davidson_25_full_pipeline\11",
        "prefix": "Davidson_25_Ch11_Poisoning",
        "expected_count": 106,
    },
    {
        "out_dir": r"D:\davidson_25_full_pipeline\15",
        "prefix": "Davidson_25_Ch15_Sexually_transmitted_infections",
        "expected_count": 87,
    },
]


def run_one(ch, args):
    out_dir, prefix = ch["out_dir"], ch["prefix"]
    print(f"\n=== {prefix} ===")

    rag_text = open(f"{out_dir}\\{prefix}_RAG_Optimised.md", encoding="utf-8").read()
    gaps_text = open(f"{out_dir}\\{prefix}_L1L2_CoverageGaps.md", encoding="utf-8").read()
    gate = json.load(open(f"{out_dir}\\{prefix}_ClinicalFidelityGate.json", encoding="utf-8"))

    result = run_stage_6(rag_text, gaps_text, gate)
    print(f"Stage 6 verdict: {result['verdict']} | chunks_checked: {result['chunks_checked']} "
          f"| failures: {result['failures']}")

    assert result["chunks_checked"] == ch["expected_count"], (
        f"expected {ch['expected_count']} chunks_checked post-fix, got {result['chunks_checked']}"
    )
    assert result["verdict"] == "PASS", f"Stage 6 did not pass for {prefix} -- not updating evidence"

    log_path = os.path.join(out_dir, f"{prefix}_Stage6_Validation.md")
    out_lines = [f"# Stage 6 Validation — {prefix}", f"Chunks checked: {result['chunks_checked']}",
                 f"VERDICT: {result['verdict']}"]
    if result["failures"]:
        out_lines += ["", "FAILURES:"] + [f"  - {f}" for f in result["failures"]]
    out_lines += [
        "",
        "v2.6.7 NOTE: re-run after the check_6_1_6_2() block-parsing fix "
        "(REPOSITORY_PRODUCTION_READINESS_AUDIT.md Blocker 2). The prior count "
        f"({ch['expected_count'] - 1}) silently omitted this file's final chunk (a frontmatter-only "
        "coverage_gap stub) because the file has no trailing newline. RAG_Optimised.md/chunks.md "
        "were NOT modified -- only Stage 6's own parser and this evidence changed.",
    ]
    report_text = "\n".join(out_lines) + "\n"

    try:
        require_authorization_for_in_place_mutation(
            out_dir, prefix, args,
            target_description=f"{prefix}'s checkpoint (Stage 6 entry) and Stage6_Validation.md",
        )
    except MutationRefused:
        print("READ-ONLY mode: checkpoint and Stage6_Validation.md NOT written. "
              "Re-run with --write --in-place --backup to apply for real.")
        return result

    cp_path = checkpoint_path_for(out_dir, prefix)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    shutil.copyfile(cp_path, f"{cp_path}.pre-v2.6.7-stage6-rerun-{ts}.bak")
    if os.path.exists(log_path):
        shutil.copyfile(log_path, f"{log_path}.pre-v2.6.7-stage6-rerun-{ts}.bak")

    open(log_path, "w", encoding="utf-8").write(report_text)

    checkpoint, checkpoint_path = load_checkpoint_for_run(out_dir, prefix)
    mark_stage_complete(checkpoint, checkpoint_path, "6", output_file=os.path.basename(log_path),
                         chunks_checked=result["chunks_checked"], hard_fails=0, verdict="PASS")
    checkpoint, checkpoint_path = load_checkpoint_for_run(out_dir, prefix)
    record_manual_edit(
        checkpoint, checkpoint_path, "6", log_path,
        note=(
            "v2.6.7 emergency correctness fix: check_6_1_6_2()'s block-splitting regex silently "
            f"dropped this file's final chunk (an empty-body coverage_gap stub) because the file "
            f"has no trailing newline. Real count is {ch['expected_count']} "
            f"(was {ch['expected_count'] - 1}). Parser fixed in pipeline/stages/stage_6_validation.py "
            "(_split_blocks, boundary-based splitting robust to missing trailing newline). "
            "RAG_Optimised.md/chunks.md content unchanged -- only Stage 6's own re-derived count "
            "and this checkpoint entry were updated after manually re-verifying the stub's own "
            "frontmatter (chunk_id, semantic_type=coverage_gap, disease_focus, coverage_status=gap, "
            "gap_note) is well-formed."
        ),
    )
    print(f"Stage 6 re-marked COMPLETED for {prefix} under v2.6.7's fixed parser.")
    next_stage = checkpoint["pipeline_state"]["next_stage_to_run"]
    if next_stage is not None:
        print("L7 SAFETY: this archival Stage 6 re-run intentionally leaves the chapter UNTRUSTED. "
              f"Resume from Stage {next_stage}, complete every required stage through Stage 8, "
              "then run finalize_trusted_chapter.py and verify_trusted_corpus_invariants.py.")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--in-place", action="store_true")
    parser.add_argument("--backup", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    results = []
    for ch in CHAPTERS:
        results.append(run_one(ch, args))
    return results


if __name__ == "__main__":
    main()
