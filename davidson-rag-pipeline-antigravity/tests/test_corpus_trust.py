"""v2.6.2 — deterministic corpus-trust classifier (was previously hand-
edited prose across several documents, per-chapter, independently — a real
error occurred that way: 25_AI_H was misclassified as having no checkpoint
at all when it actually has one, just an ancient pre-Stage-4.5c one).

`stages.corpus_trust.classify_trust()` takes small, explicit evidence
inputs (never infers from `RAG_Optimised.md`'s mere existence) and returns
a structured classification. This is the single source of truth going
forward — CORPUS_TRUST_STATUS.md should describe its OUTPUT, not
independently re-derive classifications by hand.
"""
from pipeline.stages.corpus_trust import classify_trust


def _ch05_shaped_checkpoint():
    return {
        "chapter_info": {"checkpoint_schema_version": "2.0"},
        "pipeline_state": {
            "pipeline_status": "CORPUS_PIPELINE_COMPLETED",
            "corpus_pipeline_completed": True,
            "advisory_scorecard_completed": True,
        },
        "stage_completions": {
            "4.5c": {"status": "COMPLETED"},
            "4.5d": {"status": "COMPLETED"},
            "6": {"status": "COMPLETED"},
        },
    }


def _ch05_gate_pass():
    return {"verdict": "PASS", "unresolved_candidates": 0, "unresolved_corruptions": 0}


def _25_ai_h_shaped_ancient_checkpoint():
    """Real shape, confirmed against the actual 25_AI_H checkpoint during
    the audit: no chapter_info.pipeline_version key, no '4.5c' key in
    stage_completions (predates that stage's introduction), literal
    pipeline_status == 'COMPLETED' (pre-v2.6.0 string)."""
    return {
        "chapter_info": {},  # no pipeline_version, no checkpoint_schema_version
        "pipeline_state": {"pipeline_status": "COMPLETED", "next_stage_to_run": None},
        "stage_completions": {
            "1": {"status": "COMPLETED"}, "2": {"status": "COMPLETED"},
            "3": {"status": "COMPLETED"}, "4a": {"status": "COMPLETED"},
            "4b": {"status": "COMPLETED"}, "4.5": {"status": "COMPLETED"},
            "4.5b": {"status": "COMPLETED"}, "4.6": {"status": "COMPLETED"},
            "4.7": {"status": "COMPLETED"}, "5.2": {"status": "COMPLETED"},
            "5.3": {"status": "COMPLETED"}, "5.4": {"status": "COMPLETED"},
            "5": {"status": "COMPLETED"}, "6": {"status": "COMPLETED"},
        },
    }


def test_chapter_05_shaped_state_classifies_corpus_testing_ready():
    """v2.6.6: Stage 4.6/4.7/8 evidence is now mandatory once a chapter
    reaches corpus_completed+gate_pass, so the full evidence set is supplied
    explicitly here (this basic v2.6.2-era fixture predates those stages)."""
    result = classify_trust(
        _ch05_shaped_checkpoint(), clinical_fidelity_gate=_ch05_gate_pass(),
        source_lines_precision_summary={"tested": True, "unresolved_count": 0},
        stage_4_6_review_status="COMPLETED",
        stage_4_6_chunks_reviewed=10, stage_4_6_total_flagged=10,
        unresolved_completeness_clusters=0,
    )
    assert result["classification"] == "CORPUS_TESTING_READY"
    assert result["trusted_for_downstream_use"] is True


def test_chapter_05_shaped_state_without_v2_6_6_evidence_is_review_pending():
    """v2.6.6 (Fail-Closed Finalization): the same checkpoint as above,
    WITHOUT the new mandatory Stage 4.6/4.7/8 evidence, must now demote to
    CORPUS_REVIEW_PENDING rather than silently reaching CORPUS_TESTING_READY
    -- this is the systemic fix for the Chapter 11 defect (missing evidence
    treated as 'not considered' instead of 'must fail closed')."""
    result = classify_trust(_ch05_shaped_checkpoint(), clinical_fidelity_gate=_ch05_gate_pass())
    assert result["classification"] == "CORPUS_REVIEW_PENDING"
    assert result["trusted_for_downstream_use"] is False


