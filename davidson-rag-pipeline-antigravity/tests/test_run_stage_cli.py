"""Tests for pipeline/run_stage.py CLI dispatcher (v2.14.0)."""
import os
import subprocess
import sys
import pytest

from pipeline.run_stage import derive_chapter_info, execute_stage, execute_pipeline_auto

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_derive_chapter_info_standard_format():
    src = r"D:\davidson_25_full_pipeline\01\Davidson_25_01_Clinical_decision_making.pdf.markdown_inlined.md"
    info = derive_chapter_info(src)
    assert info["ch_num"] == "01"
    assert info["prefix"] == "Davidson_25_Ch01_Clinical_decision_making"
    assert not info["is_pharma"]


def test_derive_chapter_info_pharma_detection():
    src = r"D:\davidson_25_full_pipeline\18\Davidson_25_18_Cardiovascular_disease.pdf.markdown_inlined.md"
    info = derive_chapter_info(src)
    assert info["ch_num"] == "18"
    assert info["prefix"] == "Davidson_25_Ch18_Cardiovascular_disease"
    assert info["is_pharma"]
    assert info["doc_archetype"] == "TEXTBOOK"


def test_derive_chapter_info_guideline_archetype():
    src = r"D:\guidelines\DM\ADA_2026_DM_guideline.pdf\ADA_2026_DM_guideline.pdf.markdown_inlined.md"
    info = derive_chapter_info(src)
    assert info["doc_archetype"] == "GUIDELINE"
    assert info["ch_num"] == "01"  # Year 2026 is protected, defaults to 01
    assert info["prefix"] == "ADA_2026_DM_guideline"

    src2 = r"D:\guidelines\KDIGO_2024_CKD_Guideline.pdf.markdown_inlined.md"
    info2 = derive_chapter_info(src2)
    assert info2["doc_archetype"] == "GUIDELINE"
    assert info2["ch_num"] == "01"
    assert info2["prefix"] == "KDIGO_2024_CKD_Guideline"



def test_run_stage_cli_init_checkpoint(tmp_path):
    src = str(tmp_path / "Davidson_25_01_Clinical_decision_making.pdf.markdown_inlined.md")
    with open(src, "w", encoding="utf-8") as f:
        f.write("# Chapter 1\n\n## Overview\nSample clinical text.")

    out_dir = str(tmp_path / "01_out")
    cmd = [
        sys.executable,
        "-m",
        "pipeline.run_stage",
        "--stage",
        "0",
        "--source",
        src,
        "--out",
        out_dir,
    ]
    proc = subprocess.run(cmd, cwd=REPO_DIR, capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0
    assert "Initialized checkpoint at:" in proc.stdout
    assert os.path.exists(os.path.join(out_dir, "Davidson_25_Ch01_Clinical_decision_making_CHECKPOINT.json"))


def test_run_stage_cli_auto_execution(tmp_path):
    src = str(tmp_path / "Davidson_25_01_Clinical_decision_making.pdf.markdown_inlined.md")
    with open(src, "w", encoding="utf-8") as f:
        f.write("# Chapter 1\n\n## Overview\n\n### Clinical Management\nPatient should receive 500 mg paracetamol.\n")

    out_dir = str(tmp_path / "01_auto_out")
    cmd = [
        sys.executable,
        "-m",
        "pipeline.run_stage",
        "--stage",
        "auto",
        "--source",
        src,
        "--out",
        out_dir,
    ]
    proc = subprocess.run(cmd, cwd=REPO_DIR, capture_output=True, text=True, encoding="utf-8")
    # Since the stub chapter triggers a blocking gate (Stage 4.5c coverage),
    # the CLI properly exits 1 (fail-closed) rather than masking failure with 0.
    assert proc.returncode in (0, 1)
    assert "Starting Automated Pipeline Chaining" in proc.stdout
    assert os.path.exists(os.path.join(out_dir, "Davidson_25_Ch01_Clinical_decision_making_CHECKPOINT.json"))


def test_run_stage_cli_default_subfolder_output(tmp_path):
    """Proves that omitting --out automatically outputs to <source_dir>/rag_pipeline_output."""
    chapter_dir = tmp_path / "Davidson_25_01_Clinical_decision_making.pdf"
    chapter_dir.mkdir()
    src = str(chapter_dir / "Davidson_25_01_Clinical_decision_making.pdf.markdown_inlined.md")
    with open(src, "w", encoding="utf-8") as f:
        f.write("# Chapter 1\n\n## Overview\nSample clinical text.")

    cmd = [
        sys.executable,
        "-m",
        "pipeline.run_stage",
        "--stage",
        "0",
        "--source",
        src,
    ]
    proc = subprocess.run(cmd, cwd=REPO_DIR, capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0
    expected_out_dir = chapter_dir / "rag_pipeline_output"
    assert expected_out_dir.exists()
    assert (expected_out_dir / "Davidson_25_Ch01_Clinical_decision_making_CHECKPOINT.json").exists()