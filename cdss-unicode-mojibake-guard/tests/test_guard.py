"""
Unit tests for cdss-unicode-mojibake-guard skill.
"""

import sys
import tempfile
from pathlib import Path

# Add scripts directory to sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import guard

import re

def test_version():
    """Verify semantic version declaration."""
    assert re.match(r"^\d+\.\d+\.\d+$", guard.__version__)


def test_layer8_physics_and_cleanroom_docx():
    """Verify Layer 8 physics symbols and cleanroom-docx filter."""
    raw = r"$\Delta P$ with $\rho \cdot v$ and $V_{max} \approx 4\text{ m/s}$."
    filtered = guard.cleanroom_docx_filter(raw)
    assert r"\Delta" not in filtered
    assert r"\rho" not in filtered
    assert r"\cdot" not in filtered
    assert "Delta P" in filtered
    assert "Vmax" in filtered
    assert "~ 4 m/s" in filtered

def test_repair_mojibake():
    corrupted = "Serum digoxin â‰¥ 2.0 Âµg/L with â€” severe toxicity â€˜nauseaâ€™."
    repaired = guard.repair_mojibake(corrupted)
    assert "â‰¥" not in repaired
    assert ">=" in repaired
    assert "mcg" in repaired
    assert " - " in repaired

def test_sanitize_for_llm_ismp():
    # Test ISMP medication safety rule (microgram to mcg)
    text = "Starting dose: 10 µg or 25μg once daily if GFR ≥ 50 mL/min."
    sanitized = guard.sanitize_for_llm(text, enforce_ismp=True)
    assert "10 mcg" in sanitized
    assert "25mcg" in sanitized
    assert ">= 50" in sanitized
    assert "µg" not in sanitized
    assert "μg" not in sanitized
    assert "≥" not in sanitized

def test_strip_zero_width_and_bom():
    text_with_bom_and_zwsp = "\ufeffPatient\u200b presented with\u00ad dyspnoea."
    cleaned = guard.sanitize_for_llm(text_with_bom_and_zwsp)
    assert "\ufeff" not in cleaned
    assert "\u200b" not in cleaned
    assert "\u00ad" not in cleaned
    assert cleaned == "Patient presented with dyspnoea."

def test_clean_clinical_latex():
    """Verify Layer 7: Clinical LaTeX & Pseudo-Math De-Delimiter."""
    # Test heart sounds and valve components
    text1 = "Evaluation of $S_1$, $S_2$, $S_3$, and $S_4$ gallops with $A_2\\text{--}OS$ interval."
    cleaned1 = guard.clean_clinical_latex(text1)
    assert cleaned1 == "Evaluation of S1, S2, S3, and S4 gallops with A2-OS interval."

    # Test OCR inequality patterns in \( ... \) and $ ... $
    text2 = "Adults with age \\( \\geq 65 \\) years or LVEF ( \\( \\leq35\\% \\) ) and BMI $\\geq 30\\mathrm{kg} / \\mathrm{m}^2$."
    cleaned2 = guard.clean_clinical_latex(text2)
    assert ">= 65" in cleaned2
    assert "<= 35%" in cleaned2
    assert ">= 30" in cleaned2
    assert "\\" not in cleaned2
    assert "$" not in cleaned2

    # Test superscript references
    text3 = "Adipose tissue accumulation. \\( ^{18} \\) In addition, risk score.$^{1,119-121}$"
    cleaned3 = guard.clean_clinical_latex(text3)
    assert "[18]" in cleaned3
    assert "[1,119-121]" in cleaned3

def test_safe_json_dumps():
    data = {"dose": "10 mcg", "inequality": ">= 50", "temp": "37 deg C"}
    serialized = guard.safe_json_dumps(data)
    assert ">= 50" in serialized
    assert "\\u" not in serialized

