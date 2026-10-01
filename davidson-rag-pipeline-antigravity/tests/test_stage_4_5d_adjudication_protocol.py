"""Stage 4.5d checkpoint flow (IMPLEMENTATION_MAP.md §3.5) and the
{PREFIX}_ClinicalFidelityGate.json builder (correction C): a chapter cannot
reach COMPLETED while any candidate is unadjudicated or any confirmed
corruption is unresolved.
"""
from pipeline.stages import stage_4_5d_clinical_fidelity as s45d


def _candidate(check="numeric", cid="c1"):
    # v2.6.2: _candidate() no longer assigns candidate_id at creation
    # (collision fix, see test_candidate_id_collision.py) -- assign it here
    # via the real post-processing function so this helper still produces
    # a usable, unique ID the way the real pipeline does.
    c = s45d._candidate(check, f"L2-{cid}", source_value="250", chunk_value="25",
                         kind="missing")
    s45d.assign_candidate_ids([c])
    return c


def test_zero_candidates_gate_passes_and_carries_truth_status():
    gate = s45d.build_clinical_fidelity_gate([], s45d.REQUIRED_DETECTORS, "2.6.0", "Ch99")
    assert gate["verdict"] == "PASS"
    assert gate["unresolved_candidates"] == 0
    assert gate["truth_status"]["semantic_completeness_claimed"] is False
    assert gate["truth_status"]["scope"] == "DEFINED_PATTERN_SET_ONLY"


def test_missing_required_detector_is_not_tested_not_silently_pass():
    ran = [d for d in s45d.REQUIRED_DETECTORS if d != "negation"]
    gate = s45d.build_clinical_fidelity_gate([], ran, "2.6.0", "Ch99")
    assert gate["verdict"] == "NOT_TESTED"
    assert "negation" in gate["detectors_not_tested"]


def test_unadjudicated_candidate_blocks_with_pending_manual_action():
    candidates = [_candidate()]
    gate = s45d.build_clinical_fidelity_gate(candidates, s45d.REQUIRED_DETECTORS, "2.6.0", "Ch99")
    assert gate["verdict"] == "BLOCKED"
    assert gate["unresolved_candidates"] == 1
    assert gate["unresolved_corruptions"] == 0  # not yet classified either way
    action, meta = s45d.decide_checkpoint_action(gate)
    assert action == "pending_manual"


def test_confirmed_corruption_not_yet_fixed_blocks():
    candidates = [_candidate()]
    s45d.apply_adjudication_decisions(candidates, {candidates[0]["candidate_id"]: "confirmed_corruption"})
    gate = s45d.build_clinical_fidelity_gate(candidates, s45d.REQUIRED_DETECTORS, "2.6.0", "Ch99")
    assert gate["verdict"] == "BLOCKED"
    assert gate["unresolved_candidates"] == 0  # WAS adjudicated
    assert gate["unresolved_corruptions"] == 1  # but confirmed + not yet re-verified fixed
    action, meta = s45d.decide_checkpoint_action(gate)
    assert action == "blocked"


def test_confirmed_corruption_fixed_and_reverified_clears_gate():
    candidates = [_candidate()]
    s45d.apply_adjudication_decisions(candidates, {candidates[0]["candidate_id"]: "confirmed_corruption"})
    candidates[0]["re_verified"] = True  # splice-fix applied + re-scanned clean
    gate = s45d.build_clinical_fidelity_gate(candidates, s45d.REQUIRED_DETECTORS, "2.6.0", "Ch99")
    assert gate["verdict"] == "PASS"
    action, meta = s45d.decide_checkpoint_action(gate)
    assert action == "complete"


def test_false_positive_and_legitimate_paraphrase_clear_without_a_fix():
    candidates = [_candidate(cid="a"), _candidate(cid="b")]
    s45d.apply_adjudication_decisions(candidates, {
        candidates[0]["candidate_id"]: "false_positive",
        candidates[1]["candidate_id"]: "legitimate_paraphrase",
    })
    gate = s45d.build_clinical_fidelity_gate(candidates, s45d.REQUIRED_DETECTORS, "2.6.0", "Ch99")
    assert gate["verdict"] == "PASS"


def test_apply_adjudication_decisions_reports_unmatched_ids_loudly():
    candidates = [_candidate()]
    _, unmatched = s45d.apply_adjudication_decisions(candidates, {"does-not-exist": "false_positive"})
    assert unmatched == ["does-not-exist"]


def test_export_for_review_batches_all_candidates():
    candidates = [_candidate(cid=str(i)) for i in range(30)]
    for i, c in enumerate(candidates):
        c["candidate_id"] = f"cand-{i}"
    batches = s45d.export_candidates_for_review(candidates, batch_size=25)
    assert len(batches) == 2
    assert "cand-0" in batches[0]
    assert "cand-29" in batches[1]
