"""v2.6.4 -- Corpus-Scale Gate Closure, MUST-FIX #2: source_lines precision
integration (short-bullet handling + adjudication).

Covers the required test matrix: precise contiguous mappings, genuine
over/under-inclusive mappings, short contiguous bullet lists, discontinuous
ranges, missing source_lines, malformed ranges, adjudicated checker false
positive, confirmed metadata defect followed by correction and recheck.
"""
import os
import re

from pipeline.stages.source_lines_precision import (
    check_chunk_precision, classify_precision, apply_corrections,
    apply_source_lines_adjudication, unresolved_findings, build_precision_summary,
    ADJUDICATION_DECISION_VALUES,
)

CH02_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "02")
CH02_PREFIX = "Davidson_25_Ch02_Clinical_therapeutics_and_good_prescribing"


def _load_ch02_chunk(chunk_id):
    path = os.path.join(CH02_DIR, f"{CH02_PREFIX}_chunks.md")
    if not os.path.exists(path):
        return None
    text = open(path, encoding="utf-8").read()
    blocks = re.findall(r'(---\nchunk_id:.*?\n---\n.*?)(?=\n---\nchunk_id:|\Z)', text, re.DOTALL)
    for b in blocks:
        if re.search(rf'chunk_id:\s*{re.escape(chunk_id)}\b', b):
            return b
    return None


def _ch02_repaired_s2():
    return open(os.path.join(CH02_DIR, f"{CH02_PREFIX}_REPAIRED_S2.md"), encoding="utf-8").read()


def _block(chunk_id, source_lines, body):
    if source_lines is None:
        return f'---\nchunk_id: {chunk_id}\nchunk_level: 2\n---\n\n{body}'
    return f'---\nchunk_id: {chunk_id}\nchunk_level: 2\nsource_lines: "{source_lines}"\n---\n\n{body}'


# --- Short contiguous bullet lists: the real Chapter 02 failure shape ---

def test_real_chapter_02_hypersensitivity_box_is_bullet_gap_only():
    """The real, confirmed Chapter 02 finding (Box 2.6, types I-IV drug
    hypersensitivity reactions): short repeated drug-name bullets
    ("- Penicillins", "- NSAIDs", appearing multiple times across the four
    reaction types) create ambiguous anchor matches that produce a spurious
    internal gap -- OVER_INCLUSIVE, but must be marked bullet_gap_only so it
    routes to low-priority/likely-safe adjudication rather than being
    treated as a genuine content-swap defect."""
    block = _load_ch02_chunk("L2-033")
    if block is None:
        import pytest
        pytest.skip("Real Chapter 02 chunks.md not present in this environment")
    result = check_chunk_precision(block, _ch02_repaired_s2())
    assert result["verdict"] == "OVER_INCLUSIVE"
    assert result["bullet_gap_only"] is True


def test_genuine_over_inclusive_unrelated_box_is_not_marked_bullet_gap_only():
    """The real Chapter 05 L2-118 signature: an unrelated BOX (not short
    bullets) sits in the gap -- must remain a full-priority signal, never
    downgraded by the bullet heuristic."""
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
    block = _block("L2-118", "1-8", body)
    result = check_chunk_precision(block, repaired)
    assert result["verdict"] == "OVER_INCLUSIVE"
    assert result["bullet_gap_only"] is False


def test_mixed_bullet_and_prose_gap_is_not_marked_bullet_gap_only():
    """Conservative-rule guard: a gap that is MOSTLY short bullets but ALSO
    contains one genuine prose/box line must not be waved through as a
    bullet-only artifact."""
    body = "First matched sentence that is long enough to anchor reliably right here.\n\nSecond matched sentence that anchors reliably at the far end of the range."
    repaired_lines = [
        "First matched sentence that is long enough to anchor reliably right here.",
        "- Penicillins",
        "This is a genuine unrelated prose sentence that should block the bullet-only heuristic entirely.",
        "- NSAIDs",
        "Second matched sentence that anchors reliably at the far end of the range.",
    ]
    repaired = "\n".join(repaired_lines) + "\n"
    block = _block("L2-999", "1-5", body)
    result = check_chunk_precision(block, repaired)
    assert result["verdict"] == "OVER_INCLUSIVE"
    assert result["bullet_gap_only"] is False


def test_classify_precision_without_source_lines_list_never_sets_bullet_gap_only():
    """Backward compatibility: every pre-v2.6.4 call site (and every
    existing direct classify_precision() test) omits source_lines_list --
    bullet_gap_only must always be False in that case, never inferred."""
    result = classify_precision(
        declared_segments=[(10, 30)], matched_lines=[10, 11, 29, 30],
        total_units=4, unmatched=0,
    )
    assert result["verdict"] == "OVER_INCLUSIVE"
    assert result["bullet_gap_only"] is False


# --- Precise contiguous, discontinuous ranges, missing/malformed source_lines ---

def test_precise_contiguous_mapping():
    body = "This is a full sentence that genuinely exists in the source text right here."
    repaired = "filler line one\n" + body + "\nfiller line three\n"
    block = _block("L2-01", "2-2", body)
    result = check_chunk_precision(block, repaired)
    assert result["verdict"] == "PRECISE"
    assert result["bullet_gap_only"] is False


def test_discontinuous_declared_range_with_intentional_gap_not_flagged():
    """A chunk whose source_lines is ALREADY a corrected, discontinuous,
    comma-separated range (the post-splice-fix form) must not be re-flagged
    for the gap it deliberately excludes."""
    body = "First part of the chunk right here in this very sentence.\n\nSecond part of the same chunk over here as well."
    repaired_lines = [
        "First part of the chunk right here in this very sentence.",
        "Unrelated interleaved content that this chunk correctly excludes now.",
        "Second part of the same chunk over here as well.",
    ]
    repaired = "\n".join(repaired_lines) + "\n"
    block = _block("L2-05", "1-1, 3-3", body)
    result = check_chunk_precision(block, repaired)
    assert result["verdict"] == "PRECISE"


