"""CP-03 — desired behavior: when Stage 1's verdict is production_safe and
Stage 2 is skipped, {PREFIX}_REPAIRED_S2.md must still exist as an exact
copy of SOURCE_PATH, since Stage 3 unconditionally reads it.

Per the "Limited Extraction Scope" decision, this fix is NOT pulled out of
SKILL.md into an importable pipeline/stages/ module (it's a two-line shutil.copyfile
addition to the Stage-1-skip block, not a verdict/decision function like the
other CP items) -- SKILL.md remains the sole authority for it. This test
therefore validates the DESIRED behavior via a standalone equivalent of that
exact block (shutil.copyfile + the same checkpoint call shape), not by
importing SKILL.md (which is markdown, not mechanically importable). The
actual SKILL.md edit was hand-verified to match this snippet -- see
PHASE0_PHASE1_REPORT.md's file-by-file diff summary for the real block.
"""
import os
import shutil

from pipeline.checkpoint_utils import load_or_create_checkpoint, load_checkpoint, mark_stage_complete


def stage1_skip_stage2(source_path, out_dir, prefix, checkpoint, checkpoint_path):
    """Equivalent of the fixed SKILL.md Stage-1-skip block."""
    out_path = os.path.join(out_dir, f"{prefix}_REPAIRED_S2.md")
    shutil.copyfile(source_path, out_path)
    mark_stage_complete(checkpoint, checkpoint_path, "2", output_file=os.path.basename(out_path),
                         repair_mode="pass_through",
                         status_note="SKIPPED - Stage 1 verdict was production_safe")
    return out_path


def test_stage2_skip_writes_exact_source_copy(tmp_path):
    source = tmp_path / "source.md"
    source.write_text("Clean chapter text, nothing to repair.\n", encoding="utf-8")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    checkpoint, checkpoint_path = load_or_create_checkpoint(
        source_path=str(source), output_dir=str(out_dir), prefix="Ch99", ch_num="99", ch_slug="Test",
    )
    # Stage 1 already ran and completed in this scenario (not under test here).
    mark_stage_complete(checkpoint, checkpoint_path, "1", verdict="production_safe")

    out_path = stage1_skip_stage2(str(source), str(out_dir), "Ch99", checkpoint, checkpoint_path)

    assert os.path.exists(out_path)
    assert open(out_path, encoding="utf-8").read() == open(source, encoding="utf-8").read()

    reloaded, _ = load_checkpoint(str(out_dir), "Ch99")
    assert reloaded["stage_completions"]["2"]["repair_mode"] == "pass_through"
    assert reloaded["stage_completions"]["2"]["status"] == "COMPLETED"


def test_stage3_can_read_the_skipped_output_without_crashing(tmp_path):
    """Confirms the specific downstream crash CP-03 exists to prevent:
    Stage 3 unconditionally opens {PREFIX}_REPAIRED_S2.md."""
    source = tmp_path / "source.md"
    source.write_text("Clean chapter text.\n", encoding="utf-8")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    checkpoint, checkpoint_path = load_or_create_checkpoint(
        source_path=str(source), output_dir=str(out_dir), prefix="Ch99", ch_num="99", ch_slug="Test",
    )
    mark_stage_complete(checkpoint, checkpoint_path, "1", verdict="production_safe")
    stage1_skip_stage2(str(source), str(out_dir), "Ch99", checkpoint, checkpoint_path)

    rep_path = os.path.join(str(out_dir), "Ch99_REPAIRED_S2.md")
    rep_text = open(rep_path, encoding="utf-8").read()  # must not raise FileNotFoundError

    from pipeline.stages.stage_3_reaudit import compute_reaudit
    result = compute_reaudit(open(source, encoding="utf-8").read(), rep_text)
    assert result["verdict"] == "PASSED"
