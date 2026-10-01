"""Regression tests for Claude audit findings: real grounding gate, cleanroom copy, figures."""
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
from verify_grounding import verify_note_grounding  # noqa: E402

GOOD_NOTE = """# Cardiac murmurs
## Coverage Declaration
This note covers Davidson chapter 16 and Harrison part 5 material on murmurs.
## LAYER 2 — Davidson Core Spine
- Levine grade 4 murmurs have a palpable thrill [Anchor: Davidson-16-L2-045]
- Peripheral signs of aortic regurgitation are listed in Box 16.89
### Benign vs pathological
- Diastolic murmurs are always pathological [chunk: L2-046]
## QB Awareness / Exam Trap
- Acute severe MR may produce no murmur at all [Anchor: Harrison-5-L2-010]
## LAYER 5 — Active Recall
1. Which Levine grade has a thrill? [Anchor: Davidson-16-L2-045]
## Clinical Evidence Notes
- ESC 2021 gives a Class I recommendation for echocardiography in symptomatic murmurs.
"""


def make_package(root: Path) -> Path:
    pkg = root / "pkg"
    dav = pkg / "01_Davidson_25" / "Davidson_25_Ch16_Cardio"
    har = pkg / "02_Harrison_22" / "Parts"
    dav.mkdir(parents=True)
    har.mkdir(parents=True)
    (dav / "Davidson_25_Ch16_Cardio_RAG_Optimised.md").write_text(
        "---\nchunk_id: L2-045\n---\nGrade 4 has a thrill. See Box 16.89.\n---\nchunk_id: L2-046\n---\nDiastolic.\n",
        encoding="utf-8")
    (har / "Harrison_22_Part05_RAG_Optimised.md").write_text("---\nchunk_id: L2-010\n---\nAcute MR.\n", encoding="utf-8")
    return pkg


def check(tmp_path, text):
    note = tmp_path / "note.md"
    note.write_text(text, encoding="utf-8")
    return verify_note_grounding(note, make_package(tmp_path))


def test_good_note_passes(tmp_path):
    rep = check(tmp_path, GOOD_NOTE)
    assert rep["status"] == "PASS", rep["failures"]
    assert rep["citations_resolved"] == 5


def test_trivial_note_fails(tmp_path):
    assert check(tmp_path, "b\n")["status"] == "FAIL"


def test_uncited_claim_fails(tmp_path):
    rep = check(tmp_path, GOOD_NOTE.replace(" [chunk: L2-046]", ""))
    assert rep["status"] == "FAIL" and rep["uncited_lines"]


def test_nonexistent_chunk_fails(tmp_path):
    rep = check(tmp_path, GOOD_NOTE.replace("L2-045]", "L2-999]"))
    assert rep["status"] == "FAIL" and rep["unresolved_citations"]


def test_non_davidson_anchor_in_layer2_fails(tmp_path):
    rep = check(tmp_path, GOOD_NOTE.replace("[chunk: L2-046]", "[Anchor: Harrison-5-L2-010]"))
    assert rep["status"] == "FAIL"


def test_missing_box_fails(tmp_path):
    assert check(tmp_path, GOOD_NOTE.replace("Box 16.89", "Box 16.99"))["status"] == "FAIL"


def test_missing_package_fails(tmp_path):
    note = tmp_path / "note.md"
    note.write_text(GOOD_NOTE, encoding="utf-8")
    assert verify_note_grounding(note, tmp_path / "nope")["status"] == "FAIL"


