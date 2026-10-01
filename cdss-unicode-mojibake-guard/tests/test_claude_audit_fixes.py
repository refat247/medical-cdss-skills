"""Regression tests for Claude audit findings (source verbatim, output-only ISMP rewrites)."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import guard


LAB_AND_DOSE = ("Warfarin 5.0 mg; colchicine .5 mg; insulin 10 U; heparin 5000 IU QD; "
                "Hb 13.0 g/dL; K 4.0 mmol/L; BMI 30.0 kg/m2")


def test_source_text_is_kept_verbatim_by_fix():
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "source.md"
        f.write_text(LAB_AND_DOSE, encoding="utf-8")
        guard.fix_directory(Path(tmp))
        assert f.read_text(encoding="utf-8") == LAB_AND_DOSE


def test_output_rewrites_doses_but_not_lab_values():
    out = guard.sanitize_for_llm(LAB_AND_DOSE)
    assert "Warfarin 5 mg" in out
    assert "0.5 mg" in out
    assert "10 units" in out
    assert "5000 units once daily" in out
    assert "Hb 13.0 g/dL" in out
    assert "K 4.0 mmol/L" in out
    assert "BMI 30.0 kg/m2" in out


def test_cleanroom_applies_dose_rewrites():
    assert "5 mg once daily" in guard.cleanroom_docx_filter("Give 5.0 mg QD")


def test_ismp_findings_are_advisory_not_blocking():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "a.md").write_text(LAB_AND_DOSE, encoding="utf-8")
        res = guard.audit_directory(Path(tmp))
        assert res["status"] == "PASS"
        assert res["advisories"] and res["advisories"][0]["hits"] >= 3


def test_legacy_corruption_is_blocking():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "old.md").write_text("Creatinine 120 mcgmol/L; WBC 4-11 x 109/L", encoding="utf-8")
        assert guard.audit_directory(Path(tmp))["status"] == "FAIL"


def test_include_outputs_scans_rag_pipeline_output():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "Ch01" / "rag_pipeline_output"
        out.mkdir(parents=True)
        (out / "Ch01_RAG_Optimised.md").write_text("x 109/L", encoding="utf-8")
        assert guard.audit_directory(Path(tmp))["status"] == "PASS"
        assert guard.audit_directory(Path(tmp), include_outputs=True)["status"] == "FAIL"


def test_mixed_encoding_keeps_greek_and_superscripts():
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "mix.md"
        f.write_bytes("β-blocker; α1; 10⁹/L; Na⁺; ".encode("utf-8") + b"Fentanyl 50 \xb5g")
        guard.fix_directory(Path(tmp))
        text = f.read_text(encoding="utf-8")
        for s in ("β-blocker", "α1", "10⁹/L", "Na⁺", "50 µg"):
            assert s in text


def test_verbatim_corpus_symbols_are_not_blocking():
    """A trusted verbatim corpus (µg, ≥, pipeline LaTeX) must pass the gate; only real corruption blocks."""
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "c.md").write_text(r"Give 25 µg if K ≥ 5.5 and \( 0.5 \times 10^{9}/L \)", encoding="utf-8")
        res = guard.audit_directory(Path(tmp))
        assert res["status"] == "PASS" and res["advisories"]
        guard.fix_directory(Path(tmp))
        assert (Path(tmp) / "c.md").read_text(encoding="utf-8").startswith("Give 25 µg if K ≥ 5.5")


def test_mcgg_and_fraction_slash_are_legacy_corruption():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "k.md").write_text("Glucagon 50 to 150 mcgg/kg; take 1\u20442 tablet", encoding="utf-8")
        assert guard.audit_directory(Path(tmp))["status"] == "FAIL"


def test_latex_powers_of_ten_become_superscripts():
    out = guard.sanitize_for_llm(r"neutrophils \( <1.5 \times 10^{9}/L \) and 10^12/L; ref \( ^{18} \)")
    assert "10⁹/L" in out and "10¹²/L" in out and "109/L" not in out and "[18]" in out


def test_image_folders_are_skipped_by_audit_and_fix():
    bad = "WBC 4-11 x 109/L; creatinine 120 mcgmol/L; Âµg"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "Ch01_RAG_Optimised.md").write_text("clean text", encoding="utf-8")
        planted = []
        for d in ("assets", "figures", "pages", "images", "__pycache__"):
            sub = root / "Ch01" / d
            sub.mkdir(parents=True)
            fp = sub / "note.md"
            fp.write_text(bad, encoding="utf-8")
            planted.append(fp)
        result = guard.audit_directory(root, include_outputs=True)
        assert result["status"] == "PASS"
        assert result["total_scanned"] == 1
        assert guard.fix_directory(root) == 0
        assert all(fp.read_text(encoding="utf-8") == bad for fp in planted)
        # Control: the same text in an ordinary folder is still scanned and blocked.
        (root / "Ch01" / "notes").mkdir()
        (root / "Ch01" / "notes" / "note.md").write_text(bad, encoding="utf-8")
        assert guard.audit_directory(root, include_outputs=True)["status"] == "FAIL"


def test_spaced_mcg_g_and_mcg_mol_are_legacy_corruption():
    # "\mu g" / "\mu mol" became "mcg g" / "mcg mol" (with a space) in old pipeline output
    for bad in ("ferritin > 1000 mcg g/L", "creatinine greater than 177 mcg mol/L"):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "x.md").write_text(bad, encoding="utf-8")
            assert guard.audit_directory(Path(tmp))["status"] == "FAIL"
    for good in ("500 mcg given twice", "177 μmol/L", "1000 μg/L"):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "x.md").write_text(good, encoding="utf-8")
            assert guard.audit_directory(Path(tmp))["status"] == "PASS"