def test_audit_and_fix_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create a corrupted file with mojibake and OCR LaTeX
        bad_file = tmp_path / "chapter_chunks.md"
        bad_file.write_text("Dose: 100 Âµg â‰¥ 50. Heart sound $S_2$ and \\( \\geq 65 \\).", encoding="utf-8")

        # 1. Audit should detect corruption
        res = guard.audit_directory(tmp_path)
        assert res["status"] == "FAIL"
        assert len(res["violations"]) == 1

        # 2. Fix directory
        fixed = guard.fix_directory(tmp_path)
        assert fixed == 1

        # 3. Re-audit should PASS
        res2 = guard.audit_directory(tmp_path)
        assert res2["status"] == "PASS"
        assert res2["clean_files"] == 1

        # Content verification: encoding damage repaired to the ORIGINAL characters; printed text and
        # LaTeX stay verbatim in source (they are normalised only in generated output)
        content = bad_file.read_text(encoding="utf-8")
        assert "100 µg ≥ 50" in content
        assert "Âµg" not in content and "â‰¥" not in content
        assert "$S_2$" in content
        assert "\\( \\geq 65 \\)" in content
        out = guard.sanitize_for_llm(content)
        assert "100 mcg >= 50" in out and "S2" in out and ">= 65" in out

def test_audit_claude_findings_regression():
    """Verify regressions reported in Claude audit are fixed."""
    # 1. Superscript preservation (NFC instead of NFKC)
    raw_platelets = "Platelet count: 150-400 x 10⁹/L and fraction ½ dose."
    sanitized_platelets = guard.sanitize_for_llm(raw_platelets)
    assert "10⁹/L" in sanitized_platelets
    assert "109/L" not in sanitized_platelets
    assert "½" in sanitized_platelets

    # 2. Approximation tilde preservation
    raw_tilde = "Incidence is ~5% to ~10% in elderly patients."
    sanitized_tilde = guard.sanitize_for_llm(raw_tilde)
    assert "~5%" in sanitized_tilde
    assert "~10%" in sanitized_tilde

    # 3. Snake_case word preservation (e.g., drug_dosing)
    raw_snake = "Review drug_dosing guidelines and heart_rate ranges."
    sanitized_snake = guard.clean_clinical_latex(raw_snake)
    assert "drug_dosing" in sanitized_snake
    assert "heart_rate" in sanitized_snake

    # 4. Mojibake Âµ before mol/L -> µmol/L (NOT mcgmol/L)
    raw_umol = "Creatinine: 120 Âµmol/L with dose 50 Âµg."
    sanitized_umol = guard.sanitize_for_llm(raw_umol)
    assert "120 µmol/L" in sanitized_umol
    assert "mcgmol" not in sanitized_umol
    assert "50 mcg" in sanitized_umol

    # 5. LaTeX \mu g -> mcg
    raw_latex_ug = r"Administer $62.5 \mu g$ or \( 12.5 \mu\text{g} \) daily."
    sanitized_latex_ug = guard.clean_clinical_latex(raw_latex_ug)
    assert "62.5 mcg" in sanitized_latex_ug
    assert "12.5 mcg" in sanitized_latex_ug

    # 6. Protected directory skipping in fix_directory
    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        prot_dir = root_dir / "protected_output"
        prot_dir.mkdir()
        (prot_dir / "CORPUS_OUTPUT_PROTECTED.json").write_text("{}", encoding="utf-8")
        corrupted_in_prot = prot_dir / "chapter_RAG_Optimised.md"
        corrupted_in_prot.write_text("Platelets 150 x 10⁹/L and Âµg", encoding="utf-8")

        regular_dir = root_dir / "raw_chapter"
        regular_dir.mkdir()
        corrupted_reg = regular_dir / "raw.md"
        corrupted_reg.write_text("Âµg â‰¥ 10", encoding="utf-8")

        fixed = guard.fix_directory(root_dir)
        assert fixed == 1
        # Protected file remains unmodified
        assert corrupted_in_prot.read_text(encoding="utf-8") == "Platelets 150 x 10⁹/L and Âµg"
        # Regular file was repaired to the original characters (source kept verbatim)
        assert "µg ≥ 10" in corrupted_reg.read_text(encoding="utf-8")

    # 7. LaTeX microgram vs micromole distinction
    raw_latex_umol = r"Serum creatinine: \( \mu \)mol/L and $\mu$mol/L with dose \( \mu \)g and $\mu$g."
    sanitized_latex_umol = guard.sanitize_for_llm(raw_latex_umol)
    assert "µmol/L and µmol/L" in sanitized_latex_umol
    assert "mcgmol" not in sanitized_latex_umol
    assert "mcg and mcg" in sanitized_latex_umol

    # 8. Checkpoint file prefix directory protection in fix_directory
    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        ch_dir = root_dir / "CH05_Chapter"
        ch_dir.mkdir()
        (ch_dir / "CH05_CHECKPOINT.json").write_text("{}", encoding="utf-8")
        corrupted_in_ch = ch_dir / "CH05_RAG_Optimised.md"
        corrupted_in_ch.write_text("Âµg", encoding="utf-8")

        fixed = guard.fix_directory(root_dir)
        assert fixed == 0
        assert corrupted_in_ch.read_text(encoding="utf-8") == "Âµg"

    # 9. CP1252 byte 0xB5 (µ) fallback decode in fix_directory
    with tempfile.TemporaryDirectory() as tmpdir:
        root_dir = Path(tmpdir)
        ch_dir = root_dir / "legacy_notes"
        ch_dir.mkdir()
        cp1252_file = ch_dir / "legacy.txt"
        # 0xB5 is 'µ' in CP1252, 0x67 is 'g' -> "50 µg"
        cp1252_file.write_bytes(b"Dose: 50 \xb5g\r\n")

        fixed = guard.fix_directory(root_dir)
        assert fixed == 1
        cleaned_text = cp1252_file.read_text(encoding="utf-8")
        assert "50 µg" in cleaned_text
        assert "\ufffd" not in cleaned_text

    # 10. Mixed UTF-8 + CP1252 stray byte without Greek letter corruption
    raw_mixed = "β-blocker and α1-antitrypsin with 10⁹/L platelets and dose: 50 ".encode("utf-8") + b"\xb5g"
    decoded_mixed = guard.safe_decode_text(raw_mixed)
    assert "β-blocker" in decoded_mixed
    assert "α1-antitrypsin" in decoded_mixed
    assert "10⁹/L" in decoded_mixed
    assert "50 µg" in decoded_mixed
    assert "Î²" not in decoded_mixed

    sanitized_mixed = guard.sanitize_for_llm(decoded_mixed)
    assert "β-blocker" in sanitized_mixed
    assert "α1-antitrypsin" in sanitized_mixed
    assert "10⁹/L" in sanitized_mixed
    assert "50 mcg" in sanitized_mixed

    # 11. Currency phrase preservation ($5 to $10)
    raw_currency = "Treatment cost ranges from $5 to $10 per day, or $100 annually."
    cleaned_curr = guard.clean_clinical_latex(raw_currency)
    assert "$5 to $10" in cleaned_curr
    assert "$100" in cleaned_curr

    # 12. ISMP clinical rules: trailing zeros, leading decimals, abbreviations
    raw_ismp = "Give 5.0 mg or .5 mg QD or 10 U / 100 IU insulin."
    sanitized_ismp = guard.sanitize_for_llm(raw_ismp)
    assert "5 mg" in sanitized_ismp
    assert "0.5 mg" in sanitized_ismp
    assert "once daily" in sanitized_ismp
    assert "10 units" in sanitized_ismp
    assert "100 units" in sanitized_ismp
    assert "5.0 mg" not in sanitized_ismp
    assert " .5 mg" not in sanitized_ismp
    assert "QD" not in sanitized_ismp
    assert "IU" not in sanitized_ismp





def test_review_regressions_latex_and_ismp_day():
    import guard
    assert guard.clean_clinical_latex("10$^{3}$/uL") == "10³/uL"
    assert guard.clean_clinical_latex("37$^{\\circ}$C") == "37°C"
    assert "\\" not in guard.clean_clinical_latex("IL-1$^{\\beta}$")
    assert guard.apply_ismp_dose_rewrites("warfarin 5.0 mg/day") == "warfarin 5 mg/day"
    assert guard.apply_ismp_dose_rewrites("Hb 13.0 g/dL") == "Hb 13.0 g/dL"
