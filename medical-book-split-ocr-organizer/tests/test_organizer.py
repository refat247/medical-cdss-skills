import os
import shutil
import sys
import tempfile
from pathlib import Path
import pytest

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(root_dir / "scripts") not in sys.path:
    sys.path.insert(0, str(root_dir / "scripts"))

from scripts.organizer import normalize_name, cmd_init, cmd_status, cmd_organize_section, cmd_ingest, cmd_organize_book


def test_normalize_name():
    assert normalize_name("Chapter_01.pdf") == "chapter 01"
    assert normalize_name("PART   12__disorders.pdf") == "part 12 disorders"
    assert normalize_name("National Guideline for Measles_2026.pdf") == "national guideline for measles 2026"


def test_cmd_organize_section_from_pdf_folder():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create an unorganized section folder ending in .pdf
        sec_folder = root / "National Guideline for the Management of Measles_2026.pdf"
        sec_folder.mkdir()

        # Place a source PDF file inside
        pdf_file = sec_folder / "National Guideline for the Management of Measles_2026.pdf"
        pdf_file.write_text("dummy pdf content", encoding="utf-8")

        # Place raw OCR files inside
        md_file = sec_folder / "markdown.md"
        md_file.write_text("# Measles Guideline", encoding="utf-8")
        pages_dir = sec_folder / "pages"
        pages_dir.mkdir()
        (pages_dir / "page-1").mkdir()
        (pages_dir / "page-1" / "tbl-0.md").write_text("| Table |", encoding="utf-8")

        # Run organize-section
        res = cmd_organize_section(str(sec_folder))
        assert res == 0

        # Verify old .pdf folder is gone
        assert not sec_folder.exists()

        # Verify canonical section folder without .pdf exists
        canonical_sec = root / "National Guideline for the Management of Measles_2026"
        assert canonical_sec.exists()
        assert canonical_sec.is_dir()

        # Verify source PDF is at canonical_sec root
        canonical_pdf = canonical_sec / "National Guideline for the Management of Measles_2026.pdf"
        assert canonical_pdf.exists()
        assert canonical_pdf.read_text(encoding="utf-8") == "dummy pdf content"

        # Verify ocr markdown isolation folder exists and contains OCR files
        ocr_item = canonical_sec / "ocr markdown" / "National Guideline for the Management of Measles_2026.pdf"
        assert ocr_item.exists()
        assert ocr_item.is_dir()
        assert (ocr_item / "markdown.md").exists()
        assert (ocr_item / "pages" / "page-1" / "tbl-0.md").exists()


def test_cmd_ingest_direct_single_ocr_folder_to_single_section():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Target section dir
        sec_dir = root / "DIARRHOEA"
        sec_dir.mkdir()
        pdf_file = sec_dir / "THE TREATMENT OF DIARRHOEA_A manual for physicians by WHO.pdf"
        pdf_file.write_text("pdf dummy content", encoding="utf-8")
        docx_file = sec_dir / "who-2005-diarrhoea-2026-companion.docx"
        docx_file.write_text("docx dummy content", encoding="utf-8")

        # Direct OCR staging folder
        ocr_staging = root / "THE TREATMENT OF DIARRHOEA_A manual for physicians by WHO.pdf"
        ocr_staging.mkdir()
        (ocr_staging / "markdown.md").write_text("# Diarrhoea OCR", encoding="utf-8")
        pages_dir = ocr_staging / "pages"
        pages_dir.mkdir()
        (pages_dir / "page-0").mkdir()

        # Run ingest directly from ocr_staging into sec_dir
        res = cmd_ingest(target_dir=str(sec_dir), source_dir=str(ocr_staging))
        assert res == 0

        # Verify old staging folder is gone (moved)
        assert not ocr_staging.exists()

        # Verify destination in sec_dir
        dest_ocr = sec_dir / "ocr markdown" / "THE TREATMENT OF DIARRHOEA_A manual for physicians by WHO.pdf"
        assert dest_ocr.exists()
        assert dest_ocr.is_dir()
        assert (dest_ocr / "markdown.md").exists()
        assert (dest_ocr / "pages" / "page-0").exists()

        # Verify original PDF and docx remain untouched in sec_dir
        assert pdf_file.exists()
        assert docx_file.exists()


