"""v2.6.4 -- Corpus-Scale Gate Closure, MUST-FIX #1: Stage 2 MCQ content-loss.

Chapter 05's real checkpoint records a piracy-removal sweep that deleted
MCQ 5.1's stem and its five options because the OLD `is_clinical()` guard
did not recognize decimal-numbered stems ("5.1.") or dash-prefixed options
("- A."). See `pipeline/stages/stage_2_repair.py`'s module docstring for the full
root-cause writeup. Every test here proves the protected block survives
byte-for-byte (or, where noted, that legitimate non-clinical content is
still correctly removable -- the fix must not become a blanket "never
delete anything numbered" regression).
"""
import re

from pipeline.stages.stage_2_repair import is_clinical, repair_stage2, PIRACY_TRIGGERS


def _piracy_block_with(clinical_tail):
    """A minimal, realistic piracy/watermark trigger block (Bengali text +
    "Medical Higher Study", matching the actual Chapter 05/02 source shape)
    immediately followed by `clinical_tail` -- close enough (within the
    10-line-before/15-line-after sweep window) to be at risk of being swept
    if `is_clinical()` doesn't protect it."""
    return (
        "Some preceding prose paragraph that is not clinical content at all.\n\n"
        "বাংলা বাংলা বাংলা বাংলা বাংলা\n\n"
        "Medical Higher Study\n\n"
        "Get it on\nGoogle Play\n\n"
        "## Multiple Choice Questions\n\n"
        + clinical_tail
    )


# --- is_clinical() unit tests: each required MCQ line shape ---

def test_decimal_numbered_mcq_stem_is_clinical():
    assert is_clinical("5.1. Which of the following drugs acts on a transporter protein?")


def test_multilevel_decimal_mcq_stem_is_clinical():
    assert is_clinical("5.1.2. A sub-numbered stem shape some editions use.")


def test_dash_prefixed_option_dot_is_clinical():
    assert is_clinical("- A. Gliclazide")


def test_dash_prefixed_option_paren_is_clinical():
    assert is_clinical("- A) Gliclazide")


def test_ordinary_option_dot_is_clinical():
    assert is_clinical("A. Gliclazide")


def test_ordinary_option_paren_is_clinical():
    assert is_clinical("A) Gliclazide")


def test_bare_single_level_numbered_item_still_clinical_no_regression():
    """The OLD guard's one correct case (plain numbered list item, e.g. a
    prescribing-steps list) must still be protected after widening the regex."""
    assert is_clinical("1. Consider factors that might influence the patient's response to therapy")


def test_legitimate_non_clinical_numbered_prose_is_still_removable():
    """A plain decimal-looking measurement in flowing prose ("1.5 million")
    has no trailing period before the space -- must NOT be mistaken for an
    MCQ-stem shape ("5.1. ") and must remain correctly unprotected, i.e.
    still removable by the piracy sweep if it happens to sit in a triggered
    window (it isn't itself clinical content worth protecting)."""
    assert not is_clinical("1.5 million people were affected by this condition in 2020, a promotional note.")


def test_bare_page_number_is_still_removable():
    assert not is_clinical("247")


# --- repair_stage2() integration tests: full piracy-sweep behavior ---

def test_decimal_stem_and_options_survive_piracy_sweep_near_boundary():
    text = _piracy_block_with(
        "5.1. Which of the following drugs for type 2 diabetes acts on a transporter protein?\n\n"
        "- A. Gliclazide\n"
        "- B. Dapagliflozin\n"
        "- C. Metformin hydrochloride\n\n"
        "Answer: B.\n"
    )
    repaired, report, stats = repair_stage2(text)
    assert "5.1. Which of the following drugs for type 2 diabetes acts on a transporter protein?" in repaired
    assert "- A. Gliclazide" in repaired
    assert "- B. Dapagliflozin" in repaired
    assert "- C. Metformin hydrochloride" in repaired
    assert "Answer: B." in repaired
    # the piracy junk itself must still be gone
    assert "Medical Higher Study" not in repaired
    assert "Google Play" not in repaired


def test_multilevel_decimal_stem_survives_piracy_sweep():
    text = _piracy_block_with(
        "5.1.2. A sub-numbered stem shape near the piracy boundary.\n\n"
        "- A. Option one\n- B. Option two\n\nAnswer: A.\n"
    )
    repaired, report, stats = repair_stage2(text)
    assert "5.1.2. A sub-numbered stem shape near the piracy boundary." in repaired
    assert "- A. Option one" in repaired


