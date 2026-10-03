"""Regression tests for davidson-ocr-preready (skill_audits/SECOND_SWEEP.md 2.6, P1, P2, M13-M17)."""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from preready import __version__  # noqa: E402
from preready import auditor  # noqa: E402
from preready.header_normalizer import clean_ocr_running_headers, normalize_heading_hierarchy  # noqa: E402
from preready.runner import detect_document_archetype  # noqa: E402


def test_p1_provenance_stamp_equals_the_skill_version():
    assert auditor.SKILL_VERSION == __version__
    assert f'skill_version: "{__version__}"' in auditor._format_provenance_header("x")


@pytest.mark.parametrize("folder,expected", [
    ("ADA_2026_DM_guideline", "GUIDELINE"), ("KDIGO_2024_CKD", "GUIDELINE"), ("NICE_NG28", "GUIDELINE"),
    ("canada_notes_ch3", "TEXTBOOK"), ("venice_2020_chapter", "TEXTBOOK"), ("Davidson_25_Ch5", "TEXTBOOK"),
    ("Standards_of_Care_2026", "GUIDELINE"),
])
def test_p2_archetype_uses_whole_tokens_not_substrings(folder, expected, tmp_path):
    d = tmp_path / folder; d.mkdir()
    assert detect_document_archetype(str(d)) == expected


@pytest.mark.parametrize("line", ["T4", "S3x", "CD4", "B12", "IL-6", "pH 7"])
def test_m13_short_clinical_tokens_are_not_page_markers(line):
    out = clean_ocr_running_headers(f"Text before.\n\n{line}\n\nText after.\n")
    assert line in out and "page:" not in out


@pytest.mark.parametrize("line,marker", [("42", "<!-- page: 42 -->"), ("S12", "<!-- page: S12 -->"), ("P-7", "<!-- page: P7 -->")])
def test_m13_real_page_numbers_still_become_markers(line, marker):
    assert marker in clean_ocr_running_headers(f"Text.\n\n{line}\n\nMore.\n")


def test_m13_number_inside_running_text_is_kept():
    out = clean_ocr_running_headers("Give aspirin\n300\nmg stat\n")
    assert "\n300\n" in out


def test_m14_https_resource_lines_are_not_deleted_but_downloaded_from_is():
    out = clean_ocr_running_headers("Useful websites\n\nhttps://www.who.int/dengue\n\nDownloaded from x.org\n")
    assert "https://www.who.int/dengue" in out and "Downloaded from" not in out


def test_m15_adjacent_distinct_page_markers_are_both_kept():
    out = clean_ocr_running_headers("a\n\n12\n\n13\n\nb\n")
    assert "<!-- page: 12 -->" in out and "<!-- page: 13 -->" in out


def test_m15_exact_duplicate_markers_still_collapse():
    out = clean_ocr_running_headers("a\n\n12\n\n12\n\nb\n")
    assert out.count("<!-- page: 12 -->") == 1


@pytest.mark.parametrize("line", ["Table 1.2 shows that the dose doubles in renal failure.", "0.9 Normal saline at 100 mL/h",
                                  "2.5 mg is the usual starting dose."])
def test_m16_prose_and_dose_lines_are_not_turned_into_headings(line):
    assert normalize_heading_hierarchy(f"{line}\n") == f"{line}"


@pytest.mark.parametrize("line", ["Table 1.2 Causes of anaemia", "Box 3.1 Diagnostic criteria", "1.1 Root causes of diagnostic error"])
def test_m16_real_headings_still_normalised(line):
    assert normalize_heading_hierarchy(f"{line}\n") == f"### {line}"


def test_m16_hash_comment_inside_code_fence_is_not_demoted():
    md = "# Title\n\n```\n# comment\n```\n"
    assert "# comment" in normalize_heading_hierarchy(md) and "## comment" not in normalize_heading_hierarchy(md)


def test_review_m6_real_captions_are_promoted_but_prose_is_not():
    from preready.header_normalizer import normalize_heading_hierarchy
    for cap in ["Table 14.3 Causes of hypokalaemia (K+ <3.5 mmol/L)", "Box 4.2 When is surgery indicated",
                "Table 5.2 Drugs that require dose adjustment when eGFR is below 30 mL/min"]:
        assert normalize_heading_hierarchy(cap).startswith("### "), cap
    assert not normalize_heading_hierarchy("Table 1.2 shows that insulin is required").startswith("###")


def test_review_m7_bare_publisher_pdf_url_watermark_is_stripped():
    from preready.header_normalizer import clean_ocr_running_headers as clean_ocr_noise
    out = clean_ocr_noise("Text.\n\nhttps://diabetesjournals.org/care/article-pdf/48/1/S1.pdf\n\nMore text.")
    assert "article-pdf" not in out


def _chapter(tmp_path, md, tables=None):
    src = tmp_path / "src"
    for name, body in (tables or {}).items():
        d = src / "pages" / "page-1"
        d.mkdir(parents=True, exist_ok=True)
        (d / name).write_text(body, encoding="utf-8")
    src.mkdir(exist_ok=True)
    (src / "markdown.md").write_text(md, encoding="utf-8")
    return str(src)


def test_m17_empty_header_cell_still_gets_full_delimiter():
    from preready.table_inliner import ensure_table_delimiters
    out = ensure_table_delimiters("| A |  | C |\n| 1 | 2 | 3 |").splitlines()
    assert out[1].count("---") == 3


def test_m19_report_is_computed_and_missing_table_is_partial(tmp_path):
    from preready.runner import run_preready
    src = _chapter(tmp_path, "# T\n\n[tbl-0.md](tbl-0.md)\n\n[tbl-9.md](tbl-9.md)\n",
                   {"tbl-0.md": "| A | B |\n|---|---|\n| 1 | 2 |"})
    res = run_preready(source_dir=src, ch_num=2, prefix="Davidson_25_02_T")
    assert res["status"] == "PARTIAL"
    report = open(res["master_report"], encoding="utf-8").read()
    assert "Completeness**: 100%" not in report and "50% (1/2)" in report


def test_m19_complete_chapter_is_success_and_cli_exit_is_3_on_partial(tmp_path):
    import subprocess
    from preready.runner import run_preready
    ok = _chapter(tmp_path, "# T\n\n[tbl-0.md](tbl-0.md)\n", {"tbl-0.md": "| A | B |\n|---|---|\n| 1 | 2 |"})
    res = run_preready(source_dir=ok, ch_num=2, prefix="Davidson_25_02_T")
    assert res["status"] == "SUCCESS"
    assert "Completeness**: 100% (1/1)" in open(res["master_report"], encoding="utf-8").read()
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "markdown.md").write_text("# T\n\n[tbl-5.md](tbl-5.md)\n", encoding="utf-8")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    r = subprocess.run([sys.executable, "-m", "preready.runner", "--source-dir", str(bad), "--ch", "2", "--prefix", "Davidson_25_02_T"],
                       cwd=root, capture_output=True, text=True)
    assert r.returncode == 3, r.stderr

