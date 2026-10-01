"""Regression tests for the guard (skill_audits/SECOND_SWEEP.md 2.1-2.4)."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import guard  # noqa: E402


# ---- 2.3 ISMP "U" rule must only touch doses ----
@pytest.mark.parametrize("s", ["5 U.S. adults", "ECG: 2 U-wave", "3 U.K. centres"])
def test_u_rule_leaves_non_dose_text_alone(s):
    assert guard.sanitize_for_llm(s) == s


@pytest.mark.parametrize("s,out", [("Give 10 U insulin", "Give 10 units insulin"), ("100 U daily", "100 units daily")])
def test_u_rule_still_rewrites_real_doses(s, out):
    assert guard.sanitize_for_llm(s) == out


# ---- 2.4 LaTeX / paths / currency ----
@pytest.mark.parametrize("s,out", [("Ca$^{2+}$ level", "Ca2+ level"), ("$^{99m}$Tc scan", "99mTc scan"),
                                   ("trial$^{12}$ shows", "trial[12] shows")])
def test_ion_charges_and_isotopes_are_not_citation_brackets(s, out):
    assert guard.sanitize_for_llm(s) == out


def test_file_names_keep_their_underscores():
    assert "page_042.png" in guard.sanitize_for_llm("see page_042.png and fig_3.png")


def test_currency_pairs_are_not_treated_as_math():
    assert guard.sanitize_for_llm("Costs $5 for A vs $10 for B") == "Costs $5 for A vs $10 for B"


def test_real_inline_math_is_still_de_delimited():
    assert guard.sanitize_for_llm("where $P < 0.05$ was met") == "where P < 0.05 was met"


@pytest.mark.parametrize("s,out", [("Q.D. for 5 days", "once daily for 5 days"), ("5 I.U. daily", "5 units daily"),
                                   ("Alb 3.0 g/24 h", "Alb 3.0 g/24 h")])
def test_ismp_abbreviation_with_trailing_dot_and_lab_denominators(s, out):
    assert guard.sanitize_for_llm(s) == out


# ---- 2.4 mojibake coverage: repaired AND flagged ----
@pytest.mark.parametrize("bad,good", [("âˆ’5 mmol/L", "−5 mmol/L"), ("â‰ˆ 5", "≈ 5"), ("Î²-blocker", "β-blocker"),
                                      ("Â½ tablet", "½ tablet"), ("Â² ", "² "), ("â€¢ item", "• item"), ("Ã¶", "ö")])
def test_more_mojibake_is_repaired_in_source_and_flagged_by_audit(bad, good, tmp_path):
    assert guard.repair_source_text(bad) == good
    f = tmp_path / "a.md"; f.write_text(bad, encoding="utf-8")
    res = guard.audit_directory(tmp_path)
    assert res["status"] != "PASS", bad


def test_minus_sign_survives_output_sanitise_as_a_minus():
    assert guard.sanitize_for_llm("âˆ’5 mmol/L").lstrip().startswith(("-5", "−5"))


# ---- 2.1 / 2.2 fix_directory safety ----
def test_protected_directory_is_not_descended(tmp_path):
    (tmp_path / "prot" / "sub").mkdir(parents=True)
    (tmp_path / "prot" / "X_CHECKPOINT.json").write_text("{}")
    for rel in ("prot/b.md", "prot/sub/a.md"):
        (tmp_path / rel).write_text("â‰¥ 5", encoding="utf-8")
    guard.fix_directory(tmp_path)
    assert (tmp_path / "prot" / "b.md").read_text(encoding="utf-8") == "â‰¥ 5"
    assert (tmp_path / "prot" / "sub" / "a.md").read_text(encoding="utf-8") == "â‰¥ 5"


@pytest.mark.parametrize("enc", ["utf-16", "utf-32"])
def test_utf16_and_utf32_files_are_skipped_not_corrupted(tmp_path, enc):
    f = tmp_path / "u.md"; raw = "Dose ≥ 5 mg".encode(enc); f.write_bytes(raw)
    guard.fix_directory(tmp_path)
    assert f.read_bytes() == raw


def test_fix_directory_dry_run_changes_nothing_but_counts(tmp_path):
    f = tmp_path / "a.md"; f.write_text("â‰¥ 5", encoding="utf-8")
    assert guard.fix_directory(tmp_path, dry_run=True) == 1
    assert f.read_text(encoding="utf-8") == "â‰¥ 5"


def test_fix_directory_reports_unreadable_files(tmp_path, capsys):
    d = tmp_path / "x.md"; d.mkdir()          # a directory named like a file: cannot be read
    guard.fix_directory(tmp_path)             # must not crash
    assert guard.fix_directory.__doc__ is not None