def test_25_ai_c_shaped_no_checkpoint_but_reached_stage6_evidence_is_legacy_uncheckpointed():
    """25_AI_C: no checkpoint file, but has Stage6_Validation.md and
    L1L2_CoverageGaps.md on disk from an ad hoc script run that DID reach
    those stages."""
    result = classify_trust(
        checkpoint=None,
        has_stage6_validation_file=True,
        has_coverage_gaps_file=True,
    )
    assert result["classification"] == "LEGACY_UNCHECKPOINTED"
    assert result["trusted_for_downstream_use"] is False


def test_25_ai_h_shaped_ancient_checkpoint_is_legacy_stale_checkpoint():
    """The specific audit-corrected case: 25_AI_H DOES have a checkpoint
    (not None), but it predates Stage 4.5c entirely -- must classify as
    LEGACY_STALE_CHECKPOINT, not LEGACY_UNCHECKPOINTED (which would
    incorrectly imply no checkpoint exists) and not CORPUS_TESTING_READY
    (its historical 'COMPLETED' does not equal modern certification)."""
    result = classify_trust(_25_ai_h_shaped_ancient_checkpoint())
    assert result["classification"] == "LEGACY_STALE_CHECKPOINT"
    assert result["trusted_for_downstream_use"] is False
    assert result["required_action"] == "FULL_CANONICAL_RERUN_REQUIRED"


def test_chapter_27_shaped_no_checkpoint_no_stage6_evidence_is_legacy_ungated():
    """27: no checkpoint, no Stage6_Validation.md, no L1L2_CoverageGaps.md
    -- ad hoc scripts stopped before ever reaching those stages."""
    result = classify_trust(
        checkpoint=None,
        has_stage6_validation_file=False,
        has_coverage_gaps_file=False,
    )
    assert result["classification"] == "LEGACY_UNGATED"
    assert result["trusted_for_downstream_use"] is False


def test_old_completed_string_does_not_equal_modern_corpus_certification():
    """A checkpoint with stage_completions including '4.5c' AND '4.5d' but
    an old-style bare pipeline_status=='COMPLETED' string (rather than the
    current CORPUS_PIPELINE_COMPLETED) must not be silently treated as
    certified just because both modern stage keys happen to be present."""
    cp = _ch05_shaped_checkpoint()
    cp["pipeline_state"]["pipeline_status"] = "COMPLETED"  # old-style string
    cp["pipeline_state"]["corpus_pipeline_completed"] = False  # flag never actually set
    result = classify_trust(cp, clinical_fidelity_gate=_ch05_gate_pass())
    assert result["classification"] != "CORPUS_TESTING_READY"
    assert result["trusted_for_downstream_use"] is False


def test_classification_never_depends_solely_on_rag_optimised_existence():
    """No parameter of classify_trust() is 'rag_optimised_exists' at all --
    confirmed by signature inspection, not just behavior, since the risk is
    someone adding such a parameter and wiring it in later without
    noticing this is exactly the anti-pattern being guarded against."""
    import inspect
    sig = inspect.signature(classify_trust)
    assert "rag_optimised_exists" not in sig.parameters
    assert not any("rag_optimised" in p.lower() for p in sig.parameters)


def test_missing_stage6_completion_but_has_4_5c_and_4_5d_is_in_progress_not_certified():
    cp = _ch05_shaped_checkpoint()
    del cp["stage_completions"]["6"]
    cp["pipeline_state"]["corpus_pipeline_completed"] = False
    result = classify_trust(cp, clinical_fidelity_gate=None)
    assert result["trusted_for_downstream_use"] is False
    assert result["classification"] != "CORPUS_TESTING_READY"


def test_gate_not_pass_blocks_certification_even_if_stage6_marked_complete():
    """Belt-and-suspenders: even if a checkpoint somehow shows Stage 6
    COMPLETED, a non-PASS or missing Stage 4.5d gate must not certify."""
    cp = _ch05_shaped_checkpoint()
    result = classify_trust(cp, clinical_fidelity_gate={"verdict": "BLOCKED"})
    assert result["trusted_for_downstream_use"] is False
    result_none = classify_trust(cp, clinical_fidelity_gate=None)
    assert result_none["trusted_for_downstream_use"] is False


def test_result_shape_matches_required_contract():
    result = classify_trust(_ch05_shaped_checkpoint(), clinical_fidelity_gate=_ch05_gate_pass())
    assert set(result.keys()) >= {"classification", "trusted_for_downstream_use", "reasons", "required_action"}
    assert isinstance(result["reasons"], list) and result["reasons"]
    assert isinstance(result["trusted_for_downstream_use"], bool)
