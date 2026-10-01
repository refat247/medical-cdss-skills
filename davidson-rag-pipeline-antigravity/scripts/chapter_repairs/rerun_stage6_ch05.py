"""Re-run Stage 6 for real against Chapter 05 now that Stage 4.5d's gate is
PASS, and update the checkpoint accordingly (mark_stage_complete for both
"4.5d" and "6", replacing the stale pre-4.5d "6" entry -- see
PHASE0_PHASE1_REPORT.md's "known limitations" #1 for why this needed doing
explicitly rather than happening automatically via should_run_stage).

v2.6.3 SAFETY GUARDRAIL: CLASSIFICATION = chapter-specific repair, mutates
the checkpoint (a certified chapter's stage_completions) AND writes
Stage6_Validation.md. Default invocation is READ-ONLY -- computes and
prints the would-be Stage 6 verdict without touching the checkpoint or the
real Stage6_Validation.md file. Requires --write --in-place --backup
(backup mandatory once CORPUS_OUTPUT_PROTECTED.json exists for this
chapter) to actually mutate. Uses load_checkpoint_for_run() (v2.6.3), not
the historical load_checkpoint() alias, to make the pipeline-execution
intent explicit at this call site.
"""
import argparse
import sys
import os
import json
import shutil
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pipeline.checkpoint_utils import load_checkpoint_for_run, mark_stage_complete, checkpoint_path_for
from pipeline.stages.stage_4_5d_clinical_fidelity import decide_checkpoint_action, build_clinical_fidelity_gate
from pipeline.stages.stage_6_validation import run_stage_6
from pipeline.stages.mutation_guard import require_authorization_for_in_place_mutation, MutationRefused

OUT_DIR = r"D:\davidson_25_full_pipeline\05"
PREFIX = "Davidson_25_Ch05_Nutritional_factors_in_disease"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--in-place", action="store_true")
    parser.add_argument("--backup", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    gate = json.load(open(f"{OUT_DIR}\\{PREFIX}_ClinicalFidelityGate.json", encoding="utf-8"))
    action, metadata = decide_checkpoint_action(gate)
    print(f"Stage 4.5d checkpoint action would be: {action}")

    rag_text = open(f"{OUT_DIR}\\{PREFIX}_RAG_Optimised.md", encoding="utf-8").read()
    gaps_text = open(f"{OUT_DIR}\\{PREFIX}_L1L2_CoverageGaps.md", encoding="utf-8").read()
    result = run_stage_6(rag_text, gaps_text, gate)
    print(f"Stage 6 verdict: {result['verdict']} | failures: {result['failures']}")

    log_path = os.path.join(OUT_DIR, f"{PREFIX}_Stage6_Validation.md")
    out = [f"# Stage 6 Validation — {PREFIX}", f"Chunks checked: {result['chunks_checked']}",
           f"VERDICT: {result['verdict']}"]
    if result["failures"]:
        out += ["", "FAILURES:"] + [f"  - {f}" for f in result["failures"]]
    report_text = "\n".join(out)

    try:
        require_authorization_for_in_place_mutation(
            OUT_DIR, PREFIX, args,
            target_description=f"{PREFIX}'s checkpoint (Stage 4.5d/6 entries) and Stage6_Validation.md",
        )
    except MutationRefused:
        print("READ-ONLY mode: checkpoint and Stage6_Validation.md NOT written. "
              "Re-run with --write --in-place --backup to apply for real.")
        return result

    assert action == "complete", f"expected complete, got {action}"
    assert result["verdict"] == "PASS", "Stage 6 did not pass -- not marking complete"

    cp_path = checkpoint_path_for(OUT_DIR, PREFIX)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    shutil.copyfile(cp_path, f"{cp_path}.pre-mutation-{ts}.bak")
    if os.path.exists(log_path):
        shutil.copyfile(log_path, f"{log_path}.pre-mutation-{ts}.bak")

    checkpoint, checkpoint_path = load_checkpoint_for_run(OUT_DIR, PREFIX)
    mark_stage_complete(checkpoint, checkpoint_path, "4.5d",
                         output_file=f"{PREFIX}_ClinicalFidelityGate.json", **metadata)

    open(log_path, "w", encoding="utf-8").write(report_text)

    checkpoint, checkpoint_path = load_checkpoint_for_run(OUT_DIR, PREFIX)
    mark_stage_complete(checkpoint, checkpoint_path, "6", output_file=os.path.basename(log_path),
                         chunks_checked=result["chunks_checked"], hard_fails=0, verdict="PASS")
    print("Stage 6 re-marked COMPLETED under v2.6.0 rules (including Check 6.4b).")
    print(f"pipeline_status: {checkpoint['pipeline_state']['pipeline_status']}")
    print(f"corpus_pipeline_completed: {checkpoint['pipeline_state']['corpus_pipeline_completed']}")
    return result


if __name__ == "__main__":
    main()
