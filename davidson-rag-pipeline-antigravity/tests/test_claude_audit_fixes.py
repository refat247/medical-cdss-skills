"""Regression tests for Claude audit findings: asset sync, untrusted completion exit code."""
import os

from pipeline import run_stage


def test_sync_chapter_assets_merges_into_existing_folder(tmp_path):
    ch = tmp_path / "Ch01"
    (ch / "assets" / "figures").mkdir(parents=True)
    (ch / "assets" / "figures" / "ch01_fig_02.jpeg").write_bytes(b"new")
    out = ch / "rag_pipeline_output"
    (out / "assets" / "figures").mkdir(parents=True)
    (out / "assets" / "figures" / "ch01_fig_01.jpeg").write_bytes(b"old")
    run_stage.sync_chapter_assets(str(ch / "Ch01.pdf.markdown_inlined.md"), str(out))
    assert sorted(os.listdir(out / "assets" / "figures")) == ["ch01_fig_01.jpeg", "ch01_fig_02.jpeg"]


def _fake_run(monkeypatch, trusted):
    from pipeline.stages import trust_ledger
    monkeypatch.setattr(run_stage, "execute_stage", lambda *a, **k: {"status": "COMPLETED"})
    monkeypatch.setattr(trust_ledger, "build_chapter_trust_record", lambda out, name, **k: {
        "trusted_for_downstream_use": trusted, "classification": "X"})


def test_auto_reports_untrusted(tmp_path, monkeypatch):
    src = tmp_path / "Davidson_25_Ch01_X" / "Davidson_25_Ch01_X.pdf.markdown_inlined.md"
    src.parent.mkdir()
    src.write_text("# x", encoding="utf-8")
    _fake_run(monkeypatch, False)
    assert run_stage.execute_pipeline_auto(str(src)) == "UNTRUSTED"
    _fake_run(monkeypatch, True)
    assert run_stage.execute_pipeline_auto(str(src)) is True
