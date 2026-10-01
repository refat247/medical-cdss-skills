"""v2.6.2 — Stage 4.5d candidate ID collision protection.

Audit finding: the pre-v2.6.2 candidate_id format
(`4.5d-{check}-{chunk_id}-{source_or_chunk_value}`) collides whenever two
distinct candidates on the same chunk/check happen to share the same
source_value/chunk_value (e.g. two separate "missing '2'" findings on the
same chunk from two different sentences). New format:
`4.5d-{check}-{chunk_id}-{ordinal}-{stable_hash}`, assigned by
`assign_candidate_ids()` as a post-processing pass over a full candidate
list, guaranteeing uniqueness regardless of how many detector call sites
produced them.
"""
from pipeline.stages import stage_4_5d_clinical_fidelity as s45d


def test_two_identical_value_candidates_same_chunk_and_check_get_unique_ids():
    src = "The dose is 2 mg. Later the dose is 2 mg again in a different sentence."
    chunk = "The dose is mg. Later the dose is mg again in a different sentence."
    # Both "2" tokens missing from chunk -- multiset diff would only ever
    # report ONE "missing 2" record (Counter-based), so construct the
    # collision directly the way the real bug manifested: two candidates
    # with identical check/chunk_id/source_value but different context.
    c1 = s45d._candidate("numeric", "L2-01", source_value="2", chunk_value=None, kind="missing")
    c2 = s45d._candidate("numeric", "L2-01", source_value="2", chunk_value=None, kind="missing")
    candidates = s45d.assign_candidate_ids([c1, c2])
    assert candidates[0]["candidate_id"] != candidates[1]["candidate_id"]


def test_assign_candidate_ids_is_deterministic_given_same_input_order():
    c1 = s45d._candidate("numeric", "L2-01", source_value="2", chunk_value=None, kind="missing")
    c2 = s45d._candidate("numeric", "L2-01", source_value="2", chunk_value=None, kind="missing")
    ids_a = [c["candidate_id"] for c in s45d.assign_candidate_ids([dict(c1), dict(c2)])]
    ids_b = [c["candidate_id"] for c in s45d.assign_candidate_ids([dict(c1), dict(c2)])]
    assert ids_a == ids_b


def test_candidate_id_format_has_five_segments():
    c = s45d._candidate("numeric", "L2-01", source_value="2", chunk_value=None, kind="missing")
    s45d.assign_candidate_ids([c])
    parts = c["candidate_id"].split("-")
    # "4.5d", check, chunk_id(may itself contain '-'), ordinal, hash --
    # check the fixed prefix/suffix rather than a brittle exact split count.
    assert c["candidate_id"].startswith("4.5d-numeric-L2-01-")
    assert parts[-1].isalnum() and len(parts[-1]) >= 6  # stable hash suffix
    assert parts[-2].isdigit()  # ordinal


def test_ordinal_increments_within_same_check_and_chunk_group():
    cands = [
        s45d._candidate("numeric", "L2-01", source_value="2", chunk_value=None, kind="missing"),
        s45d._candidate("numeric", "L2-01", source_value="3", chunk_value=None, kind="missing"),
        s45d._candidate("numeric", "L2-01", source_value="4", chunk_value=None, kind="missing"),
    ]
    s45d.assign_candidate_ids(cands)
    ordinals = [c["candidate_id"].split("-")[-2] for c in cands]
    assert ordinals == ["1", "2", "3"]


def test_ordinal_resets_per_distinct_check_chunk_group():
    cands = [
        s45d._candidate("numeric", "L2-01", source_value="2", chunk_value=None, kind="missing"),
        s45d._candidate("unit", "L2-01", source_value="2 mg", chunk_value=None, kind="missing"),
        s45d._candidate("numeric", "L2-02", source_value="2", chunk_value=None, kind="missing"),
    ]
    s45d.assign_candidate_ids(cands)
    ordinals = [c["candidate_id"].split("-")[-2] for c in cands]
    assert ordinals == ["1", "1", "1"]  # each is the first in its own (check, chunk_id) group


def test_run_all_detectors_for_chunk_returns_globally_unique_ids():
    """Integration-level: a chunk with multiple mismatches on the same
    check must not silently collapse to duplicate IDs when run through the
    real detector pipeline (not just the low-level assign function)."""
    src = "Values: 2, 3, 2, and 3 again, plus a stray 2 for good measure."
    chunk = "Values: X, X, X, and X again, plus a stray X for good measure."
    candidates, _ = s45d.run_all_detectors_for_chunk(src, chunk, "L2-42")
    ids = [c["candidate_id"] for c in candidates]
    assert len(ids) == len(set(ids)), f"duplicate candidate_id(s) found: {ids}"


def test_migrate_legacy_candidate_ids_preserves_recorded_decisions():
    """Existing adjudication files (old 4-segment ID format, decisions
    already recorded) must not have their decisions silently invalidated
    by a re-ID pass -- decisions live on the record itself, not keyed
    externally by ID, so migration only touches the id field."""
    legacy = {
        "candidate_id": "4.5d-numeric-L2-038-2",  # old format
        "check": "numeric", "chunk_id": "L2-038",
        "source_value": "2", "chunk_value": None, "kind": "missing",
        "severity": "RESOLVED_NOT_A_CORRUPTION", "status_label": "VERIFIED",
        "decision": "false_positive",
    }
    migrated = s45d.migrate_legacy_candidate_ids([dict(legacy)])
    assert migrated[0]["decision"] == "false_positive"
    assert migrated[0]["status_label"] == "VERIFIED"
    assert migrated[0]["severity"] == "RESOLVED_NOT_A_CORRUPTION"
    assert migrated[0]["candidate_id"] != legacy["candidate_id"]  # re-IDed to new format
    assert migrated[0]["candidate_id"].startswith("4.5d-numeric-L2-038-")
