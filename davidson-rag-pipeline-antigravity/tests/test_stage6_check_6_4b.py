"""Stage 6 Check 6.4b — desired behavior: Stage 6 reads
{PREFIX}_ClinicalFidelityGate.json (correction C), not just
ClinicalFidelityFailures.json, since an unresolved-but-unadjudicated
candidate is not yet classified as a confirmed failure and must not be
treated as equivalent to "clean."
"""
from pipeline.stages.stage_6_validation import check_6_4b, run_stage_6
from pipeline.stages import stage_4_5d_clinical_fidelity as s45d

VALID_RAG = (
    "---\nchunk_id: L2-001\nchunk_level: 2\ndisease_focus: gout\n"
    "coverage_status: complete\n---\n\nbody text"
)


def test_missing_gate_file_is_a_failure_not_pass_by_default():
    failures = check_6_4b(None)
    assert failures and "missing" in failures[0]


def test_gate_pass_with_zero_unresolved_is_clean():
    gate = s45d.build_clinical_fidelity_gate([], s45d.REQUIRED_DETECTORS, "2.6.0", "Ch99")
    failures = check_6_4b(gate)
    assert failures == []


def test_gate_with_unresolved_candidates_fails_even_without_confirmed_corruption():
    """The specific scenario correction C exists to prevent: 3 candidates
    found, none adjudicated yet -> ClinicalFidelityFailures.json (confirmed
    corruptions only) would be EMPTY, but the chapter is not clean."""
    candidates = [s45d._candidate("numeric", f"L2-0{i}", "250", "25", "missing") for i in range(3)]
    gate = s45d.build_clinical_fidelity_gate(candidates, s45d.REQUIRED_DETECTORS, "2.6.0", "Ch99")
    assert gate["unresolved_candidates"] == 3
    failures = check_6_4b(gate)
    assert any("unresolved" in f and "candidate" in f for f in failures)


def test_gate_not_tested_fails():
    ran = [d for d in s45d.REQUIRED_DETECTORS if d != "sequence"]
    gate = s45d.build_clinical_fidelity_gate([], ran, "2.6.0", "Ch99")
    failures = check_6_4b(gate)
    assert any("not tested" in f.lower() for f in failures)


def test_full_stage6_hard_fails_when_4_5d_gate_missing():
    result = run_stage_6(VALID_RAG, coverage_gaps_text_or_none="VERDICT: PASS",
                          clinical_fidelity_gate_or_none=None)
    assert result["verdict"] == "HARD-FAIL"


def test_full_stage6_passes_when_everything_clean():
    gate = s45d.build_clinical_fidelity_gate([], s45d.REQUIRED_DETECTORS, "2.6.0", "Ch99")
    result = run_stage_6(VALID_RAG, coverage_gaps_text_or_none="VERDICT: PASS",
                          clinical_fidelity_gate_or_none=gate)
    assert result["verdict"] == "PASS"
