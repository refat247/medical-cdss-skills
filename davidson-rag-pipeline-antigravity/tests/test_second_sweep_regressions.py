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
