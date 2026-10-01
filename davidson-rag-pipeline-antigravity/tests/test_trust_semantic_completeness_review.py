"""v2.6.5 Part 6: the trust classifier must account for unresolved
mandatory review in Stage 4.6 (semantic-type) and Stage 4.7 (completeness)
before granting CORPUS_TESTING_READY. This is the exact gap that let
Chapter 14 reach trusted_for_downstream_use=True with 238/283 Stage 4.6
candidates and 18/35 Stage 4.7 clusters unreviewed.
"""
from pipeline.stages.corpus_trust import classify_trust


def _ready_checkpoint():
    return {
        "stage_completions": {"4.5c": {"status": "COMPLETED"}, "4.5d": {"status": "COMPLETED"}},
        "pipeline_state": {"corpus_pipeline_completed": True},
    }


def _passing_gate():
    return {"verdict": "PASS"}


def _clean_precision():
    return {"tested": True, "unresolved_count": 0}


def test_omitting_stage_4_6_and_4_7_now_demotes_to_corpus_review_pending():
    """v2.6.6 (Fail-Closed Finalization) supersedes the pre-v2.6.6 behavior
    this test used to assert ("omitting the new params entirely preserves
    the exact pre-v2.6.5 CORPUS_TESTING_READY behavior"). That was exactly
    the Chapter 11 defect's fail-open shape generalized: a chapter that
    reached corpus_completed+gate_pass must not be certified merely because
    Stage 4.6/4.7 evidence wasn't supplied to the classification call.
    Omitting them now demotes to CORPUS_REVIEW_PENDING."""
    r = classify_trust(_ready_checkpoint(), _passing_gate(),
                        source_lines_precision_summary=_clean_precision())
    assert r["classification"] == "CORPUS_REVIEW_PENDING"
    assert r["trusted_for_downstream_use"] is False
    # Display booleans retain their None-if-omitted semantics (distinct from
    # the mandatory classification-gate decision above).
    assert r["semantic_metadata_review_complete"] is None
    assert r["completeness_review_complete"] is None
    assert r["retrieval_ready"] is False


def test_partial_stage_4_6_review_blocks_corpus_testing_ready():
    """The Chapter 14 regression: Stage 4.6 status IN_PROGRESS (partial
    review) must demote to CORPUS_REVIEW_PENDING, not stay READY."""
    r = classify_trust(_ready_checkpoint(), _passing_gate(),
                        source_lines_precision_summary=_clean_precision(),
                        stage_4_6_review_status="IN_PROGRESS")
    assert r["classification"] == "CORPUS_REVIEW_PENDING"
    assert r["trusted_for_downstream_use"] is False
    assert r["semantic_metadata_review_complete"] is False
    assert any("Stage 4.6" in reason for reason in r["reasons"])


def test_completed_stage_4_6_review_does_not_block():
    r = classify_trust(_ready_checkpoint(), _passing_gate(),
                        source_lines_precision_summary=_clean_precision(),
                        stage_4_6_review_status="COMPLETED",
                        stage_4_6_chunks_reviewed=10, stage_4_6_total_flagged=10,
                        unresolved_completeness_clusters=0)
    assert r["classification"] == "CORPUS_TESTING_READY"
    assert r["semantic_metadata_review_complete"] is True


def test_unresolved_completeness_clusters_blocks_corpus_testing_ready():
    """The Chapter 14 regression: 18 undetermined SCATTERED clusters must
    demote to CORPUS_REVIEW_PENDING."""
    r = classify_trust(_ready_checkpoint(), _passing_gate(),
                        source_lines_precision_summary=_clean_precision(),
                        stage_4_6_review_status="COMPLETED",
                        stage_4_6_chunks_reviewed=10, stage_4_6_total_flagged=10,
                        unresolved_completeness_clusters=18)
    assert r["classification"] == "CORPUS_REVIEW_PENDING"
    assert r["trusted_for_downstream_use"] is False
    assert r["completeness_review_complete"] is False
    assert any("18" in reason for reason in r["reasons"])


def test_zero_unresolved_completeness_clusters_does_not_block():
    r = classify_trust(_ready_checkpoint(), _passing_gate(),
                        source_lines_precision_summary=_clean_precision(),
                        stage_4_6_review_status="COMPLETED",
                        stage_4_6_chunks_reviewed=10, stage_4_6_total_flagged=10,
                        unresolved_completeness_clusters=0)
    assert r["classification"] == "CORPUS_TESTING_READY"
    assert r["completeness_review_complete"] is True


def test_both_stage_4_6_and_4_7_complete_reaches_corpus_testing_ready():
    r = classify_trust(_ready_checkpoint(), _passing_gate(),
                        source_lines_precision_summary=_clean_precision(),
                        stage_4_6_review_status="COMPLETED",
                        stage_4_6_chunks_reviewed=10, stage_4_6_total_flagged=10,
                        unresolved_completeness_clusters=0)
    assert r["classification"] == "CORPUS_TESTING_READY"
    assert r["trusted_for_downstream_use"] is True
    assert r["semantic_metadata_review_complete"] is True
    assert r["completeness_review_complete"] is True


def test_retrieval_ready_is_always_false():
    """This pipeline does not implement retrieval -- never inferred True."""
    r = classify_trust(_ready_checkpoint(), _passing_gate(),
                        source_lines_precision_summary=_clean_precision(),
                        stage_4_6_review_status="COMPLETED",
                        stage_4_6_chunks_reviewed=10, stage_4_6_total_flagged=10,
                        unresolved_completeness_clusters=0)
    assert r["retrieval_ready"] is False


def test_missing_stage_4_6_counts_blocks_even_with_status_completed():
    """v2.6.6: status=='COMPLETED' alone is not sufficient -- chunks_reviewed
    and total_flagged must also be explicitly present and well-formed."""
    r = classify_trust(_ready_checkpoint(), _passing_gate(),
                        source_lines_precision_summary=_clean_precision(),
                        stage_4_6_review_status="COMPLETED",
                        unresolved_completeness_clusters=0)
    assert r["classification"] == "CORPUS_REVIEW_PENDING"
    assert r["trusted_for_downstream_use"] is False
    assert any("4.6" in reason for reason in r["reasons"])


def test_stage_4_6_chunks_reviewed_less_than_total_flagged_blocks():
    """v2.6.6: the Chapter 14 pre-repair shape -- status=='COMPLETED' but a
    genuinely partial review (chunks_reviewed < total_flagged)."""
    r = classify_trust(_ready_checkpoint(), _passing_gate(),
                        source_lines_precision_summary=_clean_precision(),
                        stage_4_6_review_status="COMPLETED",
                        stage_4_6_chunks_reviewed=45, stage_4_6_total_flagged=283,
                        unresolved_completeness_clusters=0)
    assert r["classification"] == "CORPUS_REVIEW_PENDING"
    assert r["trusted_for_downstream_use"] is False
    assert any("45" in reason and "283" in reason for reason in r["reasons"])
