"""v2.6.5 Part 5: Stage 4.6 must not be marked COMPLETED merely because
SOME regex-flagged candidates were reviewed. This is the exact defect
found on Chapter 14 (45/283 flagged candidates reviewed, returned
"complete" pre-v2.6.5 with no signal that 238 remained unreviewed).
"""
from pipeline.stages.stage_4_6_decision import decide_checkpoint_action


def _meta(chunks_reviewed, chunks_corrected=0, chunks_unparsed=0):
    return {
        "needs_manual_verification": False,
        "chunks_reviewed": chunks_reviewed,
        "chunks_corrected": chunks_corrected,
        "chunks_unparsed": chunks_unparsed,
    }


def test_pre_v2_6_5_behavior_preserved_when_total_flagged_omitted():
    """Backward compatibility: existing callers that don't pass
    total_flagged still get "complete" from any chunks_reviewed > 0 within
    threshold — this parameter is opt-in, not a breaking change."""
    action, meta = decide_checkpoint_action(_meta(chunks_reviewed=45, chunks_corrected=10))
    assert action == "complete"


def test_partial_review_is_review_incomplete_not_complete():
    """The core regression test: 45 of 283 flagged candidates reviewed
    must NOT return 'complete'."""
    action, meta = decide_checkpoint_action(
        _meta(chunks_reviewed=45, chunks_corrected=10), total_flagged=283
    )
    assert action == "review_incomplete"
    assert meta["total_flagged"] == 283
    assert meta["chunks_reviewed"] == 45
    assert "238" in meta["reason"]  # remaining count called out explicitly


def test_full_review_of_all_flagged_candidates_is_complete():
    action, meta = decide_checkpoint_action(
        _meta(chunks_reviewed=283, chunks_corrected=20), total_flagged=283
    )
    assert action == "complete"
    assert meta["review_completeness_ratio"] == 1.0


def test_reviewing_more_than_flagged_still_complete():
    """chunks_reviewed can legitimately exceed total_flagged (e.g. a
    reviewer double-checks some already-clean chunks too) -- not a bug."""
    action, meta = decide_checkpoint_action(
        _meta(chunks_reviewed=300, chunks_corrected=20), total_flagged=283
    )
    assert action == "complete"


def test_zero_flagged_candidates_with_total_flagged_zero_is_complete():
    """A chapter where the regex baseline found nothing to flag at all —
    total_flagged=0 means there was nothing required to review, not an
    incomplete state."""
    action, meta = decide_checkpoint_action(
        _meta(chunks_reviewed=1, chunks_corrected=0), total_flagged=0
    )
    assert action == "complete"
    assert meta["review_completeness_ratio"] == 1.0


def test_review_incomplete_takes_priority_over_blocked_only_when_ratio_ok():
    """Degraded-run blocking (CP-05) is still checked BEFORE the
    completeness check -- an unparsed-ratio failure should still block,
    not silently downgrade to review_incomplete."""
    action, meta = decide_checkpoint_action(
        _meta(chunks_reviewed=10, chunks_corrected=1, chunks_unparsed=5), total_flagged=283
    )
    assert action == "blocked"


def test_chunks_reviewed_zero_still_fails_regardless_of_total_flagged():
    action, meta = decide_checkpoint_action(_meta(chunks_reviewed=0), total_flagged=283)
    assert action == "failed"
