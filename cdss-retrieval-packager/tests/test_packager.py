import sys
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