def test_historical_chapter_05_failure_shape_now_preserved():
    """Reproduces the exact historical Chapter 05 shape (Bengali text +
    'Medical Higher Study' + Google Play/App Store block immediately
    preceding an MCQ stem+options) end-to-end, and proves the protected
    block survives byte-for-byte."""
    stem_and_options = (
        "5.1. A 68-year-old woman taking warfarin for atrial fibrillation is\n"
        "prescribed a new antibiotic for a urinary tract infection. Which of the\n"
        "following antibiotics is most likely to potentiate the effect of warfarin?\n\n"
        "- A. Amoxicillin\n"
        "- B. Erythromycin\n"
        "- C. Cefalexin\n"
        "- D. Nitrofurantoin\n"
        "- E. Trimethoprim\n\n"
        "Answer: E.\n\n"
        "Trimethoprim inhibits the metabolism of warfarin via CYP2C9, increasing INR."
    )
    text = (
        "Some ordinary chapter prose immediately before the watermark junk begins here.\n\n"
        "বাংলা বাংলা বাংলা বাংলা বাংলা\n\n"
        "Medical Higher Study\n\n"
        "Get it on\nGoogle Play\n\n"
        "Download on the\nApp Store\n\n"
        "medicalhigherstudy.com\n\n"
        "## Multiple Choice Questions\n\n"
        + stem_and_options
    )
    repaired, report, stats = repair_stage2(text)
    assert stem_and_options in repaired, (
        "Historical Chapter 05 MCQ-sweep shape regressed -- protected clinical "
        "block did not survive byte-for-byte."
    )
    assert "Medical Higher Study" not in repaired
    assert "medicalhigherstudy.com" not in repaired
    assert stats["piracy_lines_removed"] > 0


def test_no_regression_in_existing_piracy_removal_when_no_mcq_nearby():
    """A piracy block with no MCQ content nearby at all must still be fully
    swept, exactly as before -- the fix must not make the sweep weaker in
    the ordinary case."""
    text = (
        "Ordinary prose paragraph one, nothing clinical here at all really.\n\n"
        "বাংলা বাংলা বাংলা বাংলা বাংলা\n\n"
        "Medical Higher Study\n\n"
        "Get it on\nGoogle Play\n\n"
        "Download on the\nApp Store\n\n"
        "medicalhigherstudy.com\n\n"
        "## Some Later Section\n\n"
        "More ordinary prose that follows the piracy block by a wide margin.\n"
    )
    repaired, report, stats = repair_stage2(text)
    assert "Medical Higher Study" not in repaired
    assert "Google Play" not in repaired
    assert "App Store" not in repaired
    assert "medicalhigherstudy.com" not in repaired
    assert stats["piracy_lines_removed"] > 0
    assert "## Some Later Section" in repaired


def test_real_chapter_02_source_still_repairs_cleanly():
    """Regression guard against the REAL Chapter 02 source shape (dash-
    prefixed options, piracy block immediately before the MCQ heading) --
    confirms the fix doesn't disturb the one real chapter that already
    passed this stage under the old code."""
    import os
    ch02_source = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "02",
        "Davidson_25_Ch02_Clinical_therapeutics_and_good_prescribing_REPAIRED_S2.md",
    )
    if not os.path.exists(ch02_source):
        import pytest
        pytest.skip("Real Chapter 02 REPAIRED_S2.md not present in this environment")
    text = open(ch02_source, encoding="utf-8").read()
    # Re-running repair_stage2 on an already-repaired file should be idempotent
    # in the sense that no further piracy triggers remain to sweep.
    repaired, report, stats = repair_stage2(text)
    assert "Multiple Choice Questions" in repaired
    # Q2.1's own stem + option A are genuinely absent from the source itself
    # (confirmed during Stage 4B chunking of the real chapter -- not a Stage 2
    # sweep artifact); option B onward is present and dash-prefixed, exactly
    # the shape this fix protects.
    assert "- B. Dapagliflozin" in repaired
    assert stats["piracy_lines_removed"] == 0  # already clean, nothing left to sweep
