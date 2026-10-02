"""Regression tests for the grounding-gate fail-open paths (skill_audits/SECOND_SWEEP.md 2.14-2.17)."""
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from verify_grounding import verify_note_grounding  # noqa: E402


def make_package(root: Path) -> Path:
    pkg = root / "pkg"
    for ch, body in (("16", "Grade 4 has a thrill."), ("17", "Heart failure drugs.")):
        d = pkg / "01_Davidson_25" / f"Davidson_25_Ch{ch}_X"
        d.mkdir(parents=True)
        # local chunk ids repeat in every chapter, exactly like the real pipeline output
        (d / f"Davidson_25_Ch{ch}_X_RAG_Optimised.md").write_text(
            f"---\nchunk_id: L2-001\n---\n{body}\n---\nchunk_id: L2-002\n---\nMore text {ch}.\n", encoding="utf-8")
    # an id that exists in ONE chapter only
    (pkg / "01_Davidson_25" / "Davidson_25_Ch16_X" / "Davidson_25_Ch16_X_RAG_Optimised.md").write_text(
        "---\nchunk_id: L2-001\n---\nGrade 4 has a thrill.\n---\nchunk_id: L2-002\n---\nMore text 16.\n"
        "---\nchunk_id: L2-777\n---\nOnly in sixteen.\n", encoding="utf-8")
    return pkg


def run(tmp_path, text):
    note = tmp_path / "note.md"
    note.write_text(text, encoding="utf-8")
    return verify_note_grounding(note, make_package(tmp_path))


HEAD = "# T\n## LAYER 2 — Davidson Core Spine\n- Levine grade 4 has a thrill [Anchor: Davidson-16-L2-001]\n"


def test_baseline_passes(tmp_path):
    assert run(tmp_path, HEAD)["status"] == "PASS"


def test_exempt_words_in_a_layer_heading_do_not_exempt_the_section(tmp_path):
    rep = run(tmp_path, HEAD + "## Layer 3 - Pharmacology: Clinical Evidence\n- Digoxin 5 mg daily is first line for all atrial fibrillation patients.\n")
    assert rep["status"] == "FAIL" and rep["uncited_lines"]


def test_real_exempt_section_is_still_exempt(tmp_path):
    rep = run(tmp_path, HEAD + "## Clinical Evidence Notes\n- ESC 2021 gives a Class I recommendation for echocardiography here.\n")
    assert rep["status"] == "PASS"


def test_unclassified_section_with_claims_fails(tmp_path):
    rep = run(tmp_path, HEAD + "## Treatment Pearls\n- Amiodarone 2000 mg IV bolus is safe in all patients with shock.\n")
    assert rep["status"] == "FAIL"


def test_bare_chunk_id_that_exists_in_several_chapters_is_ambiguous(tmp_path):
    rep = run(tmp_path, "# T\n## LAYER 2 — Davidson Core Spine\n- Amiodarone 2000 mg IV bolus in all patients [chunk: L2-001]\n")
    assert rep["status"] == "FAIL" and any("ambiguous" in u.lower() for u in rep["unresolved_citations"])


def test_unique_bare_chunk_id_still_resolves(tmp_path):
    rep = run(tmp_path, "# T\n## LAYER 2 — Davidson Core Spine\n- Only in sixteen exactly as written here [chunk: L2-777]\n")
    assert rep["status"] == "PASS", rep["failures"]


def test_wrong_chapter_label_fails_even_for_a_unique_id(tmp_path):
    rep = run(tmp_path, "# T\n## LAYER 2 — Davidson Core Spine\n- Only in sixteen but cited as ninety nine [Anchor: Davidson-99-L2-777]\n")
    assert rep["status"] == "FAIL"


def test_single_token_table_rows_are_claims(tmp_path):
    rep = run(tmp_path, HEAD + "## LAYER 4 — Beyond Davidson\n| Drug | Dose |\n|---|---|\n| Warfarin | 10mg |\n| Digoxin | 5mg |\n")
    assert rep["status"] == "FAIL" and len(rep["uncited_lines"]) == 2


def test_layer_1_heading_does_not_match_layer_10(tmp_path):
    rep = run(tmp_path, HEAD + "## Layer 10 notes\n- This line has no citation but is plainly a clinical claim here.\n")
    assert rep["status"] == "FAIL"        # unclassified (not silently treated as Layer 1 or exempt)