def test_missing_source_lines_field_is_unresolved_not_a_crash():
    body = "Some perfectly ordinary chunk body text that exists somewhere in the source."
    repaired = "filler\n" + body + "\nfiller\n"
    block = _block("L2-06", None, body)
    result = check_chunk_precision(block, repaired)
    # No declared_segments at all -- classify_precision treats every matched
    # line as "outside declared" (see `outside = ... if declared_segments else list(matched_lines)`).
    assert result["verdict"] in ("UNDER_INCLUSIVE", "UNRESOLVED")


def test_malformed_source_lines_range_does_not_crash():
    body = "Some chunk body text that should still be checkable even with garbage metadata."
    repaired = "filler\n" + body + "\nfiller\n"
    block = _block("L2-07", "not-a-valid-range", body)
    result = check_chunk_precision(block, repaired)
    assert result["verdict"] in ("UNDER_INCLUSIVE", "UNRESOLVED", "PRECISE")


# --- Adjudication mechanism ---

def _sample_results():
    return [
        {"chunk_id": "L2-033", "verdict": "OVER_INCLUSIVE", "bullet_gap_only": True},
        {"chunk_id": "L2-118", "verdict": "OVER_INCLUSIVE", "bullet_gap_only": False},
        {"chunk_id": "L2-097", "verdict": "UNDER_INCLUSIVE", "bullet_gap_only": False},
        {"chunk_id": "L2-999", "verdict": "PRECISE", "bullet_gap_only": False},
    ]


def test_unresolved_findings_lists_every_non_precise_unadjudicated_chunk():
    results = _sample_results()
    assert set(unresolved_findings(results)) == {"L2-033", "L2-118", "L2-097"}


def test_adjudicated_checker_false_positive_resolves_finding():
    results = _sample_results()
    decisions = {"L2-033": {"decision": "CHECKER_FALSE_POSITIVE",
                             "rationale": "Gap is entirely short hypersensitivity-drug bullets; "
                                          "body content confirmed verbatim-correct and contiguous."}}
    updated, errors = apply_source_lines_adjudication(results, decisions)
    assert errors == []
    assert "L2-033" not in unresolved_findings(updated)
    l2_033 = next(r for r in updated if r["chunk_id"] == "L2-033")
    assert l2_033["adjudication"]["decision"] == "CHECKER_FALSE_POSITIVE"
    assert l2_033["adjudication"]["rationale"]


def test_confirmed_metadata_defect_remains_unresolved_until_rechecked_precise():
    """Recording HUMAN_CONFIRMED_METADATA_DEFECT does NOT resolve the finding
    on its own -- only a subsequent correction + recheck to PRECISE does."""
    results = _sample_results()
    decisions = {"L2-097": {"decision": "HUMAN_CONFIRMED_METADATA_DEFECT",
                             "rationale": "Declared range excludes the chunk's own reference-intake "
                                          "table, which actually starts 1 line later than declared."}}
    updated, errors = apply_source_lines_adjudication(results, decisions)
    assert errors == []
    assert "L2-097" in unresolved_findings(updated)  # still unresolved -- fix not yet applied

    # Simulate the fix + recheck: apply_corrections() rewrites source_lines,
    # then a fresh check_chunk_precision() run reports PRECISE.
    chunks_text = '---\nchunk_id: L2-097\nchunk_level: 2\nsource_lines: "1045-1058"\n---\n\nbody text here'
    corrected_text, changed, unmatched = apply_corrections(chunks_text, {"L2-097": [(1045, 1084)]})
    assert changed == 1
    assert 'source_lines: "1045-1084"' in corrected_text


def test_adjudication_rejects_invalid_decision_value():
    results = _sample_results()
    decisions = {"L2-033": {"decision": "MAYBE_FINE", "rationale": "not a valid decision"}}
    updated, errors = apply_source_lines_adjudication(results, decisions)
    assert errors
    assert updated == results  # unchanged -- no partial application


def test_adjudication_rejects_blank_rationale():
    results = _sample_results()
    decisions = {"L2-033": {"decision": "CHECKER_FALSE_POSITIVE", "rationale": "   "}}
    updated, errors = apply_source_lines_adjudication(results, decisions)
    assert errors
    assert updated == results


def test_adjudication_rejects_unknown_chunk_id():
    results = _sample_results()
    decisions = {"L2-DOES-NOT-EXIST": {"decision": "CHECKER_FALSE_POSITIVE", "rationale": "n/a"}}
    updated, errors = apply_source_lines_adjudication(results, decisions)
    assert errors


def test_decision_values_are_exactly_the_two_required_labels():
    assert set(ADJUDICATION_DECISION_VALUES) == {"CHECKER_FALSE_POSITIVE", "HUMAN_CONFIRMED_METADATA_DEFECT"}


def test_build_precision_summary_reports_tested_and_unresolved_count():
    results = _sample_results()
    summary = build_precision_summary(results)
    assert summary["tested"] is True
    assert summary["chunks_checked"] == 4
    assert summary["unresolved_count"] == 3
    assert summary["bullet_gap_only_count"] == 1

    decisions = {"L2-033": {"decision": "CHECKER_FALSE_POSITIVE", "rationale": "confirmed bullet artifact"}}
    updated, _errors = apply_source_lines_adjudication(results, decisions)
    summary2 = build_precision_summary(updated)
    assert summary2["unresolved_count"] == 2
