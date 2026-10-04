import sys
import pytest
from pathlib import Path
from PIL import Image

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from packager import CDSSPackager
from enhance_figures import enhance_figure



def test_prune_directory_preserves_trust_files_and_midname_suffixes(tmp_path):
    """Verify that CORPUS_OUTPUT_PROTECTED and files like notes.bak.md are preserved."""
    packager = CDSSPackager(verbose=False)

    # 1. Protected trust files
    prot_file1 = tmp_path / "CORPUS_OUTPUT_PROTECTED.json"
    prot_file1.write_text("{}", encoding="utf-8")
    prot_file2 = tmp_path / "CORPUS_TRUST_STATUS.md"
    prot_file2.write_text("# Trust Status", encoding="utf-8")

    # 2. Files with .bak or .zip inside their names, but not actual backup/zip archives
    not_a_bak = tmp_path / "notes.bak.md"
    not_a_bak.write_text("markdown", encoding="utf-8")
    not_a_zip = tmp_path / "summary.zip.txt"
    not_a_zip.write_text("text", encoding="utf-8")

    # 3. Genuine files that SHOULD be pruned
    actual_bak = tmp_path / "old_backup.bak"
    actual_bak.write_text("old", encoding="utf-8")
    actual_zip = tmp_path / "archive.zip"
    actual_zip.write_text("zip", encoding="utf-8")
    actual_scorecard = tmp_path / "QualityScorecard.json"
    actual_scorecard.write_text("{}", encoding="utf-8")

    deleted = packager.prune_directory(tmp_path)
    assert deleted == 3

    # Verify preservation
    assert prot_file1.exists()
    assert prot_file2.exists()
    assert not_a_bak.exists()
    assert not_a_zip.exists()

    # Verify pruned
    assert not actual_bak.exists()
    assert not actual_zip.exists()
    assert not actual_scorecard.exists()


def test_enhance_figure_la_and_rgba(tmp_path):
    """Verify enhance_figure correctly converts LA and RGBA images without error."""
    # 1. Create an LA (luminance-alpha) image
    la_img = Image.new("LA", (100, 100), color=(128, 200))
    la_path = tmp_path / "test_la.png"
    la_img.save(la_path)

    la_out = tmp_path / "enhanced_la.jpeg"
    assert enhance_figure(la_path, la_out, scale_factor=2) is True
    assert la_out.exists()

    # 2. Create an RGBA image with transparent pixels
    rgba_img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    rgba_path = tmp_path / "test_rgba.png"
    rgba_img.save(rgba_path)

    rgba_out = tmp_path / "enhanced_rgba.jpeg"
    assert enhance_figure(rgba_path, rgba_out, scale_factor=2) is True
    assert rgba_out.exists()


def test_generate_federated_search_has_compress(tmp_path):
    """Verify that generated cdss_federated_search.py script defines and supports --compress."""
    packager = CDSSPackager(verbose=False)
    fed_script = packager.generate_federated_search(tmp_path)
    assert fed_script.exists()
    content = fed_script.read_text(encoding="utf-8")
    assert "--compress" in content
    assert "compress: bool = False" in content
    assert "def compress_excerpt" in content


def test_compress_excerpt_boundaries():
    from packager import compress_excerpt
    # 1. Short text unchanged
    assert compress_excerpt("Short text.", max_chars=50) == "Short text."

    # 2. Sentence boundary preservation
    text = "Platelet count: 150-400 x 10⁹/L. Administer aspirin 75 mg daily."
    comp = compress_excerpt(text, max_chars=40)
    assert comp == "Platelet count: 150-400 x 10⁹/L. [...]"  # " [...]" marks omitted later sentences
    assert "Adminis" not in comp

    # 3. A single sentence is never cut mid-clause (the qualifier must survive), up to the hard cap
    long_sentence = "Do not administer beta-blockers in severe cardiogenic shock or decompensated heart failure."
    comp2 = compress_excerpt(long_sentence, max_chars=45)
    assert comp2 == long_sentence




# ---- second-sweep 2.11: abbreviation periods are not sentence ends (a dose was dropped after "i.v.") ----
def test_compress_excerpt_does_not_cut_after_iv_abbreviation():
    from packager import compress_excerpt
    out = compress_excerpt("Start heparin i.v. 80 U/kg bolus then 18 U/kg/h and monitor aPTT closely every six hours. "
                           "Do not give if platelet count is low.", 60)
    assert "80 U/kg" in out and "18 U/kg/h" in out


@pytest.mark.parametrize("txt,must", [
    ("Give approx. 5 mg orally twice daily for seven days then review in clinic with bloods. Stop if rash.", "5 mg"),
    ("Give 2 g p.o. 6-hourly for ten days in total, adjusting for renal function as needed. Review weekly.", "6-hourly"),
    ("Administer 10 mg s.c. daily vs. 5 mg b.d. in elderly patients with impaired renal clearance. Monitor.", "10 mg"),
])
def test_compress_excerpt_keeps_doses_after_abbreviations(txt, must):
    from packager import compress_excerpt
    assert must in compress_excerpt(txt, 40)


def test_compress_excerpt_still_cuts_at_real_sentence_ends():
    from packager import compress_excerpt
    out = compress_excerpt("Aspirin is first line. " + "Then more text follows here. " * 20, 30)
    assert out.startswith("Aspirin is first line.") and out.endswith("[...]")


