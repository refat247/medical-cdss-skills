"""source_lines precision checker — constructed fixtures for each verdict,
plus a real-fixture check against Chapter 05's actual known-bad chunks
(L2-097 under-inclusive, L2-118 over-inclusive) confirming the tool
reproduces what the manual adjudication pass found by hand.
"""
import os
import re

from pipeline.stages.source_lines_precision import (
    check_chunk_precision, classify_precision, apply_corrections,
    segments_to_source_lines_string,
)


def _block(chunk_id, source_lines, body):
    return f'---\nchunk_id: {chunk_id}\nchunk_level: 2\nsource_lines: "{source_lines}"\n---\n\n{body}'


def test_precise_when_declared_span_matches_content_exactly():
    body = "This is a full sentence that genuinely exists in the source text right here."
    repaired = "filler line one\n" + body + "\nfiller line three\n"
    block = _block("L2-01", "2-2", body)
    result = check_chunk_precision(block, repaired)
    assert result["verdict"] == "PRECISE"


def test_under_inclusive_when_content_found_outside_declared_range():
    """Reproduces the L2-097 pattern: declared range too short, real
    content (a table) lives past the declared end line."""
    table_row = "A retinol Liver Milk and milk products eggs fish oils 700 micrograms men 600 micrograms women"
    repaired = "\n".join([
        "## Vitamins",
        "Vitamins are organic compounds with vital roles in metabolic pathways here.",
        table_row,
    ]) + "\n"
    body = "## Vitamins\n\nVitamins are organic compounds with vital roles in metabolic pathways here.\n\n" + table_row
    block = _block("L2-97", "1-2", body)  # declared range excludes line 3 (the table)
    result = check_chunk_precision(block, repaired)
    assert result["verdict"] in ("UNDER_INCLUSIVE", "UNDER_AND_OVER_INCLUSIVE")
    assert 3 in result["lines_matched_outside_declared"]


def test_over_inclusive_when_declared_range_sweeps_in_unrelated_content():
    """Reproduces the L2-118 pattern: declared range spans an unrelated
    interleaved block the chunk's own body doesn't contain."""
    body = (
        "There are a number of non-essential organic compounds with purported health benefits here today.\n\n"
        "Caffeine and related compounds in tea and coffee can improve mental performance in the short term."
    )
    repaired_lines = [
        "## Other bioactive dietary compounds",
        "There are a number of non-essential organic compounds with purported health benefits here today.",
        "",
        "## 5.36 Cause and clinical features of scurvy",
        "Swollen gums that bleed easily and other unrelated box content sits right here in between.",
        "More unrelated box content about clinical features of scurvy continues here as well.",
        "",
        "Caffeine and related compounds in tea and coffee can improve mental performance in the short term.",
    ]
    repaired = "\n".join(repaired_lines) + "\n"
    block = _block("L2-118", "1-8", body)  # declared range sweeps in lines 4-6 (the unrelated box)
    result = check_chunk_precision(block, repaired)
    assert result["verdict"] == "OVER_INCLUSIVE"
    assert result["suggested_segments"][0][1] < 8 or len(result["suggested_segments"]) > 1


def test_unresolved_when_too_few_anchors_match():
    body = "Completely different content that does not exist anywhere in the source file at all whatsoever."
    repaired = "totally unrelated source text with nothing in common here\n"
    block = _block("L2-99", "1-1", body)
    result = check_chunk_precision(block, repaired)
    assert result["verdict"] == "UNRESOLVED"


def test_classify_precision_directly_precise_case():
    result = classify_precision(
        declared_segments=[(10, 12)], matched_lines=[10, 11, 12],
        total_units=3, unmatched=0,
    )
    assert result["verdict"] == "PRECISE"


def test_classify_precision_directly_under_inclusive_case():
    result = classify_precision(
        declared_segments=[(10, 11)], matched_lines=[10, 11, 15],
        total_units=3, unmatched=0,
    )
    assert result["verdict"] == "UNDER_INCLUSIVE"
    assert 15 in result["lines_matched_outside_declared"]