def test_cli_exit_code(tmp_path):
    note = tmp_path / "note.md"
    note.write_text("b\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(SCRIPTS / "verify_grounding.py"), "-n", str(note), "-p", str(tmp_path)])
    assert r.returncode == 1


def test_publisher_keeps_source_and_fails_on_missing_image(tmp_path):
    pytest = __import__("pytest")
    pytest.importorskip("docx")
    from synthesize_bridge_note import run_pipeline
    pkg = make_package(tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    note = out / "Note_16.1_Cardiac_Murmurs_V2.2.md"
    src = GOOD_NOTE + "\n![ECG](figures/ecg.png)\n"
    note.write_text(src, encoding="utf-8")
    # grounding passes, but the referenced image is missing -> publishing must fail closed
    assert run_pipeline("Cardiac Murmurs", out, pkg, note_id="16.1") is False
    assert not (out / "Note_16.1_Cardiac_Murmurs_V2.2_Executive.docx").exists()
    # source note is never rewritten by the cleanroom step
    assert note.read_text(encoding="utf-8") == src
    # with the image present it publishes
    (out / "figures").mkdir()
    from PIL import Image
    Image.new("RGB", (300, 200), "white").save(out / "figures" / "ecg.png")
    assert run_pipeline("Cardiac Murmurs", out, pkg, note_id="16.1") is True
    assert (out / "Note_16.1_Cardiac_Murmurs_V2.2_Executive.docx").exists()
    assert note.read_text(encoding="utf-8") == src


def test_enhance_figures_copies_identical_and_png_stays_png(tmp_path):
    from PIL import Image
    other = Path(__file__).resolve().parents[2] / "cdss-retrieval-packager" / "scripts" / "enhance_figures.py"
    if other.exists():
        assert other.read_bytes() == (SCRIPTS / "enhance_figures.py").read_bytes()
    src = tmp_path / "in"
    src.mkdir()
    Image.new("RGB", (200, 100)).save(src / "rgb.png")
    Image.new("RGBA", (200, 100), (255, 0, 0, 128)).save(src / "alpha.png")
    Image.new("CMYK", (200, 100)).save(src / "cmyk.jpg")
    r = subprocess.run([sys.executable, str(SCRIPTS / "enhance_figures.py"), "-f", str(src), "-o", str(tmp_path / "o")])
    assert r.returncode == 0
    assert Image.open(tmp_path / "o" / "rgb.png").format == "PNG"
    assert Image.open(tmp_path / "o" / "alpha.png").format == "PNG"
    assert Image.open(tmp_path / "o" / "cmyk.jpg").format == "JPEG"


def test_free_text_provenance_and_table_headers(tmp_path):
    note = GOOD_NOTE.replace("## QB Awareness / Exam Trap\n", "## QB Awareness / Exam Trap\n"
        "| Term | Meaning | Provenance |\n| :--- | :--- | :--- |\n"
        "| Thrill | Palpable murmur vibration | Davidson Ch. 16 (Chunk L2-045) |\n"
        "- Acute MR can be silent [Anchor: Harrison Ch. 44, Fig. 44.4 / Chunk L2-010]\n")
    rep = check(tmp_path, note)
    assert not rep["uncited_lines"], rep["uncited_lines"]  # header row is not a claim
    # Fig. 44.4 is not in the Harrison fixture text -> unresolved (proves figure refs are checked per book)
    assert any("44.4" in u for u in rep["unresolved_citations"])


def test_chunk_outside_cited_chapter_fails(tmp_path):
    # L2-045 exists only in Davidson Ch 16; citing it as Ch 17 must fail when the book is chapter-numbered
    pkg = make_package(tmp_path)
    ch17 = pkg / "01_Davidson_25" / "Davidson_25_Ch17_Other"
    ch17.mkdir()
    (ch17 / "Davidson_25_Ch17_Other_RAG_Optimised.md").write_text("---\nchunk_id: L2-001\n---\nx\n---\nchunk_id: L2-045\n---\ny\n", encoding="utf-8")
    note = tmp_path / "n.md"
    note.write_text(GOOD_NOTE.replace("[Anchor: Davidson-16-L2-045]", "Davidson Ch. 18 (Chunk L2-045)"), encoding="utf-8")
    rep = verify_note_grounding(note, pkg)
    assert any("not in chapter 18" in u for u in rep["unresolved_citations"])
