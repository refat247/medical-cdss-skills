"""CP-02 — desired behavior: a stage whose own verdict is a failure/gap must
never route to mark_stage_complete(). Tests the extracted decision modules
directly (pipeline/stages/stage_3_reaudit.py, pipeline/stages/stage_4_5c_coverage.py,
pipeline/stages/stage_4_6_decision.py, pipeline/stages/stage_6_validation.py) since those are
what SKILL.md's thin caller now branches on -- see IMPLEMENTATION_MAP.md's
"Limited Extraction Scope" and correction B (desired-behavior assertions,
RED/GREEN captured externally in PHASE0_PHASE1_REPORT.md).
"""
from pipeline.stages import stage_3_reaudit, stage_4_5c_coverage, stage_4_6_decision, stage_6_validation


# --- Stage 3 -----------------------------------------------------------

def test_stage3_issues_verdict_routes_to_blocked():
    orig = "Clean text with a table row.\n| a | b |\n"
    rep = orig  # identical text but we inject a dead tbl link to force ISSUES
    rep_with_issue = rep + "\n[tbl-1.md](tbl-1.md)\n"
    result = stage_3_reaudit.compute_reaudit(orig, rep_with_issue)
    assert result["verdict"] != "PASSED"
    action, meta = stage_3_reaudit.decide_checkpoint_action(result)
    assert action == "blocked"


def test_stage3_passed_verdict_routes_to_complete():
    orig = "Clean prose with nothing wrong here at all, repeated enough to pass ratio checks. " * 5
    rep = orig
    result = stage_3_reaudit.compute_reaudit(orig, rep)
    assert result["verdict"] == "PASSED"
    action, meta = stage_3_reaudit.decide_checkpoint_action(result)
    assert action == "complete"


# --- Stage 4.5c ----------------------------------------------------------

def _chunk(cid, level, body, topic="T", source_lines=None):
    src = f'source_lines: "{source_lines}"\n' if source_lines else ""
    return f"---\nchunk_id: {cid}\nchunk_level: {level}\ntopic: {topic}\n{src}---\n\n{body}"


def test_stage4_5c_gap_routes_to_blocked():
    l1_body = "This is a full sentence that will never appear in any L2 chunk at all here."
    chunks = _chunk("L1-001", 1, l1_body) + "\n\n" + _chunk("L2-001", 2, "Totally unrelated content.")
    result = stage_4_5c_coverage.compute_coverage_gaps(chunks)
    assert result["verdict"] == "BLOCKING FAIL"
    action, meta = stage_4_5c_coverage.decide_checkpoint_action(result)
    assert action == "blocked"


def test_stage4_5c_full_coverage_routes_to_complete():
    l1_body = "This is a full sentence that will appear in an L2 chunk as well right here."
    chunks = _chunk("L1-001", 1, l1_body) + "\n\n" + _chunk("L2-001", 2, l1_body)
    result = stage_4_5c_coverage.compute_coverage_gaps(chunks)
    assert result["verdict"] == "PASS"
    action, meta = stage_4_5c_coverage.decide_checkpoint_action(result)
    assert action == "complete"


# --- Stage 4.6 (CP-05 lives in the same decision function -- see its own
#     dedicated test file for the degraded-ratio-specific cases) ---------

def test_stage4_6_manual_verification_needed_routes_to_pending():
    action, meta = stage_4_6_decision.decide_checkpoint_action({"needs_manual_verification": True})
    assert action == "pending_manual"


def test_stage4_6_clean_result_routes_to_complete():
    meta_in = {"needs_manual_verification": False, "chunks_reviewed": 20,
               "chunks_unparsed": 0, "chunks_corrected": 3}
    action, meta = stage_4_6_decision.decide_checkpoint_action(meta_in)
    assert action == "complete"


# --- Stage 6 (already correct pre-fix -- kept as the reference pattern,
#     confirmed here so a future edit can't silently regress it) ---------

def test_stage6_hard_fail_routes_to_blocked():
    rag = "---\nchunk_id: L2-001\nchunk_level: 2\n---\n\nbody with no disease_focus"
    result = stage_6_validation.run_stage_6(rag, coverage_gaps_text_or_none=None,
                                             clinical_fidelity_gate_or_none=None)
    assert result["verdict"] == "HARD-FAIL"
    action, meta = stage_6_validation.decide_checkpoint_action(result)
    assert action == "blocked"
