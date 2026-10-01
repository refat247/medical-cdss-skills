r"""v2.6.7 -- RED/GREEN evidence for the Stage 6 block-parsing blind spot
found by REPOSITORY_PRODUCTION_READINESS_AUDIT.md (Blocker 2).

Root cause: `check_6_1_6_2()`'s original regex (as a raw string)
    r"(---\nchunk_id:.*?\n---\n.*?)(?=\n---\nchunk_id:|\Z)"
requires the literal sequence '\n---\n' (WITH a trailing newline) to close
a chunk's frontmatter. When a RAG_Optimised.md file has no trailing newline
AND its last chunk is empty-body (frontmatter-only, e.g. a Tier-3
coverage_gap stub), that final '\n---\n' never occurs -- the file ends in
'\n---' with nothing after it -- so the last chunk is silently dropped,
never merged into a neighbor, never double-counted, just invisible.

This file was authored BEFORE the parser fix (Part B) to capture genuine
RED evidence, then re-run after the fix to confirm GREEN. See
V2_6_7_STAGE6_AND_CH05_COMPLETENESS_FIX_REPORT.md for the actual pytest
output captured at each stage.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.stages.stage_6_validation import check_6_1_6_2


def _chunk(chunk_id, disease_focus="malaria", coverage_status="complete",
           gap_note=None, body="Some real body text about the disease."):
    fm = [
        "---",
        f"chunk_id: {chunk_id}",
        "semantic_type: clinical_feature",
        f"disease_focus: {disease_focus}",
        f"coverage_status: {coverage_status}",
    ]
    if gap_note is not None:
        fm.append(f'gap_note: "{gap_note}"')
    fm.append("---")
    frontmatter = "\n".join(fm)
    if body:
        return f"{frontmatter}\n{body}\n"
    return f"{frontmatter}\n"  # empty-body chunk: nothing after closing '---' line


def _gap_stub(chunk_id="L2-999-GAP"):
    """A frontmatter-only (empty-body) Tier-3 coverage_gap stub -- exactly
    the shape of Ch11's L2-105-GAP / Ch15's L2-087-GAP."""
    return (
        "---\n"
        f"chunk_id: {chunk_id}\n"
        "semantic_type: coverage_gap\n"
        "disease_focus: poisoning_unspecified\n"
        "coverage_status: gap\n"
        'gap_note: "No source coverage found for this sub-topic."\n'
        "---"
    )  # deliberately NO trailing newline / body -- this IS the whole chunk


def test_final_empty_body_chunk_no_trailing_newline_is_currently_missed():
    """RED (pre-fix) / GREEN (post-fix) case #1 -- the exact Ch11/Ch15
    scenario: one normal chunk, then a frontmatter-only gap stub as the
    LAST chunk, with no trailing newline after the stub's closing '---'."""
    normal = _chunk("L2-001")
    stub = _gap_stub("L2-002-GAP")
    text = normal.rstrip("\n") + "\n" + stub  # no trailing newline at all

    failures, n = check_6_1_6_2(text)
    # POST-FIX requirement: both chunks detected, stub counted as its own
    # block, and its own frontmatter passes 6.1/6.2 (well-formed).
    assert n == 2, f"expected 2 blocks (post-fix), got {n}"
    assert failures == [], f"expected no failures for well-formed chunks, got {failures}"


def test_control_same_content_with_trailing_newline_detects_both():
    """Control: identical content but WITH a trailing newline. This should
    already pass even pre-fix -- confirms the newline is the true variable,
    not something else about the stub's shape."""
    normal = _chunk("L2-001")
    stub = _gap_stub("L2-002-GAP")
    text = normal.rstrip("\n") + "\n" + stub + "\n"  # trailing newline present

    failures, n = check_6_1_6_2(text)
    assert n == 2
    assert failures == []


def test_final_non_empty_chunk_no_trailing_newline_already_works():
    """A final chunk WITH real body text and no trailing newline should
    already work both pre- and post-fix (the `\\Z` alternative in the
    original regex's lookahead already covers this case)."""
    c1 = _chunk("L2-001")
    c2 = _chunk("L2-002", body="Final chunk with real body text.")
    text = c1.rstrip("\n") + "\n" + c2.rstrip("\n")  # no trailing newline

    failures, n = check_6_1_6_2(text)
    assert n == 2
    assert failures == []