def test_classify_precision_directly_over_inclusive_case():
    result = classify_precision(
        declared_segments=[(10, 30)], matched_lines=[10, 11, 29, 30],
        total_units=4, unmatched=0,
    )
    assert result["verdict"] == "OVER_INCLUSIVE"


def test_apply_corrections_rewrites_source_lines_field():
    chunks_text = _block("L2-01", "5-10", "some body text here")
    new_text, changed, unmatched = apply_corrections(chunks_text, {"L2-01": [(5, 6), (9, 10)]})
    assert changed == 1
    assert unmatched == []
    assert 'source_lines: "5-6,9-10"' in new_text  # v2.6.5 canonical format (no space)


def test_apply_corrections_reports_unmatched_chunk_id_loudly():
    chunks_text = _block("L2-01", "5-10", "body")
    new_text, changed, unmatched = apply_corrections(chunks_text, {"L2-99-does-not-exist": [(1, 2)]})
    assert changed == 0
    assert unmatched == ["L2-99-does-not-exist"]


def test_segments_to_source_lines_string_formats_multi_segment():
    """v2.6.5: format now delegates to the canonical
    stages.source_lines_parser serializer (comma-joined, no space,
    single-line segments as bare "N") instead of a local ad hoc format."""
    assert segments_to_source_lines_string([(3, 4), (8, 9)]) == "3-4,8-9"


def test_segments_to_source_lines_string_single_line_segment_has_no_dash():
    assert segments_to_source_lines_string([(5, 5)]) == "5"


# --- Real-fixture confirmation against Chapter 05's actual known-bad chunks ---

CH05_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "05")
FIXTURES_CH05_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "ch05_regression")


def _load_ch05_chunk(chunk_id):
    path = os.path.join(CH05_DIR, "Davidson_25_Ch05_Nutritional_factors_in_disease_chunks.md")
    if not os.path.exists(path):
        path = os.path.join(FIXTURES_CH05_DIR, "chunks_fixture.md")
    if not os.path.exists(path):
        pytest.skip("Ch05 chunks data not available")
    text = open(path, encoding="utf-8").read()
    blocks = re.findall(r'(---\nchunk_id:.*?\n---\n.*?)(?=\n---\nchunk_id:|\Z)', text, re.DOTALL)
    for b in blocks:
        if re.search(rf'chunk_id:\s*{re.escape(chunk_id)}\b', b):
            return b
    return None


def _ch05_repaired_s2():
    path = os.path.join(CH05_DIR, "Davidson_25_Ch05_Nutritional_factors_in_disease_REPAIRED_S2.md")
    if not os.path.exists(path):
        path = os.path.join(FIXTURES_CH05_DIR, "repaired_s2_fixture.md")
    if not os.path.exists(path):
        pytest.skip("Ch05 repaired text not available")
    return open(path, encoding="utf-8").read()


def test_real_ch05_l2_097_now_corrected_to_precise():
    """L2-097's source_lines was corrected ("1045-1058" -> "1045-1084",
    apply_source_lines_corrections_ch05.py) after this test originally
    caught the under-inclusive bug against real Chapter 05 data. Now
    confirms the fix stuck -- this chunk is no longer flagged."""
    block = _load_ch05_chunk("L2-097")
    assert block is not None
    result = check_chunk_precision(block, _ch05_repaired_s2())
    assert result["verdict"] == "PRECISE"


def test_real_ch05_l2_118_now_corrected_to_precise():
    """L2-118's source_lines was corrected ("1301-1305, 1307-1334" ->
    "1301-1307, 1334-1334", excising the unrelated Box 5.36 content) after
    this test originally caught the over-inclusive bug against real
    Chapter 05 data. Now confirms the fix stuck."""
    block = _load_ch05_chunk("L2-118")
    assert block is not None
    result = check_chunk_precision(block, _ch05_repaired_s2())
    assert result["verdict"] == "PRECISE"
