"""Regression tests for defects found in the second audit sweep (see skill_audits/SECOND_SWEEP.md).
Each test pins one confirmed defect; names carry the finding id."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from pipeline.stages import stage_6_validation as s6
from pipeline.stages.stage_4_5d_clinical_fidelity import REQUIRED_DETECTORS

GOOD_GATE = {"verdict": "PASS", "unresolved_candidates": 0, "unresolved_corruptions": 0,
             "detectors_run": list(REQUIRED_DETECTORS), "detectors_not_tested": []}

GOOD_CHUNK = ("---\nchunk_id: L2-001\nchunk_level: 2\ndisease_focus: asthma\ncoverage_status: complete\n---\n\n"
              "Body text.\n")


# ---------- 1.1 Stage 6 must not pass when there is nothing to validate ----------
@pytest.mark.parametrize("text", ["", "hello world", "no chunks here at all\n"])
def test_1_1_stage6_fails_on_zero_chunks(text):
    r = s6.run_stage_6(text, "ok", GOOD_GATE)
    assert r["verdict"] == "HARD-FAIL"
    assert r["chunks_checked"] == 0
    assert any("no chunk" in f.lower() for f in r["failures"])


def test_1_1_stage6_still_passes_a_good_file():
    assert s6.run_stage_6(GOOD_CHUNK, "ok", GOOD_GATE)["verdict"] == "PASS"


# ---------- 1.29 Stage 6 field checks must read frontmatter only ----------
def test_1_29_disease_focus_in_body_does_not_satisfy_frontmatter():
    chunk = ("---\nchunk_id: L2-001\nchunk_level: 2\ncoverage_status: complete\n---\n\n"
             "disease_focus: asthma\n")
    fails, _ = s6.check_6_1_6_2(chunk)
    assert any("missing disease_focus" in f for f in fails)


def test_1_29_blocking_fail_is_case_insensitive():
    assert s6.check_6_4("Blocking Fail: 3 gaps") != []


def test_1_29_gate_must_list_required_detectors_as_run():
    gate = dict(GOOD_GATE, detectors_run=[])
    r = s6.run_stage_6(GOOD_CHUNK, "ok", gate)
    assert r["verdict"] == "HARD-FAIL"
    assert any("not run" in f.lower() or "detectors_run" in f for f in r["failures"])


# ---------- 1.3 Stage 4B must not NFKC-normalise clinical text ----------
from pipeline.stages.stage_4_parse import sanitize_chunk_text


@pytest.mark.parametrize("s", ["Platelets 10⁹/L", "BSA 1.7 m²", "5 µg", "½ tablet", "CO₂ 24 mmol/L", "10⁶ IU", "℃"])
def test_1_3_clinical_glyphs_survive_stage4b_sanitizer(s):
    assert sanitize_chunk_text(s) == s


def test_1_3_ligatures_and_invisibles_are_still_cleaned():
    assert sanitize_chunk_text("ﬁrst line​﻿") == "first line"


# ---------- 1.5 / 1.6 / 1.7 Stage 2 OCR cleanup must not destroy clinical text ----------
from pipeline.stages.stage_2_repair import repair_stage2
from pipeline.stages.stage_3_reaudit import compute_reaudit


def _s2(text):
    out = repair_stage2(text)
    return out[0] if isinstance(out, tuple) else out


def test_1_5_running_header_does_not_eat_next_paragraph():
    out = _s2("## Sec\n5 • HYPERTENSION\n\nACE inhibitors are first line for 10 mg daily.\n")
    assert "ACE inhibitors are first line" in out
    assert "<!-- page: 5 -->" in out


def test_1_5_running_header_does_not_eat_drug_name():
    out = _s2("## Sec\n3 • NaCl 0.9% infusion at 100 mL/h\n")
    assert "NaCl 0.9% infusion at 100 mL/h" in out


def test_1_6_inline_number_line_is_not_a_page_marker():
    out = _s2("## Dose\nGive aspirin\n300\nmg stat\n")
    assert "\n300\n" in out and "page: 300" not in out


def test_1_6_isolated_number_is_still_a_page_marker():
    out = _s2("## Sec\ntext\n\n42\n\nmore text\n")
    assert "<!-- page: 42 -->" in out


def test_1_7_toc_strip_keeps_h1():
    out = _s2("# Vitamin B12\n\nContents 3\nIntro ........ 5\n\n## Section\ntext\n")
    assert "# Vitamin B12" in out
    assert "Intro ........ 5" not in out


def test_1_5_stage3_agrees_with_stage2_on_clean_text():
    src = "# Title\n\n## Sec\n5 • HYPERTENSION\n\nACE inhibitors 3 • NaCl 0.9%\n"
    r = compute_reaudit(src, _s2(src))
    assert r["verdict"].startswith("PASS") or r["verdict"] in ("PASSED", "PASS"), r


# ---------- 1.2 / 1.4 / 1.29 Stage 4.5d detectors ----------
from pipeline.stages import stage_4_5d_clinical_fidelity as s45


def _cands(src, chunk):
    c, _ = s45.run_all_detectors_for_chunk(src, chunk, "L2-1")
    return c


@pytest.mark.parametrize("src,chunk", [
    ("Gentamicin 5 mg/kg once daily.", "Gentamicin 5 mg once daily."),
    ("Glucose 7 mg/dL", "Glucose 7 mg/L"),
    ("Give 10 mg/kg", "Give 10 mg/m2"),
    ("Target 50% reduction", "Target 50 reduction"),
    ("Give 50 µg", "Give 50 µg/kg"),
    ("5 mcg/kg/min", "5 mcg/min"),
    ("Na 135 mmol/L", "Na 135 mmol"),
    ("eGFR 30 mL/min/1.73m2", "eGFR 30 mL/min"),
])
def test_1_2_unit_changes_are_detected(src, chunk):
    assert _cands(src, chunk), f"unit change not detected: {src!r} -> {chunk!r}"


@pytest.mark.parametrize("src,chunk", [
    ("Give 5 mg/kg daily", "Give 5 mg/kg daily"),
    ("Give 5mg daily", "Give 5 mg daily"),
    ("Give 50 µg", "Give 50 mcg"),
    ("Target 50% reduction", "Target 50 % reduction"),
    ("BSA 1.73 m2", "BSA 1.73 m²"),
])
def test_1_2_equivalent_unit_spellings_do_not_raise_candidates(src, chunk):
    assert not [c for c in _cands(src, chunk) if c["check"] in ("unit", "dose")], (src, chunk)


@pytest.mark.parametrize("src,chunk", [
    ("Drug A is contraindicated in pregnancy. Drug B is permitted.", "Drug A is permitted in pregnancy. Drug B is permitted."),
    ("Antibiotics are not indicated for viral URTI. Steroids are indicated for croup.",
     "Antibiotics are indicated for viral URTI. Steroids are indicated for croup."),
    ("Do not give aspirin to children.", "Give aspirin to children."),
    ("Avoid NSAIDs in renal failure.", "NSAIDs in renal failure."),
    ("There is no role for steroids.", "There is a role for steroids."),
    ("Lactate increases in sepsis. Bicarbonate decreases.", "Lactate decreases in sepsis. Bicarbonate decreases."),
])
def test_1_4_sentence_level_negation_and_polarity_flips_are_detected(src, chunk):
    assert [c for c in _cands(src, chunk) if c["check"] in ("negation", "polarity")], (src, chunk)


@pytest.mark.parametrize("src,chunk", [
    ("Do not give aspirin to children.", "Aspirin should not be given to children."),
    ("Antibiotics are not indicated for viral URTI.", "Antibiotics are not indicated for viral URTI."),
])
def test_1_4_preserved_negation_is_not_flagged(src, chunk):
    assert not [c for c in _cands(src, chunk) if c["check"] in ("negation", "polarity")], (src, chunk)


@pytest.mark.parametrize("src,chunk,check", [
    ("eGFR below 30", "eGFR above 30", "inequality"),
    ("Dose 5−10 mg", "Dose 5 mg", "range"),
    ("Take four times daily", "Take twice daily", "frequency"),
    ("Take qds", "Take bd", "frequency"),
    ("for 7 d", "for 14 d", "duration"),
])
def test_1_29_detector_vocabulary_gaps(src, chunk, check):
    assert [c for c in _cands(src, chunk) if c["check"] == check], (src, chunk)


# ---------- 1.8 Stage 4.6 offline adjudicator must not relabel from body regexes ----------
from pipeline import stage_4_6_gemini_verification as s46


def _chunk46(cid, stype, topic, body):
    return (f"---\nchunk_id: {cid}\nchunk_level: 2\nsemantic_type: {stype}\ntopic_primary: \"{topic}\"\n"
            f"disease_focus: x\ncoverage_status: complete\n---\n\n{body}\n\n")


def test_1_8_offline_adjudicator_leaves_correct_types_alone():
    chunks = (_chunk46("L2-01", "diagnostic_criteria", "Diagnosis of hypothyroidism",
                       "Hypothyroidism is defined as TSH above range. Treatment is levothyroxine.") +
              _chunk46("L2-02", "clinical_feature", "Presentation", "Patients present with fatigue; some take 5 mg of a drug."))
    new_text, meta = s46.offline_adjudicate_all(chunks, levels=(2,))
    assert "semantic_type: diagnostic_criteria" in new_text
    assert "semantic_type: clinical_feature" in new_text
    assert meta["chunks_corrected"] == 0


def test_1_8_offline_method_is_declared_not_independent():
    _, meta = s46.offline_adjudicate_all(_chunk46("L2-01", "clinical_feature", "Presentation", "text"), levels=(2,))
    assert meta["verification_method"].startswith("offline")
    assert meta.get("independent_verification") is False


# ---------- 1.16 execute_stage 4.5d pending_manual must not raise UnboundLocalError ----------
def test_1_16_execute_stage_4_5d_pending_manual_records_in_progress(tmp_path, monkeypatch):
    import pipeline.run_stage as rs
    import scripts.maintenance.run_stage_4_5d as m
    from pipeline.stages import stage_4_5d_clinical_fidelity as s45d
    calls = {}
    monkeypatch.setattr(m, "run_stage_4_5d", lambda out, prefix: (
        {"verdict": "BLOCKED", "candidate_count": 2, "unresolved_candidates": ["c1"], "detectors_run": ["d"]}, []))
    monkeypatch.setattr(s45d, "decide_checkpoint_action", lambda gate: ("pending_manual", {}))
    monkeypatch.setattr(rs, "load_checkpoint", lambda out, prefix: ({}, "x.json"))
    monkeypatch.setattr(rs, "should_run_stage", lambda c, s: True)
    monkeypatch.setattr(rs, "sync_chapter_assets", lambda *a, **k: None)
    monkeypatch.setattr(rs, "mark_stage_in_progress", lambda *a, **k: calls.setdefault("in_progress", (a, k)))
    src = tmp_path / "ch.md"; src.write_text("x")
    r = rs.execute_stage("4.5d", str(src), out_dir=str(tmp_path / "o"), prefix="p", force=True)
    assert r["status"] == "PENDING_MANUAL"
    assert "in_progress" in calls


# ---------- 1.9 invalid manual corrections must be counted as unparsed, not as reviews ----------
@pytest.mark.parametrize("mod", ["stage_4_6_gemini_verification", "stage_4_6_sonnet_verification"])
def test_1_9_unknown_ids_and_invalid_types_are_unparsed(mod):
    import importlib
    m = importlib.import_module(f"pipeline.{mod}")
    chunks = _chunk46("L2-1", "clinical_feature", "Presentation", "text")
    _, meta = m.apply_manual_corrections(chunks, {"L2-99": "drug_info", "L2-1": "drug_infoo"})
    assert meta["chunks_unparsed"] == 2
    assert meta["chunks_corrected"] == 0


@pytest.mark.parametrize("mod", ["stage_4_6_gemini_verification", "stage_4_6_sonnet_verification"])
def test_1_9_valid_confirmation_and_correction_still_work(mod):
    import importlib
    m = importlib.import_module(f"pipeline.{mod}")
    chunks = _chunk46("L2-1", "clinical_feature", "Presentation", "text") + _chunk46("L2-2", "clinical_feature", "X", "t")
    text, meta = m.apply_manual_corrections(chunks, {"L2-1": "clinical_feature", "L2-2": "drug_info"})
    assert meta["chunks_unparsed"] == 0 and meta["chunks_corrected"] == 1
    assert "semantic_type: drug_info" in text


# ---------- 1.13 manifest entries must match the current scan, not just the header hash ----------
from pipeline.stages import adjudication_manifest as am


def test_1_13_tampered_manifest_entry_values_are_rejected():
    cur = [{"candidate_id": "4.5d-numeric-L2-1-1-abc", "check": "numeric", "chunk_id": "L2-1",
            "kind": "missing", "source_value": "5", "chunk_value": None}]
    manifest = {
        "schema_version": am.SCHEMA_VERSION, "source_sha256": "s", "chunks_sha256": "c",
        "candidate_set_sha256": am.build_candidate_set_hash(cur),
        "candidates": [{"candidate_id": "4.5d-numeric-L2-1-1-abc", "detector": "numeric", "chunk_id": "L2-1",
                        "mismatch_kind": "missing", "source_value": "ZZZ", "chunk_value": "WHATEVER",
                        "decision": "false_positive", "rationale": "ok"}],
    }
    for f in am.REQUIRED_MANIFEST_FIELDS:
        manifest.setdefault(f, "x")
    r = am.validate_manifest(manifest, source_sha256="s", chunks_sha256="c", current_candidates=cur)
    assert r["valid"] is False
    assert any("identity" in e or "tamper" in e.lower() for e in r["errors"])


# ---------- 1.14 invariants checker must not report success when it checked nothing ----------
from pipeline import verify_trusted_corpus_invariants as vtci


def test_1_14_nonexistent_corpus_root_is_an_error(tmp_path):
    assert vtci.main([str(tmp_path / "does-not-exist")]) != 0


def test_1_14_missing_ledger_is_an_error(tmp_path):
    assert vtci.main([str(tmp_path)]) != 0


# ---------- 1.12 a BLOCKED/FAILED/IN_PROGRESS gating stage must withdraw trust ----------
from pipeline.stages.corpus_trust import classify_trust
from tests.test_corpus_trust import _ch05_shaped_checkpoint, _ch05_gate_pass


def _classify(cp):
    return classify_trust(
        cp, clinical_fidelity_gate=_ch05_gate_pass(),
        source_lines_precision_summary={"tested": True, "unresolved_count": 0},
        stage_4_6_review_status="COMPLETED", stage_4_6_chunks_reviewed=10, stage_4_6_total_flagged=10,
        unresolved_completeness_clusters=0)


def test_1_12_baseline_is_ready():
    assert _classify(_ch05_shaped_checkpoint())["trusted_for_downstream_use"] is True


@pytest.mark.parametrize("stage,status", [("6", "BLOCKED"), ("4.5c", "BLOCKED"), ("4.5d", "FAILED"), ("4.5", "BLOCKED"),
                                           ("6", "IN_PROGRESS")])
def test_1_12_gating_stage_not_completed_withdraws_trust(stage, status):
    cp = _ch05_shaped_checkpoint()
    cp["stage_completions"][stage] = {"status": status}
    r = _classify(cp)
    assert r["trusted_for_downstream_use"] is False
    assert any(stage in x for x in r["reasons"])


# ---------- 1.10 Stage 4.5b must compare dose VALUES, not count regex hits ----------
from pipeline.stages import stage_4_5b_pharma as s45b


def _run_45b(tmp_path, monkeypatch, source, chunks):
    monkeypatch.setattr(s45b, "load_checkpoint", lambda o, p: ({}, "x.json"))
    monkeypatch.setattr(s45b, "should_run_stage", lambda c, s: True)
    monkeypatch.setattr(s45b, "mark_stage_complete", lambda *a, **k: None)
    rep, ch = tmp_path / "rep.md", tmp_path / "chunks.md"
    rep.write_text(source, encoding="utf-8"); ch.write_text(chunks, encoding="utf-8")
    return s45b.run_stage_4_5b(str(rep), str(ch), str(tmp_path), "P")


def _l2(body):
    return f"---\nchunk_id: L2-1\nchunk_level: 2\nsemantic_type: drug_info\n---\n\n{body}\n"


def test_1_10_changed_dose_value_is_flagged(tmp_path, monkeypatch):
    r = _run_45b(tmp_path, monkeypatch, "Amoxicillin 500 mg tds for 50% reduction", _l2("Amoxicillin 5000 mg tds for 50% reduction"))
    assert "WARN" in r["verdict"] and "changed" in r["verdict"].lower()


def test_1_10_unit_swap_is_flagged(tmp_path, monkeypatch):
    r = _run_45b(tmp_path, monkeypatch, "Gentamicin 5 mg/kg once daily", _l2("Gentamicin 5 mg once daily"))
    assert "WARN" in r["verdict"]


def test_1_10_l1_copy_does_not_double_count(tmp_path, monkeypatch):
    chunks = ("---\nchunk_id: L1-1\nchunk_level: 1\n---\n\nGive 500 mg daily and 600 mg nocte.\n\n"
              + _l2("Give 500 mg daily."))
    r = _run_45b(tmp_path, monkeypatch, "Give 500 mg daily and 600 mg nocte.", chunks)
    assert "WARN" in r["verdict"]          # the 600 mg is absent from the only L2 chunk


def test_1_10_identical_content_is_cleared(tmp_path, monkeypatch):
    txt = "Give 500 mg daily; target 50% reduction; eGFR<30."
    assert _run_45b(tmp_path, monkeypatch, txt, _l2(txt))["verdict"] == "CLEARED"


# ---------- 1.10b Stage 7 dosing_preservation must not read a changed dose as 100% ----------
def test_1_10_stage7_dose_change_does_not_score_perfect(tmp_path, monkeypatch):
    from pipeline.stages import stage_7_scorecard as s7
    monkeypatch.setattr(s7, "load_checkpoint", lambda o, p: ({}, "x.json"))
    monkeypatch.setattr(s7, "should_run_stage", lambda c, s: True)
    monkeypatch.setattr(s7, "mark_stage_complete", lambda *a, **k: None)
    rep, rag = tmp_path / "rep.md", tmp_path / "rag.md"
    rep.write_text("Give 5 mg daily.", encoding="utf-8"); rag.write_text("Give 50 mg daily.", encoding="utf-8")
    res = s7.run_stage_7(str(rep), str(rag), str(tmp_path), "P")
    val = res["dimensions"]["dosing_preservation"]["score"]
    assert val is not None and val < 1.0


# ---------- 1.11 Stage 4.5 verbatim check must cover the whole chunk body ----------
from pipeline.stages import stage_4_5_spotcheck as sc45


def _run_45(tmp_path, monkeypatch, source, chunks):
    monkeypatch.setattr(sc45, "load_checkpoint", lambda o, p: ({}, "x.json"))
    monkeypatch.setattr(sc45, "should_run_stage", lambda c, s: True)
    for fn in ("mark_stage_complete", "mark_stage_blocked"):
        monkeypatch.setattr(sc45, fn, lambda *a, **k: None)
    rep, ch = tmp_path / "rep.md", tmp_path / "chunks.md"
    rep.write_text(source, encoding="utf-8"); ch.write_text(chunks, encoding="utf-8")
    return sc45.run_stage_4_5(str(rep), str(ch), str(tmp_path), "P")


SRC = ("## Heparin\n\nStart unfractionated heparin with an 80 U/kg bolus and then 18 U/kg/h infusion.\n"
       "Check the aPTT every six hours until stable.\nThe maximum dose is 4 g per day in adults.\n")


def _c(body):
    return f"---\nchunk_id: L2-1\nchunk_level: 2\n---\n\n{body}\n"


def test_1_11_verbatim_chunk_passes(tmp_path, monkeypatch):
    assert _run_45(tmp_path, monkeypatch, SRC, _c(SRC.split("\n\n", 1)[1].strip()))["verdict"] == "CLEARED"


def test_1_11_late_dose_change_fails(tmp_path, monkeypatch):
    body = SRC.split("\n\n", 1)[1].strip().replace("4 g per day", "40 g per day")
    r = _run_45(tmp_path, monkeypatch, SRC, _c(body))
    assert r["verdict"] == "FAIL" and "L2-1" in r["failed_ids"]


def test_1_11_zero_l2_chunks_is_not_cleared(tmp_path, monkeypatch):
    assert _run_45(tmp_path, monkeypatch, SRC, "no chunks at all")["verdict"] == "FAIL"


def test_1_11_short_chunk_with_a_number_is_still_checked(tmp_path, monkeypatch):
    r = _run_45(tmp_path, monkeypatch, "Give 5 mg stat.\n", _c("Give 50 mg stat."))
    assert r["verdict"] == "FAIL"


# ---------- 1.21 one splitter for every stage ----------
import re as _re
from pipeline.stages.chunk_blocks import split_chunk_blocks, block_body

_OLD = r"(---\nchunk_id:.*?\n---\n.*?)(?=\n---\nchunk_id:|\Z)"
_WELL = ("---\nchunk_id: L2-1\nchunk_level: 2\n---\n\nBody one.\n\n---\nchunk_id: L2-2\nchunk_level: 2\n---\n\nBody two.\n")


def test_1_21_equals_the_old_regex_on_well_formed_input():
    assert split_chunk_blocks(_WELL) == _re.findall(_OLD, _WELL, _re.DOTALL)


def test_1_21_keeps_a_final_empty_body_chunk_without_trailing_newline():
    text = _WELL + "\n---\nchunk_id: L2-3\nchunk_level: 2\ncoverage_status: gap\n---"
    assert len(_re.findall(_OLD, text, _re.DOTALL)) == 2          # the old regex loses it
    assert [b.split("\n")[1] for b in split_chunk_blocks(text)] == ["chunk_id: L2-1", "chunk_id: L2-2", "chunk_id: L2-3"]


def test_1_21_body_keeps_horizontal_rules_inside_the_body():
    text = "---\nchunk_id: L2-1\n---\n\nabove\n\n---\n\nbelow\n"
    assert "below" in block_body(split_chunk_blocks(text)[0])


def test_1_21_no_stage_still_uses_the_old_regex():
    import glob
    offenders = []
    for f in glob.glob("pipeline/**/*.py", recursive=True) + glob.glob("scripts/**/*.py", recursive=True):
        src = open(f, encoding="utf-8").read()
        if "(?=\\n---\\nchunk_id:|\\Z)" in src and "chapter_repairs" not in f and not f.endswith(("stage_6_validation.py", "chunk_blocks.py")):
            offenders.append(f)
    assert not offenders, offenders


# ---------- 1.18 / 1.30(26) zero chunks must not clear or complete a stage ----------
from pipeline.stages.stage_4_5c_coverage import compute_coverage_gaps, decide_checkpoint_action as d45c


def test_1_18_stage_4_5c_blocks_when_there_are_no_l1_chunks():
    r = compute_coverage_gaps("no chunks here")
    assert r["verdict"] == "BLOCKING FAIL" and d45c(r)[0] == "blocked"


def test_1_26_stage_4_5c_reads_whole_body_even_with_a_horizontal_rule():
    l1 = ("---\nchunk_id: L1-1\nchunk_level: 1\ntopic: T\n---\n\nFirst sentence here is long enough to count.\n\n---\n\n"
          "Second sentence after a rule is also long enough.\n")
    l2 = ("---\nchunk_id: L2-1\nchunk_level: 2\n---\n\nFirst sentence here is long enough to count.\n")
    r = compute_coverage_gaps(l1 + "\n" + l2)
    assert r["gaps"], "the sentence after the '---' in the L1 body must be checked (and is missing from L2)"


def test_1_18_stage_4b_blocks_when_no_chunks_are_produced(tmp_path, monkeypatch):
    from pipeline.stages import stage_4_parse as s4
    calls = {}
    monkeypatch.setattr(s4, "load_checkpoint", lambda o, p: ({"stage_completions": {}, "pipeline_state": {}, "chapter_info": {}}, "x.json"))
    monkeypatch.setattr(s4, "mark_stage_complete", lambda *a, **k: calls.setdefault("complete", True))
    import pipeline.checkpoint_utils as cu
    monkeypatch.setattr(cu, "mark_stage_blocked", lambda *a, **k: calls.setdefault("blocked", True))
    rep = tmp_path / "REPAIRED_S2.md"; rep.write_text("# Title only\n\nNo second-level headings here at all.\n", encoding="utf-8")
    res = s4.run_stage_4b(str(rep), str(tmp_path), "P")
    assert res.get("blocked") and "blocked" in calls and "complete" not in calls
