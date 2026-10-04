"""Direct module tests for Stage 4.5b and Stage 7 branches the audit found untested (SECOND_SWEEP 1.30, T-items)."""
import json

import pytest

from pipeline.stages import stage_4_5b_pharma as s45b
from pipeline.stages import stage_7_scorecard as s7


@pytest.fixture
def stub_checkpoint(monkeypatch):
    marks = []
    for mod in (s45b, s7):
        monkeypatch.setattr(mod, "load_checkpoint", lambda o, p: ({}, "x.json"))
        monkeypatch.setattr(mod, "should_run_stage", lambda c, s: True)
        monkeypatch.setattr(mod, "mark_stage_complete", lambda *a, **k: marks.append((a[2], k)))
    return marks


def _files(tmp_path, source, chunks):
    rep, ch = tmp_path / "rep.md", tmp_path / "chunks.md"
    rep.write_text(source, encoding="utf-8")
    ch.write_text(chunks, encoding="utf-8")
    return str(rep), str(ch)


L2 = "---\nchunk_id: L2-1\nchunk_level: 2\nsemantic_type: drug_info\n---\n\n{}\n"


# ---- Stage 4.5b ----

def test_45b_inactive_stage_is_skipped_and_recorded(tmp_path, stub_checkpoint):
    rep, ch = _files(tmp_path, "Give 5 mg.", L2.format("Give 5 mg."))
    res = s45b.run_stage_4_5b(rep, ch, str(tmp_path), "P", is_active=False)
    assert res["status"] == "skipped" and stub_checkpoint[0][0] == "4.5b"
    assert not (tmp_path / "P_FlagCoverage.md").exists()


def test_45b_dropped_values_are_warned_and_report_written(tmp_path, stub_checkpoint):
    rep, ch = _files(tmp_path, "Reduce risk by 40% and 25% overall.", L2.format("Reduce risk overall."))
    res = s45b.run_stage_4_5b(rep, ch, str(tmp_path), "P")
    assert res["verdict"].startswith("WARN") and "dropped" in res["verdict"]
    report = (tmp_path / "P_FlagCoverage.md").read_text(encoding="utf-8")
    assert "VERDICT:" in report and "LOW" in report


def test_45b_no_dosing_content_is_cleared(tmp_path, stub_checkpoint):
    rep, ch = _files(tmp_path, "Plain narrative.", L2.format("Plain narrative."))
    assert s45b.run_stage_4_5b(rep, ch, str(tmp_path), "P")["verdict"] == "CLEARED"


# ---- Stage 7 ----

def _scorecard(tmp_path, source, final, spot=None, gaps=None):
    rep, rag = tmp_path / "rep.md", tmp_path / "rag.md"
    rep.write_text(source, encoding="utf-8")
    rag.write_text(final, encoding="utf-8")
    if spot is not None:
        (tmp_path / "P_SpotCheck.md").write_text(spot, encoding="utf-8")
    if gaps is not None:
        (tmp_path / "P_L1L2_CoverageGaps.md").write_text(gaps, encoding="utf-8")
    return s7.run_stage_7(str(rep), str(rag), str(tmp_path), "P")


def test_7_nothing_evaluable_gives_na_overall_not_a_perfect_score(tmp_path, stub_checkpoint):
    res = _scorecard(tmp_path, "Plain text.", "Plain text.")
    assert res["overall_score"] is None
    assert all(d["score"] is None for d in res["dimensions"].values())


def test_7_spotcheck_and_coverage_scores_are_parsed(tmp_path, stub_checkpoint):
    res = _scorecard(tmp_path, "Plain.", "Plain.", spot="Passed: 3 | Failed: 1",
                     gaps="L1 chunks checked: 4\n| L1-2 | gap |\n")
    dims = res["dimensions"]
    assert dims["verbatim_accuracy"]["score"] == 0.75
    assert dims["coverage_completeness"]["score"] == 0.75        # 1 gap row of 4 checked
    assert res["overall_score"] == 0.75


def test_7_zero_l1_chunks_checked_is_not_a_perfect_coverage_score(tmp_path, stub_checkpoint):
    res = _scorecard(tmp_path, "Plain.", "Plain.", gaps="L1 chunks checked: 0\n")
    assert res["dimensions"]["coverage_completeness"]["score"] is None


def test_7_writes_markdown_and_json_and_records_checkpoint(tmp_path, stub_checkpoint):
    _scorecard(tmp_path, "Give 5 mg.", "Give 5 mg.")
    assert (tmp_path / "P_QualityScorecard.md").exists()
    data = json.loads((tmp_path / "P_QualityScorecard.json").read_text(encoding="utf-8"))
    assert data["dimensions"]["dosing_preservation"]["score"] == 1.0
    assert stub_checkpoint[-1][0] == "7"


def test_7_already_complete_stage_is_skipped(tmp_path, monkeypatch):
    monkeypatch.setattr(s7, "load_checkpoint", lambda o, p: ({}, "x.json"))
    monkeypatch.setattr(s7, "should_run_stage", lambda c, s: False)
    rep, rag = tmp_path / "r.md", tmp_path / "g.md"
    rep.write_text("x", encoding="utf-8"); rag.write_text("x", encoding="utf-8")
    assert s7.run_stage_7(str(rep), str(rag), str(tmp_path), "P")["status"] == "skipped"
