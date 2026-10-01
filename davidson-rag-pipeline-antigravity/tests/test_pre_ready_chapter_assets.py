"""Tests for scripts/pre_ready_chapter_assets.py."""
import os
import subprocess
import sys
import tempfile
import pytest
from scripts.pre_ready_chapter_assets import (
    find_assets_dir,
    scan_figure_citations,
    inline_figure_tags,
    write_figure_audit_report
)

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_scan_figure_citations():
    text = (
        "# Cardiovascular Disease\n\n"
        "ECG changes are prominent (Fig. 18.4: Acute anterolateral STEMI).\n\n"
        "Further angiography is shown in Figure 18.12: Coronary dissection."
    )
    citations = scan_figure_citations(text)
    assert len(citations) == 2
    assert citations[0]["key"] == "18.4"
    assert citations[0]["caption"] == "Acute anterolateral STEMI"
    assert citations[0]["asset_name"] == "ch18_fig_04.png"
    assert citations[1]["key"] == "18.12"
    assert citations[1]["caption"] == "Coronary dissection"


def test_inline_figure_tags():
    text = "ECG changes are prominent (Fig. 18.4: Acute anterolateral STEMI).\n\nNext section."
    citations = scan_figure_citations(text)
    with tempfile.TemporaryDirectory() as tmp_dir:
        assets_dir = os.path.join(tmp_dir, "assets", "figures")
        os.makedirs(assets_dir, exist_ok=True)
        # Create a mock image file
        mock_img = os.path.join(assets_dir, "ch18_fig_04.png")
        with open(mock_img, "w") as f:
            f.write("mock image data")

        updated_text, audit_results = inline_figure_tags(text, citations, assets_dir)
        assert "![Acute anterolateral STEMI](assets/figures/ch18_fig_04.png)" in updated_text
        assert len(audit_results) == 1
        assert audit_results[0]["exists_on_disk"] is True
        assert audit_results[0]["inlined_now"] is True


def test_write_figure_audit_report():
    with tempfile.TemporaryDirectory() as tmp_dir:
        audit_results = [{
            "key": "18.4",
            "caption": "STEMI ECG",
            "asset_path": "assets/figures/ch18_fig_04.png",
            "exists_on_disk": True,
            "already_inlined": False,
            "inlined_now": True
        }]
        report_path = write_figure_audit_report(tmp_dir, "Davidson_25_18", audit_results, "assets/figures")
        assert os.path.exists(report_path)
        content = open(report_path, encoding="utf-8").read()
        assert "Figure & Asset Alignment Audit Report — Davidson_25_18" in content
        assert "Fig 18.4" in content
        assert "STEMI ECG" in content
        assert "✅ YES" in content


def test_pre_ready_cli_end_to_end():
    with tempfile.TemporaryDirectory() as tmp_dir:
        md_path = os.path.join(tmp_dir, "Davidson_25_18_Cardio.markdown_inlined.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# Chapter 18\n\nObserve ECG features (Fig. 18.4: Acute STEMI).\n")

        cmd = [
            sys.executable, "-m", "scripts.pre_ready_chapter_assets",
            "--md", md_path,
            "--out-dir", tmp_dir,
            "--ch", "18"
        ]
        res = subprocess.run(cmd, cwd=REPO_DIR, capture_output=True, text=True)
        assert res.returncode == 0
        out_md = os.path.join(tmp_dir, "Davidson_25_18_Cardio.pdf.markdown_inlined.md")
        assert os.path.exists(out_md)
        audit_file = os.path.join(tmp_dir, "Davidson_25_18_Cardio_FIGURE_AUDIT.md")
        assert os.path.exists(audit_file)