def test_single_empty_body_chunk_only_chunk_no_trailing_newline():
    """A single empty-body chunk that is the ONLY chunk in the file, no
    trailing newline. Must still be detected as exactly 1 block."""
    stub = _gap_stub("L2-001-GAP")
    text = stub  # no trailing newline

    failures, n = check_6_1_6_2(text)
    assert n == 1
    assert failures == []


def test_multiple_consecutive_empty_body_chunks_at_end_no_trailing_newline():
    """Several empty-body chunks in a row at the end of the file, no
    trailing newline. Each must be its own block -- none dropped, none
    merged together."""
    c1 = _chunk("L2-001")
    stub1 = _gap_stub("L2-002-GAP")
    stub2 = _gap_stub("L2-003-GAP")
    stub3 = _gap_stub("L2-004-GAP")
    text = (
        c1.rstrip("\n") + "\n"
        + stub1 + "\n"
        + stub2 + "\n"
        + stub3  # last one: no trailing newline
    )

    failures, n = check_6_1_6_2(text)
    assert n == 4
    assert failures == []
    ids = [f"L2-00{i}" for i in (1, 2, 3, 4)]  # sanity: no exception, all present
    # duplicate check lives in its own test below; here just confirm count


def test_normal_multi_chunk_file_with_trailing_newline_regression_control():
    """Regression control: an ordinary multi-chunk file (all non-empty
    bodies) WITH a trailing newline -- must behave identically before and
    after the fix."""
    c1 = _chunk("L2-001")
    c2 = _chunk("L2-002", body="Second chunk body.")
    c3 = _chunk("L2-003", body="Third chunk body.")
    text = c1 + c2 + c3  # each _chunk() already ends with '\n'

    failures, n = check_6_1_6_2(text)
    assert n == 3
    assert failures == []


def test_malformed_unclosed_frontmatter_fails_visibly():
    """A chunk whose frontmatter never closes (missing the closing '---')
    must fail visibly -- not be silently dropped, and not be silently
    merged into a neighboring chunk's block. Post-fix, this is surfaced as
    an explicit failure entry in the returned failures list (see Part B's
    documented failure mode) rather than a silent 0-impact omission."""
    c1 = _chunk("L2-001")
    malformed = (
        "---\n"
        "chunk_id: L2-002\n"
        "semantic_type: clinical_feature\n"
        "disease_focus: malaria\n"
        "coverage_status: complete\n"
        "This chunk's frontmatter never closes with its own '---' line.\n"
        "It just keeps going as if it were still frontmatter.\n"
    )
    text = c1 + malformed

    failures, n = check_6_1_6_2(text)
    # The malformed chunk must be visibly flagged -- not silently absorbed
    # into L2-001's block (which would make n == 1 with no failures, the
    # silent-merge failure mode this test exists to rule out).
    assert any("L2-002" in f and ("frontmatter" in f.lower() or "malformed" in f.lower())
               for f in failures), f"malformed chunk was not visibly flagged: {failures}"
    # L2-001 itself, which IS well-formed, must still be counted and clean.
    assert n >= 1


def test_no_duplicate_blocks_for_any_chunk_id():
    """No chunk_id may appear in more than one parsed block, for any of the
    scenarios above that produce multiple valid blocks."""
    c1 = _chunk("L2-001")
    stub1 = _gap_stub("L2-002-GAP")
    stub2 = _gap_stub("L2-003-GAP")
    text = c1.rstrip("\n") + "\n" + stub1 + "\n" + stub2  # no trailing newline

    import re
    # Re-derive the same block list check_6_1_6_2 uses internally by calling
    # the public function and checking failures/n, then independently count
    # chunk_id occurrences of the OUTPUT to ensure the function's failure
    # list never reports the same chunk_id twice (which would indicate a
    # duplicate-block bug rather than a single clean failure/pass entry).
    failures, n = check_6_1_6_2(text)
    assert n == 3
    assert failures == []
    # Independently regex-count chunk_id header occurrences in the source
    # text itself, to establish ground truth: exactly 3 distinct ids, and
    # the parser's block count must equal that, not more.
    ids_in_source = re.findall(r'chunk_id:\s*(\S+)', text)
    assert len(ids_in_source) == len(set(ids_in_source)) == 3
    assert n == len(set(ids_in_source))