# ---------- docx publisher: title, tables ----------
docx = pytest.importorskip("docx")
from publish_executive_docx import compile_executive_docx  # noqa: E402


def build_docx(tmp_path, md_text):
    md = tmp_path / "n.md"; md.write_text(md_text, encoding="utf-8")
    out = tmp_path / "n.docx"
    compile_executive_docx(md, out, base_dir=tmp_path, allow_missing_images=True)
    return docx.Document(str(out))


def test_docx_title_comes_from_the_note_not_a_hard_coded_cardiac_title(tmp_path):
    d = build_docx(tmp_path, "# Diabetic Ketoacidosis\n\n## LAYER 2\n- Insulin infusion is started [Anchor: Davidson-16-L2-001]\n")
    texts = [p.text for p in d.paragraphs]
    assert any("Diabetic Ketoacidosis" in t for t in texts)
    assert not any("Cardiac Auscultation" in t for t in texts)


def test_two_tables_separated_by_a_blank_line_stay_two_tables(tmp_path):
    md = "# T\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n| X | Y | Z |\n|---|---|---|\n| low | replace | keep |\n"
    d = build_docx(tmp_path, md)
    assert len(d.tables) == 2
    cells = [c.text for r in d.tables[1].rows for c in r.cells]
    assert "low" in cells and "replace" in cells and "keep" in cells


def test_escaped_pipe_does_not_create_an_extra_cell(tmp_path):
    md = "# T\n\n| Formula | Note |\n|---|---|\n| P(A\\|B) | y |\n"
    d = build_docx(tmp_path, md)
    row = [c.text for c in d.tables[0].rows[1].cells]
    assert row == ["P(A|B)", "y"]


def test_literal_asterisks_are_not_treated_as_italic(tmp_path):
    """M28: 'a * b * c' lost its asterisks and italicised ' b '."""
    pytest.importorskip("docx")
    import docx
    from publish_executive_docx import add_formatted_runs
    doc = docx.Document()
    para = doc.add_paragraph()
    add_formatted_runs(para, "dose a * b * c and *real italic* and **bold**")
    assert "".join(r.text for r in para.runs) == "dose a * b * c and real italic and bold"
    italic = [r.text for r in para.runs if r.italic]
    assert italic == ["real italic"]


def test_16bit_greyscale_png_is_not_whitened(tmp_path):
    """M30: I;16 mid-grey converted to pure white."""
    PIL = pytest.importorskip("PIL.Image")
    from enhance_figures import enhance_figure
    src, dst = tmp_path / "g.png", tmp_path / "out.png"
    PIL.new("I;16", (8, 8), 30000).save(src)
    assert enhance_figure(src, dst, scale_factor=1)
    px = PIL.open(dst).convert("RGB").getpixel((4, 4))
    assert 100 < px[0] < 135                       # ~30000/256 = 117, not 255


def test_enhanced_copy_is_refreshed_when_source_changes(tmp_path):
    """M31: an existing output copy was never replaced after the source figure changed."""
    import os
    PIL = pytest.importorskip("PIL.Image")
    from enhance_figures import audit_and_enhance_directory
    figs, out = tmp_path / "figs", tmp_path / "out"
    figs.mkdir()
    PIL.new("RGB", (700, 10), (255, 0, 0)).save(figs / "a.png")
    audit_and_enhance_directory(figs, out)
    assert PIL.open(out / "a.png").getpixel((0, 0)) == (255, 0, 0)
    PIL.new("RGB", (700, 10), (0, 0, 255)).save(figs / "a.png")
    future = (out / "a.png").stat().st_mtime + 10
    os.utime(figs / "a.png", (future, future))
    audit_and_enhance_directory(figs, out)
    assert PIL.open(out / "a.png").getpixel((0, 0)) == (0, 0, 255)


def test_book_and_chapter_matching_are_not_loose():
    """M32: 'Research_12' parsed as chapter 12; a name mentioning two books resolved to the first."""
    from verify_grounding import CHAPTER_RE, normalise_book
    assert CHAPTER_RE.search("Research_12") is None and CHAPTER_RE.search("Search 3") is None
    assert CHAPTER_RE.search("Davidson_25_Ch16_X").group(1) == "16"
    assert CHAPTER_RE.search("Chapter 7").group(1) == "7"
    assert normalise_book("Davidson_vs_Harrison_notes") is None
    assert normalise_book("01_Davidson_25") == "davidson"
