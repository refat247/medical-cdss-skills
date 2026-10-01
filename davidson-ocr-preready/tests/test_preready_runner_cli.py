"""Tests for preready/runner.py CLI."""
import os
import subprocess
import sys
import tempfile
import pytest
from preready.runner import run_preready


def test_run_preready_end_to_end():
    with tempfile.TemporaryDirectory() as tmp_source:
        with tempfile.TemporaryDirectory() as tmp_out:
            # Create mock source structure
            p2 = os.path.join(tmp_source, "pages", "page-2")
            p3 = os.path.join(tmp_source, "pages", "page-3")
            os.makedirs(p2, exist_ok=True)
            os.makedirs(p3, exist_ok=True)

            with open(os.path.join(p2, "tbl-0.md"), "w") as f:
                f.write("| Col1 | Col2 |\n|---|---|\n| Val1 | Val2 |")

            with open(os.path.join(p3, "img-0.jpeg"), "wb") as f:
                f.write(b"fake_jpeg_data")

            raw_md = (
                "# Clinical Decision-Making\n\n"
                "# Introduction\n\n"
                "Overview text.\n\n"
                "1.1 Root causes of error\n\n"
                "[tbl-0.md](tbl-0.md)\n\n"
                "![img-0.jpeg](img-0.jpeg)\n\n"
                "Fig. 1.1 Likelihood ratio of signs.\n"
            )
            with open(os.path.join(tmp_source, "markdown.md"), "w", encoding="utf-8") as f:
                f.write(raw_md)

            res = run_preready(
                source_dir=tmp_source,
                out_dir=tmp_out,
                ch_num=1,
                prefix="Davidson_25_01_Clinical_decision_making"
            )

            assert res["status"] == "SUCCESS"
            assert os.path.exists(res["output_file"])
            assert res["tables_inlined"] == 1
            assert res["figures_decoupled"] == 1

            inlined_content = open(res["output_file"], encoding="utf-8").read()
            assert "| Col1 | Col2 |" in inlined_content
            assert "assets/figures/ch01_fig_01.jpeg" in inlined_content
            assert "### 1.1 Root causes of error" in inlined_content


def test_run_preready_default_input_folder():
    with tempfile.TemporaryDirectory() as tmp_source:
        p1 = os.path.join(tmp_source, "pages", "page-1")
        os.makedirs(p1, exist_ok=True)

        with open(os.path.join(p1, "tbl-0.md"), "w") as f:
            f.write("| TblCol1 | TblCol2 |\n|---|---|\n| A | B |")

        raw_md = "# Title\n\n[tbl-0.md](tbl-0.md)\n"
        with open(os.path.join(tmp_source, "markdown.md"), "w", encoding="utf-8") as f:
            f.write(raw_md)

        # Calling without out_dir should default to tmp_source
        res = run_preready(source_dir=tmp_source, ch_num=2, prefix="Davidson_25_02_Test")

        assert res["status"] == "SUCCESS"
        assert os.path.dirname(res["output_file"]) == tmp_source
        assert os.path.exists(res["output_file"])
        assert os.path.exists(os.path.join(tmp_source, "Davidson_25_02_Test_PREREADY_REPORT.md"))


def test_resolve_chapter_number_and_expand_source_dirs():
    from preready.runner import resolve_chapter_number, expand_source_dirs, detect_document_archetype

    assert resolve_chapter_number("D:/test/Davidson_25_01_Clinical decision-making.pdf") == 1
    assert resolve_chapter_number("D:/test/Davidson_25_30_Maternal medicine.pdf") == 30
    assert resolve_chapter_number("D:/test/chapter_12") == 12
    # Guideline with 4-digit year should default to chapter 1, not 2026
    assert resolve_chapter_number("D:/test/ADA_2026_DM_guideline.pdf") == 1
    assert resolve_chapter_number("D:/test/KDIGO_2024_CKD_Guideline") == 1

    assert detect_document_archetype("D:/test/Davidson_25_01_Clinical.pdf") == "TEXTBOOK"
    assert detect_document_archetype("D:/test/ADA_2026_DM_guideline.pdf") == "GUIDELINE"
    assert detect_document_archetype("D:/test/KDIGO_2024_CKD_Guideline") == "GUIDELINE"

    with tempfile.TemporaryDirectory() as parent_dir:
        ch1 = os.path.join(parent_dir, "Davidson_25_01_Test")
        ch2 = os.path.join(parent_dir, "Davidson_25_02_Test")
        os.makedirs(ch1, exist_ok=True)
        os.makedirs(ch2, exist_ok=True)
        with open(os.path.join(ch1, "markdown.md"), "w") as f:
            f.write("# Ch1")
        with open(os.path.join(ch2, "markdown.md"), "w") as f:
            f.write("# Ch2")

        expanded = expand_source_dirs([parent_dir])
        assert len(expanded) == 2
        assert ch1 in expanded
        assert ch2 in expanded