def test_cmd_status_single_section():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        sec_dir = root / "DIARRHOEA"
        sec_dir.mkdir()
        pdf_file = sec_dir / "THE TREATMENT OF DIARRHOEA_A manual for physicians by WHO.pdf"
        pdf_file.write_text("pdf content", encoding="utf-8")

        # Before OCR
        res = cmd_status(str(sec_dir))
        assert res == 0

        # Create ocr markdown
        ocr_item = sec_dir / "ocr markdown" / "THE TREATMENT OF DIARRHOEA_A manual for physicians by WHO.pdf"
        ocr_item.mkdir(parents=True)
        (ocr_item / "markdown.md").write_text("md content", encoding="utf-8")

        # After OCR
        res = cmd_status(str(sec_dir))
        assert res == 0


def test_cmd_organize_section_with_external_pdf_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        pdf_dir = root / "split_pdfs"
        pdf_dir.mkdir()
        pdf_file = pdf_dir / "Chapter_01_Intro.pdf"
        pdf_file.write_text("external pdf bytes", encoding="utf-8")

        book_dir = root / "book_ocr"
        book_dir.mkdir()
        sec_folder = book_dir / "Chapter_01_Intro.pdf"
        sec_folder.mkdir()
        (sec_folder / "markdown.md").write_text("# Chapter 1", encoding="utf-8")

        res = cmd_organize_section(str(sec_folder), pdf_source_dir=str(pdf_dir))
        assert res == 0

        # Verify old folder is removed
        assert not sec_folder.exists()

        # Canonical section folder
        canonical_sec = book_dir / "Chapter_01_Intro"
        assert canonical_sec.exists()
        assert (canonical_sec / "Chapter_01_Intro.pdf").exists()
        assert (canonical_sec / "Chapter_01_Intro.pdf").read_text(encoding="utf-8") == "external pdf bytes"

        # OCR workspace
        ocr_ws = canonical_sec / "ocr markdown" / "Chapter_01_Intro.pdf"
        assert ocr_ws.exists()
        assert (ocr_ws / "markdown.md").exists()

        # Original in pdf_dir preserved (copied)
        assert pdf_file.exists()


def test_cmd_organize_book():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        pdf_dir = root / "split_pdfs"
        pdf_dir.mkdir()
        (pdf_dir / "Ch01.pdf").write_text("pdf 1", encoding="utf-8")
        (pdf_dir / "Ch02.pdf").write_text("pdf 2", encoding="utf-8")

        book_dir = root / "book_ocr"
        book_dir.mkdir()
        # Unorganized section 1
        sec1 = book_dir / "Ch01.pdf"
        sec1.mkdir()
        (sec1 / "markdown.md").write_text("md 1", encoding="utf-8")

        # Unorganized section 2
        sec2 = book_dir / "Ch02.pdf"
        sec2.mkdir()
        (sec2 / "markdown.md").write_text("md 2", encoding="utf-8")

        # Non-chapter directories that should be ignored
        (book_dir / "cdss_global_index").mkdir()
        (book_dir / "verification_bundle_build").mkdir()

        res = cmd_organize_book(target_dir=str(book_dir), pdf_source_dir=str(pdf_dir))
        assert res == 0

        # Both sections organized
        assert (book_dir / "Ch01" / "Ch01.pdf").exists()
        assert (book_dir / "Ch01" / "ocr markdown" / "Ch01.pdf" / "markdown.md").exists()
        assert (book_dir / "Ch02" / "Ch02.pdf").exists()
        assert (book_dir / "Ch02" / "ocr markdown" / "Ch02.pdf" / "markdown.md").exists()


