"""Canonical source_lines parser tests (v2.6.5 emergency fix).

These were written as genuine RED tests against the four pre-v2.6.5 buggy
implementations (see pipeline/stages/source_lines_parser.py's module docstring and
_v2_6_5_evidence/RED_parser_diagnosis.txt for the captured failing-state
evidence) before pipeline/stages/source_lines_parser.py existed. They now exercise
the canonical shared implementation and must all pass.
"""
import pytest

from pipeline.stages.source_lines_parser import (
    parse_source_lines, parse_source_lines_from_block, serialize_source_lines,
    resolve_span_text, extract_source_lines_value, SourceLinesParseError,
)


# ---------------------------------------------------------------------------
# The 5 required inputs from the v2.6.5 task spec -- every segment must
# survive parsing, in normalized (sorted, deduplicated) order.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected_segments", [
    ("281", [(281, 281)]),
    ("1049-1053,1095", [(1049, 1053), (1095, 1095)]),
    ("1049,1051-1053", [(1049, 1049), (1051, 1053)]),
    ("1049-1053,1095,1101-1104", [(1049, 1053), (1095, 1095), (1101, 1104)]),
    ("1049 - 1053, 1095", [(1049, 1053), (1095, 1095)]),
])
def test_required_inputs_preserve_every_segment(raw, expected_segments):
    result = parse_source_lines(raw)
    assert result.ok, f"unexpected errors for {raw!r}: {result.errors}"
    assert result.segments == expected_segments


def test_single_line_value_not_dropped():
    """The core historical bug: '281' (no hyphen) must resolve to a real
    segment, not an empty list / None / a 5-word context fallback."""
    result = parse_source_lines("281")
    assert result.segments == [(281, 281)]
    assert result.line_set() == [281]


def test_trailing_comma_single_line_segment_not_dropped():
    """The exact Chapter 14 L2-1003 pattern: '1049-1053,1095' must keep
    line 1095, not silently truncate to just the hyphenated range."""
    result = parse_source_lines("1049-1053,1095")
    assert (1095, 1095) in result.segments


def test_leading_single_line_segment_before_a_range_not_dropped():
    result = parse_source_lines("1049,1051-1053")
    assert (1049, 1049) in result.segments


def test_multiple_trailing_segments_all_preserved():
    """run_stage_4_5d.py's old _l1_span() dropped EVERY segment after the
    first; the canonical parser must keep all three here."""
    result = parse_source_lines("1049-1053,1095,1101-1104")
    assert result.segments == [(1049, 1053), (1095, 1095), (1101, 1104)]


def test_whitespace_variations_tolerated():
    a = parse_source_lines("1049 - 1053, 1095")
    b = parse_source_lines("1049-1053,1095")
    assert a.segments == b.segments


# ---------------------------------------------------------------------------
# Malformed inputs -- must be explicitly detected, never silently coerced
# into a plausible-looking wrong answer.
# ---------------------------------------------------------------------------

def test_empty_value_returns_no_segments_no_error():
    result = parse_source_lines("")
    assert result.segments == []
    assert result.ok


def test_none_value_returns_no_segments_no_error():
    result = parse_source_lines(None)
    assert result.segments == []
    assert result.ok


def test_non_numeric_token_is_a_recorded_error():
    result = parse_source_lines("abc")
    assert result.segments == []
    assert result.errors


def test_reversed_range_is_rejected_not_silently_swapped():
    """'1053-1049' (start > end) must NOT become (1049, 1053) by silent
    correction -- that would hide a real metadata defect. It must be
    excluded from segments and recorded as an error."""
    result = parse_source_lines("1053-1049")
    assert result.segments == []
    assert any("reversed" in e for e in result.errors)


def test_double_dash_is_malformed():
    result = parse_source_lines("1049--1053")
    assert result.segments == []
    assert result.errors


def test_dangling_dash_start_missing_is_malformed():
    result = parse_source_lines("-1053")
    assert result.segments == []
    assert result.errors


def test_dangling_dash_end_missing_is_malformed():
    result = parse_source_lines("1049-")
    assert result.segments == []
    assert result.errors


def test_double_comma_blank_segment_is_not_an_error_surrounding_tokens_still_parse():
    """A blank segment from a double comma isn't itself malformed content
    (nothing was lost) -- but it must not swallow the valid neighbors."""
    result = parse_source_lines("1049,,1053")
    assert result.segments == [(1049, 1049), (1053, 1053)]
    assert result.ok


