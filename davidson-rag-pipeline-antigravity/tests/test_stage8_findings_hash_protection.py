"""v2.6.5 Part 4: stale-adjudication prevention for Stage 8. Proves the
exact failure this was added to guard against -- decisions recorded
against a findings set computed BEFORE a source_lines parser fix (or any
chunk edit) must never be silently replayed onto the findings set computed
AFTER, since the fix/edit can change which chunks are even flagged.
"""
from pipeline.stages.source_lines_precision import (
    build_findings_set_hash, apply_source_lines_adjudication,
)


def _result(chunk_id, verdict, declared=None, suggested=None):
    return {
        "chunk_id": chunk_id, "verdict": verdict,
        "declared_segments": declared or [], "suggested_segments": suggested or [],
    }


def test_hash_is_deterministic_regardless_of_list_order():
    a = [_result("L2-1", "PRECISE"), _result("L2-2", "UNDER_INCLUSIVE", [(1, 2)], [(1, 3)])]
    b = list(reversed(a))
    assert build_findings_set_hash(a) == build_findings_set_hash(b)


def test_hash_changes_when_a_verdict_changes():
    before = [_result("L2-1", "UNDER_INCLUSIVE", [(1, 2)], [(1, 5)])]
    after = [_result("L2-1", "PRECISE", [(1, 5)], [(1, 5)])]
    assert build_findings_set_hash(before) != build_findings_set_hash(after)


def test_hash_changes_when_declared_segments_change():
    """This is the exact v2.6.5 regression: a parser fix changes
    declared_segments for the SAME chunk_id/verdict without necessarily
    changing the verdict string itself."""
    before = [_result("L2-1", "UNDER_INCLUSIVE", [(1049, 1053)], [(1049, 1053), (1095, 1095)])]
    after = [_result("L2-1", "UNDER_INCLUSIVE", [(1049, 1053), (1095, 1095)], [(1049, 1053), (1095, 1095), (1200, 1200)])]
    assert build_findings_set_hash(before) != build_findings_set_hash(after)


def test_apply_adjudication_without_hash_param_is_unaffected_pre_v2_6_5_behavior():
    results = [_result("L2-1", "UNDER_INCLUSIVE", [(1, 2)], [(1, 3)])]
    updated, errors = apply_source_lines_adjudication(
        results, {"L2-1": {"decision": "CHECKER_FALSE_POSITIVE", "rationale": "verified fine"}}
    )
    assert errors == []
    assert updated[0]["adjudication"]["decision"] == "CHECKER_FALSE_POSITIVE"


def test_apply_adjudication_accepts_matching_hash():
    results = [_result("L2-1", "UNDER_INCLUSIVE", [(1, 2)], [(1, 3)])]
    correct_hash = build_findings_set_hash(results)
    updated, errors = apply_source_lines_adjudication(
        results, {"L2-1": {"decision": "CHECKER_FALSE_POSITIVE", "rationale": "verified fine"}},
        expected_findings_set_sha256=correct_hash,
    )
    assert errors == []
    assert updated[0]["adjudication"]["decision"] == "CHECKER_FALSE_POSITIVE"


def test_apply_adjudication_refuses_stale_hash_after_parser_fix_changes_segments():
    """The core regression test: decisions recorded against the OLD
    (pre-fix) segments must be refused when applied to the NEW (post-fix)
    results, even though the chunk_id and verdict string are identical."""
    stale_results = [_result("L2-1003", "UNDER_INCLUSIVE", [(1049, 1053)], [(1049, 1053), (1095, 1095)])]
    stale_hash = build_findings_set_hash(stale_results)

    fixed_results = [_result("L2-1003", "PRECISE", [(1049, 1053), (1095, 1095)], [(1049, 1053), (1095, 1095)])]

    updated, errors = apply_source_lines_adjudication(
        fixed_results,
        {"L2-1003": {"decision": "HUMAN_CONFIRMED_METADATA_DEFECT", "rationale": "stale decision from before fix"}},
        expected_findings_set_sha256=stale_hash,
    )
    assert errors, "expected the stale-hash mismatch to be refused"
    assert "STALE ADJUDICATION REFUSED" in errors[0]
    assert updated == fixed_results  # unchanged -- all-or-nothing
    assert "adjudication" not in updated[0]


def test_apply_adjudication_all_or_nothing_on_hash_mismatch_even_with_other_valid_decisions():
    results = [_result("L2-1", "PRECISE"), _result("L2-2", "UNDER_INCLUSIVE", [(1, 2)], [(1, 3)])]
    updated, errors = apply_source_lines_adjudication(
        results,
        {"L2-2": {"decision": "CHECKER_FALSE_POSITIVE", "rationale": "fine"}},
        expected_findings_set_sha256="0" * 64,  # deliberately wrong
    )
    assert errors
    assert "adjudication" not in updated[1]
