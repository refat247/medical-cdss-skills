"""CP-05 + correction H — desired behavior: Stage 4.6 blocks when
chunks_unparsed/chunks_reviewed exceeds 10%, and BLOCKS/FAILS explicitly
(never silently treats the ratio as zero) when chunks_reviewed == 0.
"""
from pipeline.stages.stage_4_6_decision import decide_checkpoint_action, DEGRADED_RATIO_THRESHOLD


def test_degraded_ratio_above_threshold_blocks():
    meta = {"needs_manual_verification": False, "chunks_reviewed": 20,
            "chunks_unparsed": 3, "chunks_corrected": 5}  # 15% > 10%
    action, out = decide_checkpoint_action(meta)
    assert action == "blocked"
    assert out["unparsed_ratio"] > DEGRADED_RATIO_THRESHOLD


def test_ratio_at_threshold_boundary_passes():
    meta = {"needs_manual_verification": False, "chunks_reviewed": 20,
            "chunks_unparsed": 2, "chunks_corrected": 5}  # exactly 10%, not > 10%
    action, out = decide_checkpoint_action(meta)
    assert action == "complete"


def test_ratio_well_below_threshold_completes():
    meta = {"needs_manual_verification": False, "chunks_reviewed": 20,
            "chunks_unparsed": 1, "chunks_corrected": 5}  # 5%
    action, out = decide_checkpoint_action(meta)
    assert action == "complete"


def test_chunks_reviewed_zero_never_treated_as_clean_pass():
    """Correction H: the old _build_metadata-only logic computed
    unparsed_ratio via `len(unparsed_ids) / chunks_reviewed if chunks_reviewed
    else 0` -- a chunks_reviewed=0 chapter would silently compute ratio=0,
    i.e. look identical to a genuinely clean pass. This must now be an
    explicit failure requiring a human look, never an implicit PASS."""
    meta = {"needs_manual_verification": False, "chunks_reviewed": 0, "chunks_unparsed": 0}
    action, out = decide_checkpoint_action(meta)
    assert action == "failed"
    assert out["chunks_reviewed"] == 0


def test_manual_verification_path_takes_priority_over_ratio_check():
    meta = {"needs_manual_verification": True, "chunks_reviewed": 0, "chunks_unparsed": 0}
    action, out = decide_checkpoint_action(meta)
    assert action == "pending_manual"