# ---------------- second-sweep 2.5 (M8-M11, O1) ----------------
def _book(tmp_path, sections=("Sec A",)):
    book = tmp_path / "book"
    for s in sections:
        (book / f"{s}.pdf").mkdir(parents=True)          # section folder named like its PDF
        (book / f"{s}.pdf" / "ocr markdown").mkdir()
    return book


def _ocr_download(tmp_path, name, with_file=True):
    d = tmp_path / "dl" / name
    d.mkdir(parents=True)
    if with_file:
        (d / "markdown.md").write_text("ocr text")
    return d.parent


def test_ingest_into_an_existing_empty_destination_does_not_nest(tmp_path):
    book = _book(tmp_path)
    (book / "Sec A.pdf" / "ocr markdown" / "Sec A.pdf").mkdir()          # pre-created empty slot
    dl = _ocr_download(tmp_path, "Sec A.pdf")
    cmd_ingest(str(book), source_dir=str(dl))
    dest = book / "Sec A.pdf" / "ocr markdown" / "Sec A.pdf"
    assert (dest / "markdown.md").exists() and not (dest / "Sec A.pdf").exists()


def test_force_overwrite_moves_the_old_ocr_aside_instead_of_deleting_it(tmp_path):
    book = _book(tmp_path)
    old = book / "Sec A.pdf" / "ocr markdown" / "Sec A.pdf"; old.mkdir(); (old / "old.md").write_text("precious")
    dl = _ocr_download(tmp_path, "Sec A.pdf")
    cmd_ingest(str(book), source_dir=str(dl), force=True)
    kept = [p for p in (book / "Sec A.pdf" / "_replaced_backups").iterdir() if ".replaced-" in p.name]
    assert kept and (kept[0] / "old.md").read_text() == "precious"
    # backups must not sit among the live OCR slots
    assert not [p for p in (book / "Sec A.pdf" / "ocr markdown").iterdir() if ".replaced-" in p.name]


def test_ingest_dry_run_moves_nothing(tmp_path):
    book = _book(tmp_path)
    dl = _ocr_download(tmp_path, "Sec A.pdf")
    cmd_ingest(str(book), source_dir=str(dl), dry_run=True)
    assert (dl / "Sec A.pdf" / "markdown.md").exists()
    assert not (book / "Sec A.pdf" / "ocr markdown" / "Sec A.pdf").exists()


def test_fuzzy_match_prefers_the_longest_exact_section_and_refuses_ambiguity(tmp_path):
    book = _book(tmp_path, sections=("Part 1 Cardiology Chapter 1", "Part 1 Cardiology Chapter 10"))
    dl = _ocr_download(tmp_path, "Part 1 Cardiology Chapter 10 Heart Failure.pdf")
    cmd_ingest(str(book), source_dir=str(dl))
    assert any((book / "Part 1 Cardiology Chapter 10.pdf" / "ocr markdown").iterdir())
    assert not any((book / "Part 1 Cardiology Chapter 1.pdf" / "ocr markdown").iterdir())


def test_status_does_not_count_an_empty_ocr_slot_as_present(tmp_path, capsys):
    book = _book(tmp_path)
    (book / "Sec A.pdf" / "ocr markdown" / "Sec A.pdf").mkdir()           # empty
    (book / "Sec A.pdf" / "Sec A.pdf").write_bytes(b"%PDF")
    cmd_status(str(book))
    assert "With OCR: 0/1" in capsys.readouterr().out


def test_organize_section_leaves_unrelated_files_in_an_already_canonical_section(tmp_path):
    sec = tmp_path / "Sec A"
    sec.mkdir()
    (sec / "Sec A.pdf").write_bytes(b"%PDF")
    (sec / "my_clinical_notes.md").write_text("notes")
    (sec / "cdss_package_out").mkdir()
    cmd_organize_section(str(sec))
    assert (sec / "my_clinical_notes.md").exists() and (sec / "cdss_package_out").exists()
