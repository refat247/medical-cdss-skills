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
