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
