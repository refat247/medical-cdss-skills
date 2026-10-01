"""Regression tests for Claude audit findings: federated script compiles, clause-safe compression,
figure link check, README reflects reality."""
import py_compile
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from packager import CDSSPackager, compress_excerpt  # noqa: E402


def test_generated_federated_script_compiles_and_runs(tmp_path):
    CDSSPackager(verbose=False).generate_federated_search(tmp_path)
    script = tmp_path / "cdss_federated_search.py"
    py_compile.compile(str(script), doraise=True)
    for extra in ([], ["--json"], ["--compress"]):
        r = subprocess.run([sys.executable, str(script), "--query", "AF"] + extra, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr


def test_compression_never_drops_exception_clause():
    s = ("Thrombolysis is contraindicated in patients with prior intracranial haemorrhage, known structural "
         "cerebral vascular lesion, or ischaemic stroke within 3 months except acute ischaemic stroke within 4.5 hours.")
    assert compress_excerpt(s, 150) == s
    two = "Give 0.5 mg IV. " + "Do not give if the patient is hypotensive unless a specialist advises otherwise. " * 3
    out = compress_excerpt(two.strip(), 60)
    assert out.startswith("Give 0.5 mg IV.") and out.endswith("[...]")
    assert "[truncated" in compress_excerpt("word " * 400, 150)


def test_figure_links_checked(tmp_path):
    ch = tmp_path / "01_Davidson_25" / "Ch16"
    (ch / "assets" / "figures").mkdir(parents=True)
    (ch / "assets" / "figures" / "a.jpeg").write_bytes(b"x")
    (ch / "Ch16_RAG_Optimised.md").write_text("![a](assets/figures/a.jpeg) assets/figures/b.jpeg", encoding="utf-8")
    assert CDSSPackager(verbose=False).verify_figure_links(tmp_path).startswith("FAIL (1 of 2")
    (ch / "assets" / "figures" / "b.jpeg").write_bytes(b"x")
    assert CDSSPackager(verbose=False).verify_figure_links(tmp_path).startswith("PASS")


def test_readme_has_no_hardcoded_production_claims(tmp_path):
    (tmp_path / "01_Davidson_25").mkdir()
    CDSSPackager(verbose=False).generate_readme(tmp_path)
    text = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "Production Ready" not in text and "1,972" not in text
    assert "Not packaged" in text
