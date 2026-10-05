"""Stage 4B text hygiene must not NFKC-normalise clinical text (second-sweep finding 1.3).

NFKC rewrites superscripts/subscripts (10^9 -> 109, m^2 -> m2, CO2), vulgar fractions and the
micro sign, which silently changes clinical values.
"""
import pytest

from pipeline.stages.stage_4_parse import sanitize_chunk_text


@pytest.mark.parametrize(
    "s",
    ["Platelets 10⁹/L", "BSA 1.7 m²", "5 µg", "½ tablet", "CO₂ 24 mmol/L", "10⁶ IU", "℃"],
)
def test_clinical_glyphs_survive_stage4b_sanitizer(s):
    assert sanitize_chunk_text(s) == s


def test_ligatures_and_invisibles_are_still_cleaned():
    assert sanitize_chunk_text("ﬁrst line​﻿") == "first line"
