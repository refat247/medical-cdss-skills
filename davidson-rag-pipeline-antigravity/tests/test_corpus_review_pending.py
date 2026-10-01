"""v2.6.4 -- Corpus-Scale Gate Closure, MUST-FIX #3 (part 1): classify_trust()
gains a CORPUS_REVIEW_PENDING classification so an untested or unresolved
source-lines mapping cannot receive CORPUS_TESTING_READY, and a
protection_marker_present safety field that never influences the
classification decision itself.
"""
from pipeline.stages.corpus_trust import classify_trust, CLASSIFICATIONS


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


def _gate_pass():
    return {"verdict": "PASS", "unresolved_candidates": 0, "unresolved_corruptions": 0}


def test_corpus_review_pending_is_a_known_classification():
    assert "CORPUS_REVIEW_PENDING" in CLASSIFICATIONS


def test_omitting_precision_summary_now_demotes_to_corpus_review_pending():
    """v2.6.6 (Fail-Closed Finalization) supersedes the pre-v2.6.6 behavior
    this test used to assert ("omitting source_lines_precision_summary
    preserves CORPUS_TESTING_READY"). That was the exact fail-open shape of
    the Chapter 11 defect generalized to Stage 8: a chapter reaching the
    corpus_completed+gate_pass milestone must not be certified while Stage 8
    evidence is simply absent from the classification call. Omitting
    source_lines_precision_summary (and every other v2.6.6 mandatory
    parameter) now demotes to CORPUS_REVIEW_PENDING -- see
    V2_6_6_FAIL_CLOSED_FINALIZATION_REPORT.md."""
    result = classify_trust(_ch05_shaped_checkpoint(), clinical_fidelity_gate=_gate_pass())
    assert result["classification"] == "CORPUS_REVIEW_PENDING"
    assert result["trusted_for_downstream_use"] is False


def test_untested_precision_demotes_to_corpus_review_pending():
    result = classify_trust(
        _ch05_shaped_checkpoint(), clinical_fidelity_gate=_gate_pass(),
        source_lines_precision_summary={"tested": False, "unresolved_count": None},
    )
    assert result["classification"] == "CORPUS_REVIEW_PENDING"
    assert result["trusted_for_downstream_use"] is False


def test_tested_with_unresolved_findings_demotes_to_corpus_review_pending():
    result = classify_trust(
        _ch05_shaped_checkpoint(), clinical_fidelity_gate=_gate_pass(),
        source_lines_precision_summary={"tested": True, "unresolved_count": 3},
    )
    assert result["classification"] == "CORPUS_REVIEW_PENDING"
    assert result["trusted_for_downstream_use"] is False


def test_tested_with_zero_unresolved_findings_reaches_corpus_testing_ready():
    """v2.6.6: Stage 4.6/4.7 evidence is now also mandatory, so the full
    happy-path evidence set is supplied here (not just Stage 8) to isolate
    what this test is actually about -- clean source-lines precision."""
    result = classify_trust(
        _ch05_shaped_checkpoint(), clinical_fidelity_gate=_gate_pass(),
        source_lines_precision_summary={"tested": True, "unresolved_count": 0},
        stage_4_6_review_status="COMPLETED",
        stage_4_6_chunks_reviewed=10, stage_4_6_total_flagged=10,
        unresolved_completeness_clusters=0,
    )
    assert result["classification"] == "CORPUS_TESTING_READY"
    assert result["trusted_for_downstream_use"] is True


def test_protection_marker_present_is_disclosed_but_never_affects_classification():
    result_with_marker = classify_trust(
        _ch05_shaped_checkpoint(), clinical_fidelity_gate=_gate_pass(),
        protection_marker={"chapter": "05", "production_output_protected": True},
    )
    result_without_marker = classify_trust(
        _ch05_shaped_checkpoint(), clinical_fidelity_gate=_gate_pass(),
        protection_marker=None,
    )
    assert result_with_marker["protection_marker_present"] is True
    assert result_without_marker["protection_marker_present"] is False
    # Same classification either way -- the marker is disclosure-only.
    assert result_with_marker["classification"] == result_without_marker["classification"]
    assert result_with_marker["trusted_for_downstream_use"] == result_without_marker["trusted_for_downstream_use"]


def test_legacy_classifications_also_disclose_protection_marker_present():
    result = classify_trust(checkpoint=None, has_stage6_validation_file=False,
                             has_coverage_gaps_file=False, protection_marker=None)
    assert "protection_marker_present" in result
    assert result["protection_marker_present"] is False
