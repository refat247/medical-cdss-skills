"""SECOND_SWEEP 1.30 (duplicate AUDIT_REPORT sections): re-running Stage 4 must replace, not append again."""
from pipeline.stages.stage_4_parse import _write_stage4_report_sections


def test_rerun_replaces_stage4_sections_and_keeps_stage1_content(tmp_path):
    p = tmp_path / "X_AUDIT_REPORT.md"
    p.write_text("Stage 1 body\nVERDICT: PASS", encoding="utf-8")
    _write_stage4_report_sections(str(p), "\n\n## Stage 4 Header Map (1 headers)\n\nfirst run")
    _write_stage4_report_sections(str(p), "\n\n## Stage 4 Header Map (2 headers)\n\nsecond run")
    text = p.read_text(encoding="utf-8")
    assert text.count("## Stage 4 Header Map") == 1
    assert "second run" in text and "first run" not in text
    assert text.startswith("Stage 1 body\nVERDICT: PASS")


def test_missing_report_is_created(tmp_path):
    p = tmp_path / "Y_AUDIT_REPORT.md"
    _write_stage4_report_sections(str(p), "\n\n## Stage 4 Header Map (0 headers)\n\n")
    assert p.exists()