def test_ambiguous_multi_dash_no_comma_token_is_rejected_not_partially_matched():
    """The old buggy regex (re.findall over the whole string) incorrectly
    extracted (1049, 1053) out of this garbage via substring matching. The
    canonical parser tokenizes on commas first and requires each token to
    cleanly match one grammar -- this token matches neither, so it must be
    rejected outright, not partially parsed into something plausible."""
    result = parse_source_lines("1049- 1053-1060")
    assert result.segments == []
    assert result.errors


def test_strict_mode_raises_on_any_malformed_token():
    with pytest.raises(SourceLinesParseError):
        parse_source_lines("1053-1049", strict=True)


def test_strict_mode_does_not_raise_on_clean_input():
    result = parse_source_lines("1049-1053,1095", strict=True)
    assert result.segments == [(1049, 1053), (1095, 1095)]


# ---------------------------------------------------------------------------
# Normalization: ordering + duplicate removal
# ---------------------------------------------------------------------------

def test_out_of_order_input_is_sorted():
    result = parse_source_lines("1095,281,1049-1053")
    assert result.segments == [(281, 281), (1049, 1053), (1095, 1095)]


def test_duplicate_segments_are_deduplicated():
    result = parse_source_lines("50,50,50")
    assert result.segments == [(50, 50)]


def test_overlapping_ranges_are_merged():
    result = parse_source_lines("100-105,103-110")
    assert result.segments == [(100, 110)]


def test_adjacent_ranges_are_merged():
    result = parse_source_lines("100-105,106-110")
    assert result.segments == [(100, 110)]


def test_line_set_expands_all_segments():
    result = parse_source_lines("1-2,5")
    assert result.line_set() == [1, 2, 5]


# ---------------------------------------------------------------------------
# Deterministic serialization (round-trip)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw", [
    "281",
    "1049-1053,1095",
    "1049,1051-1053",
    "1049-1053,1095,1101-1104",
])
def test_serialize_round_trips(raw):
    parsed = parse_source_lines(raw)
    serialized = serialize_source_lines(parsed.segments)
    reparsed = parse_source_lines(serialized)
    assert reparsed.segments == parsed.segments


def test_serialize_is_deterministic_regardless_of_input_order():
    a = serialize_source_lines([(1095, 1095), (281, 281), (1049, 1053)])
    b = serialize_source_lines([(281, 281), (1049, 1053), (1095, 1095)])
    assert a == b == "281,1049-1053,1095"


def test_serialize_single_line_segment_has_no_dash():
    assert serialize_source_lines([(281, 281)]) == "281"


# ---------------------------------------------------------------------------
# Full-block extraction + span-text resolution
# ---------------------------------------------------------------------------

def test_extract_source_lines_value_from_full_block():
    block = '---\nchunk_id: L2-01\nchunk_level: 2\nsource_lines: "1049-1053,1095"\n---\n\nbody'
    assert extract_source_lines_value(block) == "1049-1053,1095"


def test_extract_source_lines_value_absent_returns_none():
    block = '---\nchunk_id: L2-01\nchunk_level: 2\n---\n\nbody'
    assert extract_source_lines_value(block) is None


def test_parse_source_lines_from_block_end_to_end():
    block = '---\nchunk_id: L2-01\nchunk_level: 2\nsource_lines: "1049,1051-1053"\n---\n\nbody'
    result = parse_source_lines_from_block(block)
    assert result.segments == [(1049, 1049), (1051, 1053)]


def test_resolve_span_text_returns_every_declared_line_including_trailing_single_line():
    """This is THE regression test for the false-negative risk: the
    resolved text must include line 1095's content, not silently omit it
    the way every pre-v2.6.5 implementation did."""
    full_text = "\n".join(f"line{n}" for n in range(1, 1200))
    result = parse_source_lines("1049-1053,1095")
    span = resolve_span_text(full_text, result.segments)
    assert "line1095" in span
    assert "line1049" in span
    assert "line1053" in span


def test_resolve_span_text_seeded_dose_fact_survives():
    """Direct regression test for the seeded false-negative proof
    (_v2_6_5_evidence/RED_seeded_false_negative_proof.txt): a critical dose
    fact living only on the trailing single-line segment of a mixed
    source_lines declaration must appear in the resolved span."""
    lines = [f"filler {n}" for n in range(1, 60)]
    lines[49] = "Do not exceed 4g of paracetamol in any 24-hour period."
    full_text = "\n".join(lines)
    result = parse_source_lines("10-12,50")
    span = resolve_span_text(full_text, result.segments)
    assert "4g of paracetamol" in span