# ---- second-sweep 2.10 / 2.13: generated federated search ----
def _generate(tmp_path):
    pk = CDSSPackager(verbose=False)
    return pk.generate_federated_search(tmp_path)


def _router(book_tag, fail=False):
    return (f"class {'HarrisonCDSSRouter' if book_tag == 'HAR' else 'CDSSRouter'}:\n"
            f"    TAG = '{book_tag}'\n"
            "    def retrieve_chunks(self, query, top_k=3, compress=False):\n"
            + ("        raise RuntimeError('db locked')\n" if fail else
               f"        return [{{'chunk_id': '{book_tag}-1', 'section': 's', 'topic': 't', 'score': 1, 'excerpt': 'text {book_tag}'}}]\n"))


def _make_pkg(tmp_path, hurst_fails=False):
    for d, tag, fail in [("02_Harrison_22", "HAR", False), ("03_Hurst_The_Heart_15", "HU", hurst_fails), ("04_Kumar_and_Clark_11", "KC", False)]:
        (tmp_path / d / "Index").mkdir(parents=True)
        (tmp_path / d / "Index" / "cdss_qa_router.py").write_text(_router(tag, fail), encoding="utf-8")
    return _generate(tmp_path)


def test_generated_search_keeps_each_books_router_separate(tmp_path):
    import importlib.util
    script = _make_pkg(tmp_path)
    spec = importlib.util.spec_from_file_location("gen_search_a", str(script))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    eng = mod.CDSSFederatedSearch()
    first = eng.search("x", book="all")
    again = eng.search("x", book="harrison")          # a long-lived caller searching again
    assert first["Harrison_22"][0]["chunk_id"] == "HAR-1"
    assert first["Hurst_The_Heart_15"][0]["chunk_id"] == "HU-1"
    assert first["Kumar_and_Clark_11"][0]["chunk_id"] == "KC-1"
    assert again["Harrison_22"][0]["chunk_id"] == "HAR-1"       # used to come back as KUMAR/KC


def test_generated_search_reports_a_failing_book_and_exits_nonzero(tmp_path):
    import subprocess
    script = _make_pkg(tmp_path, hurst_fails=True)
    r = subprocess.run([sys.executable, str(script), "--query", "x"], capture_output=True, text=True)
    assert r.returncode == 1
    assert "db locked" in r.stdout + r.stderr
    assert "RETRIEVAL FAILED" in r.stdout and "[HURST_THE_HEART_15] - 1 Evidence" not in r.stdout   # the error is not counted as a chunk


def test_generated_search_contains_a_working_compress_excerpt(tmp_path):
    import importlib.util
    script = _make_pkg(tmp_path)
    spec = importlib.util.spec_from_file_location("gen_search_b", str(script))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    assert "80 U/kg" in mod.compress_excerpt("Start heparin i.v. 80 U/kg bolus then 18 U/kg/h and monitor aPTT closely every six hours. Stop.", 60)


def test_generated_search_rejects_nonpositive_top_k(tmp_path):
    import subprocess
    script = _make_pkg(tmp_path)
    assert subprocess.run([sys.executable, str(script), "--query", "x", "-k", "-1"], capture_output=True).returncode == 2


# ---- second-sweep 2.12 / 2.13: prune safety, verify exit codes, patch-paths residue ----
def test_prune_dry_run_deletes_nothing(tmp_path):
    (tmp_path / "Ch1_CHECKPOINT.json").write_text("{}"); (tmp_path / "x.zip").write_text("z")
    n = CDSSPackager(verbose=False).prune_directory(tmp_path, dry_run=True)
    assert n == 2 and (tmp_path / "Ch1_CHECKPOINT.json").exists() and (tmp_path / "x.zip").exists()


def test_prune_can_keep_trust_evidence(tmp_path):
    for f in ("Ch1_CHECKPOINT.json", "Ch1_ClinicalFidelityGate.json", "Ch1_Stage6_Validation.md", "junk.zip"):
        (tmp_path / f).write_text("x")
    CDSSPackager(verbose=False).prune_directory(tmp_path, keep_trust_evidence=True)
    assert (tmp_path / "Ch1_CHECKPOINT.json").exists() and (tmp_path / "Ch1_ClinicalFidelityGate.json").exists()
    assert (tmp_path / "Ch1_Stage6_Validation.md").exists() and not (tmp_path / "junk.zip").exists()


def test_verify_on_empty_package_exits_nonzero(tmp_path):
    import subprocess
    r = subprocess.run([sys.executable, str(SCRIPTS_DIR / "packager.py"), "verify", "-p", str(tmp_path)], capture_output=True, text=True)
    assert r.returncode != 0


def test_verify_on_missing_directory_exits_nonzero(tmp_path):
    import subprocess
    r = subprocess.run([sys.executable, str(SCRIPTS_DIR / "packager.py"), "verify", "-p", str(tmp_path / "nope")], capture_output=True, text=True)
    assert r.returncode != 0


def test_patch_paths_reports_residual_hardcoded_paths(tmp_path):
    (tmp_path / "cdss_qa_router.py").write_text('BASE = r"D:\\\\somewhere\\\\else"\nINDEX_DIR = r"E:\\\\other"\n')
    pk = CDSSPackager(verbose=False)
    pk.patch_paths(tmp_path)
    assert pk.remaining_hardcoded and "cdss_qa_router.py" in pk.remaining_hardcoded[0]
