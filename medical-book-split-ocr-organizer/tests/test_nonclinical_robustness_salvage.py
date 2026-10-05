"""Filesystem-only OCR organizer robustness salvaged from PR #1."""
from scripts.organizer import cmd_ingest, cmd_organize_section, cmd_status


def _book(tmp_path, sections=("Sec A",)):
    book = tmp_path / "book"
    for section in sections:
        (book / f"{section}.pdf").mkdir(parents=True)
        (book / f"{section}.pdf" / "ocr markdown").mkdir()
    return book


def _ocr_download(tmp_path, name, with_file=True):
    d = tmp_path / "dl" / name
    d.mkdir(parents=True)
    if with_file:
        (d / "markdown.md").write_text("ocr text", encoding="utf-8")
    return d.parent


def test_ingest_into_existing_empty_destination_does_not_nest(tmp_path):
    book = _book(tmp_path)
    (book / "Sec A.pdf" / "ocr markdown" / "Sec A.pdf").mkdir()
    source = _ocr_download(tmp_path, "Sec A.pdf")
    cmd_ingest(str(book), source_dir=str(source))
    dest = book / "Sec A.pdf" / "ocr markdown" / "Sec A.pdf"
    assert (dest / "markdown.md").exists()
    assert not (dest / "Sec A.pdf").exists()


def test_force_overwrite_preserves_old_ocr_outside_live_slots(tmp_path):
    book = _book(tmp_path)
    old = book / "Sec A.pdf" / "ocr markdown" / "Sec A.pdf"
    old.mkdir()
    (old / "old.md").write_text("precious", encoding="utf-8")
    source = _ocr_download(tmp_path, "Sec A.pdf")

    cmd_ingest(str(book), source_dir=str(source), force=True)

    backup_dir = book / "Sec A.pdf" / "_replaced_backups"
    kept = [p for p in backup_dir.iterdir() if ".replaced-" in p.name]
    assert kept
    assert (kept[0] / "old.md").read_text(encoding="utf-8") == "precious"
    assert not [p for p in (book / "Sec A.pdf" / "ocr markdown").iterdir() if ".replaced-" in p.name]


def test_ingest_dry_run_moves_nothing(tmp_path):
    book = _book(tmp_path)
    source = _ocr_download(tmp_path, "Sec A.pdf")
    cmd_ingest(str(book), source_dir=str(source), dry_run=True)
    assert (source / "Sec A.pdf" / "markdown.md").exists()
    assert not (book / "Sec A.pdf" / "ocr markdown" / "Sec A.pdf").exists()


def test_fuzzy_match_prefers_longest_section(tmp_path):
    book = _book(tmp_path, sections=("Part 1 Cardiology Chapter 1", "Part 1 Cardiology Chapter 10"))
    source = _ocr_download(tmp_path, "Part 1 Cardiology Chapter 10 Heart Failure.pdf")
    cmd_ingest(str(book), source_dir=str(source))
    assert any((book / "Part 1 Cardiology Chapter 10.pdf" / "ocr markdown").iterdir())
    assert not any((book / "Part 1 Cardiology Chapter 1.pdf" / "ocr markdown").iterdir())


def test_status_ignores_empty_ocr_slot(tmp_path, capsys):
    book = _book(tmp_path)
    (book / "Sec A.pdf" / "ocr markdown" / "Sec A.pdf").mkdir()
    (book / "Sec A.pdf" / "Sec A.pdf").write_bytes(b"%PDF")
    cmd_status(str(book))
    assert "With OCR: 0/1" in capsys.readouterr().out


def test_organize_section_leaves_unrelated_files_in_canonical_section(tmp_path):
    sec = tmp_path / "Sec A"
    sec.mkdir()
    (sec / "Sec A.pdf").write_bytes(b"%PDF")
    (sec / "my_clinical_notes.md").write_text("notes", encoding="utf-8")
    (sec / "cdss_package_out").mkdir()

    cmd_organize_section(str(sec))

    assert (sec / "my_clinical_notes.md").exists()
    assert (sec / "cdss_package_out").exists()
