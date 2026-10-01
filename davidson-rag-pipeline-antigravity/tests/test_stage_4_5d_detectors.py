"""Stage 4.5d — one fixture pair per sub-check (constraint 9), each
engineered to contain exactly one corruption of that type, plus a clean
(true-negative) pair, and a legitimate-paraphrase pair where applicable to
confirm the detector routes it to CANDIDATE_MISMATCH for human review
rather than auto-passing or auto-failing it (constraint 4).
"""
from pipeline.stages import stage_4_5d_clinical_fidelity as s45d


# --- 1. Numeric -----------------------------------------------------------

def test_numeric_clean():
    src, chunk = "The dose is 250 mg twice daily.", "The dose is 250 mg twice daily."
    cands, scanned = s45d.detect_numeric(src, chunk, "L2-01")
    assert cands == []
    assert scanned > 0


def test_numeric_digit_dropped():
    src, chunk = "The dose is 250 mg twice daily.", "The dose is 25 mg twice daily."
    cands, _ = s45d.detect_numeric(src, chunk, "L2-01")
    assert any(c["source_value"] == "250" for c in cands)
    assert all(c["severity"] == "CANDIDATE_MISMATCH" for c in cands)


# --- 2. Unit ----------------------------------------------------------

def test_unit_swapped_dose_error():
    src = "Give 250 mg of amoxicillin."
    chunk = "Give 250 mcg of amoxicillin."
    cands, _ = s45d.detect_unit(src, chunk, "L2-01")
    assert any(c["kind"] == "missing" and "mg" in c["source_value"] for c in cands)
    assert any(c["kind"] == "added" and "mcg" in c["chunk_value"] for c in cands)


# --- 3. Inequality ------------------------------------------------------

def test_inequality_direction_reversed():
    src = "Reduce dose if eGFR < 30."
    chunk = "Reduce dose if eGFR > 30."
    cands, _ = s45d.detect_inequality(src, chunk, "L2-01")
    assert any(c["source_value"] == "<" for c in cands)
    assert any(c["chunk_value"] == ">" for c in cands)


def test_inequality_clean():
    src = chunk = "Reduce dose if eGFR < 30."
    cands, _ = s45d.detect_inequality(src, chunk, "L2-01")
    assert cands == []


# --- 4. Range -----------------------------------------------------------

def test_range_widened():
    src, chunk = "Treat for 5-10 days.", "Treat for 5-100 days."
    cands, _ = s45d.detect_range(src, chunk, "L2-01")
    assert any(c["source_value"] == "5-10" for c in cands)


# --- 5. Dose --------------------------------------------------------------

def test_dose_missing_in_chunk():
    src = "Loading dose 250 mg then maintenance dose 50 mg."
    chunk = "Loading dose then maintenance dose."
    cands, _ = s45d.detect_dose(src, chunk, "L2-01")
    assert any("250 mg" in (c["source_value"] or "") for c in cands)


# --- 6. Duration --------------------------------------------------------

def test_duration_changed():
    src, chunk = "Continue for 7 days.", "Continue for 7 weeks."
    cands, _ = s45d.detect_duration(src, chunk, "L2-01")
    assert any(c["source_value"] == "7 days" for c in cands)
    assert any(c["chunk_value"] == "7 weeks" for c in cands)


# --- 7. Frequency ---------------------------------------------------------

def test_frequency_changed():
    src, chunk = "Take twice daily.", "Take once daily."
    cands, _ = s45d.detect_frequency(src, chunk, "L2-01")
    assert any(c["source_value"] == "twice daily" for c in cands)


def test_frequency_legitimate_paraphrase_still_flagged_for_review():
    """'twice daily' -> 'every 12 hours' is plausible legitimate paraphrase,
    not necessarily a corruption -- constraint 4 requires this be routed to
    human review, never silently auto-cleared as equivalent."""
    src, chunk = "Take twice daily.", "Take every 12 hours."
    cands, _ = s45d.detect_frequency(src, chunk, "L2-01")
    assert len(cands) > 0
    assert all(c["severity"] == "CANDIDATE_MISMATCH" for c in cands)


# --- 8. Negation ----------------------------------------------------------

def test_negation_flip_is_flagged_clinically_consequential():
    src = "This drug is not indicated in pregnancy."
    chunk = "This drug is indicated in pregnancy."
    cands, _ = s45d.detect_negation(src, chunk, "L2-01")
    assert any(c["kind"] == "flipped" and c.get("clinically_consequential") for c in cands)


def test_negation_clean():
    src = chunk = "This drug is not indicated in pregnancy."
    cands, _ = s45d.detect_negation(src, chunk, "L2-01")
    assert cands == []


# --- 9. Polarity ------------------------------------------------------

def test_polarity_flip_is_flagged():
    src = "Smoking increases the risk of exacerbation."
    chunk = "Smoking decreases the risk of exacerbation."
    cands, _ = s45d.detect_polarity(src, chunk, "L2-01")
    assert any(c["kind"] == "flipped" for c in cands)


# --- 10. Sequence -------------------------------------------------------

def test_sequence_reorder_is_flagged_clinically_consequential():
    src = "First-line treatment is X. Then, second-line treatment is Y."
    chunk = "Second-line treatment is Y. Then, first-line treatment is X."
    cands, _ = s45d.detect_sequence(src, chunk, "L2-01")
    assert any(c["kind"] == "reordered" and c.get("clinically_consequential") for c in cands)


def test_sequence_clean_never_claims_semantic_verification():
    """Even a 0-candidate result on this check must not be described as
    proof the clinical order is correct (constraint 4 / correction D) --
    that claim lives at the gate level's truth_status, not this function."""
    src = chunk = "First-line treatment is X. Then, second-line treatment is Y."
    cands, _ = s45d.detect_sequence(src, chunk, "L2-01")
    assert cands == []  # this function itself makes no "verified correct" claim


# --- 11. Boundary-loss (classification rules, correction F) -------------

def test_boundary_classify_same_chunk_is_not_a_split():
    assert s45d.classify_boundary(same_chunk=True, same_disease_focus=True,
                                   adjacent_chunk_ids=True, split_at_declared_heading=False) is None


def test_boundary_classify_critical_separation_different_disease():
    result = s45d.classify_boundary(same_chunk=False, same_disease_focus=False,
                                     adjacent_chunk_ids=True, split_at_declared_heading=False)
    assert result == "CRITICAL_SEPARATION"


def test_boundary_classify_safe_linked_split_same_disease_adjacent():
    result = s45d.classify_boundary(same_chunk=False, same_disease_focus=True,
                                     adjacent_chunk_ids=True, split_at_declared_heading=False)
    assert result == "SAFE_LINKED_SPLIT"


def test_boundary_classify_intentional_section_split():
    result = s45d.classify_boundary(same_chunk=False, same_disease_focus=True,
                                     adjacent_chunk_ids=False, split_at_declared_heading=True)
    assert result == "INTENTIONAL_SECTION_SPLIT"


def test_boundary_classify_ambiguous_fallback():
    result = s45d.classify_boundary(same_chunk=False, same_disease_focus=True,
                                     adjacent_chunk_ids=False, split_at_declared_heading=False)
    assert result == "AMBIGUOUS"


def test_boundary_loss_only_critical_separation_is_hard_failure():
    l1_body = "Warfarin 5 mg once daily is the standard dose for this indication."
    l2_chunks = [
        {"chunk_id": "L2-01", "body": "Warfarin is a vitamin K antagonist.",
         "disease_focus": "atrial_fibrillation", "order": 1},
        {"chunk_id": "L2-02", "body": "The dose is 5 mg once daily for a different, unrelated condition.",
         "disease_focus": "deep_vein_thrombosis", "order": 2},
    ]
    cands, scanned = s45d.detect_boundary_loss(l1_body, l2_chunks)
    assert scanned >= 1
    critical = [c for c in cands if c.get("boundary_classification") == "CRITICAL_SEPARATION"]
    assert critical, "different disease_focus across the split must classify as CRITICAL_SEPARATION"
    assert all(c.get("clinically_consequential") for c in critical)


def test_boundary_loss_safe_linked_split_not_flagged_clinically_consequential():
    l1_body = "Warfarin 5 mg once daily is the standard dose."
    l2_chunks = [
        {"chunk_id": "L2-01", "body": "Warfarin is prescribed for this disease.",
         "disease_focus": "atrial_fibrillation", "order": 1},
        {"chunk_id": "L2-02", "body": "The dose is 5 mg once daily.",
         "disease_focus": "atrial_fibrillation", "order": 2},
    ]
    cands, _ = s45d.detect_boundary_loss(l1_body, l2_chunks)
    safe = [c for c in cands if c.get("boundary_classification") == "SAFE_LINKED_SPLIT"]
    assert safe
    assert not any(c.get("clinically_consequential") for c in safe)


def test_boundary_loss_ambiguous_via_real_detector():
    """AMBIGUOUS: same disease_focus but NOT adjacent, no heading evidence
    -- confirms the real detector (not just classify_boundary() directly)
    can produce this classification too."""
    l1_body = "Warfarin 5 mg once daily is the standard dose."
    l2_chunks = [
        {"chunk_id": "L2-01", "body": "Warfarin is prescribed for this disease.",
         "disease_focus": "atrial_fibrillation", "order": 1},
        {"chunk_id": "L2-02", "body": "The dose is 5 mg once daily.",
         "disease_focus": "atrial_fibrillation", "order": 9},  # not adjacent
    ]
    cands, _ = s45d.detect_boundary_loss(l1_body, l2_chunks)
    ambiguous = [c for c in cands if c.get("boundary_classification") == "AMBIGUOUS"]
    assert ambiguous
    assert not any(c.get("clinically_consequential") for c in ambiguous)


# --- v2.6.2: INTENTIONAL_SECTION_SPLIT reachability (audit finding fix) --

def test_boundary_loss_produces_intentional_section_split_via_real_heading_evidence():
    """The audit found INTENTIONAL_SECTION_SPLIT was implemented and
    unit-tested in classify_boundary() but never actually reachable from
    detect_boundary_loss(), which always passed
    split_at_declared_heading=False. Fixed (v2.6.2): when repaired_s2_text
    and each chunk's source_lines are provided, a real Markdown heading
    line found in the gap between the two chunks' spans is genuine
    structural evidence of an intentional split -- not an inference from
    mere adjacency. This test constructs that exact real-source-text
    scenario and confirms the real detector now produces the
    classification, not just the pure classify_boundary() function."""
    repaired_s2_text = (
        "Warfarin therapy overview\n"
        "\n"
        "## New Subsection\n"
        "\n"
        "Dose is 5 mg once daily\n"
    )
    l1_body = "Warfarin 5 mg once daily is the standard dose for this indication."
    l2_chunks = [
        {"chunk_id": "L2-01", "body": "Warfarin is a vitamin K antagonist.",
         "disease_focus": "x", "order": 1, "source_lines": (1, 1)},
        {"chunk_id": "L2-02", "body": "The dose is 5 mg once daily for something else.",
         "disease_focus": "x", "order": 5, "source_lines": (5, 5)},
    ]
    cands, scanned = s45d.detect_boundary_loss(l1_body, l2_chunks, repaired_s2_text=repaired_s2_text)
    assert scanned >= 1
    intentional = [c for c in cands if c.get("boundary_classification") == "INTENTIONAL_SECTION_SPLIT"]
    assert intentional, f"expected INTENTIONAL_SECTION_SPLIT, got: {[c.get('boundary_classification') for c in cands]}"
    assert not any(c.get("clinically_consequential") for c in intentional)


def test_boundary_loss_no_heading_in_gap_does_not_produce_intentional_split():
    """Same chunk positions, but NO heading in the gap -- must NOT be
    classified INTENTIONAL_SECTION_SPLIT just because source_lines/
    repaired_s2_text were supplied; the heading must genuinely be there."""
    repaired_s2_text = (
        "Warfarin therapy overview\n"
        "\n"
        "still just prose, no heading here\n"
        "\n"
        "Dose is 5 mg once daily\n"
    )
    l1_body = "Warfarin 5 mg once daily is the standard dose for this indication."
    l2_chunks = [
        {"chunk_id": "L2-01", "body": "Warfarin is a vitamin K antagonist.",
         "disease_focus": "different_disease", "order": 1, "source_lines": (1, 1)},
        {"chunk_id": "L2-02", "body": "The dose is 5 mg once daily for something else.",
         "disease_focus": "other_disease", "order": 5, "source_lines": (5, 5)},
    ]
    cands, _ = s45d.detect_boundary_loss(l1_body, l2_chunks, repaired_s2_text=repaired_s2_text)
    assert not any(c.get("boundary_classification") == "INTENTIONAL_SECTION_SPLIT" for c in cands)
    # different disease_focus, no heading evidence -> falls through to CRITICAL_SEPARATION
    assert any(c.get("boundary_classification") == "CRITICAL_SEPARATION" for c in cands)


def test_boundary_loss_produces_critical_separation_via_real_detector_with_source_text():
    """CRITICAL_SEPARATION reachable even when repaired_s2_text IS supplied
    (not just in the no-source-text default path already covered above) --
    confirms heading-evidence and disease-focus-based classification
    coexist correctly, heading check doesn't accidentally suppress this."""
    repaired_s2_text = "Warfarin overview\n\nDose is 5 mg once daily\n"
    l1_body = "Warfarin 5 mg once daily is the standard dose."
    l2_chunks = [
        {"chunk_id": "L2-01", "body": "Warfarin is a vitamin K antagonist.",
         "disease_focus": "atrial_fibrillation", "order": 1, "source_lines": (1, 1)},
        {"chunk_id": "L2-02", "body": "The dose is 5 mg once daily.",
         "disease_focus": "deep_vein_thrombosis", "order": 2, "source_lines": (3, 3)},
    ]
    cands, _ = s45d.detect_boundary_loss(l1_body, l2_chunks, repaired_s2_text=repaired_s2_text)
    assert any(c.get("boundary_classification") == "CRITICAL_SEPARATION" for c in cands)


def test_heading_exists_between_true_when_heading_in_gap():
    text = "line1\n## Heading\nline3\n"
    assert s45d._heading_exists_between(text, 1, 3) is True


def test_heading_exists_between_false_when_no_gap():
    text = "line1\nline2\n"
    assert s45d._heading_exists_between(text, 1, 2) is False  # adjacent, no gap


def test_heading_exists_between_false_when_gap_has_no_heading():
    text = "line1\njust prose\nline3\n"
    assert s45d._heading_exists_between(text, 1, 3) is False


def test_heading_exists_between_none_inputs_return_false():
    assert s45d._heading_exists_between(None, 1, 3) is False
    assert s45d._heading_exists_between("text", None, 3) is False


# --- correction E: source_lines mapping used first, 5-word fallback only --

def test_resolve_source_span_prefers_source_lines():
    repaired = "line one\nline two\nDRUG DOSE HERE\nline four\nline five\n"
    block = '---\nchunk_id: L2-01\nsource_lines: "3-3"\n---\n\nsome chunk body here'
    span, method = s45d.resolve_source_span(repaired, block)
    assert method == "source_lines"
    assert span.strip() == "DRUG DOSE HERE"


def test_resolve_source_span_falls_back_to_context_when_source_lines_missing():
    repaired = "irrelevant\n"
    block = '---\nchunk_id: L2-01\n---\n\none two three four five six seven'
    span, method = s45d.resolve_source_span(repaired, block)
    assert method == "context_fallback"
    assert span == "one two three four five"


def test_resolve_source_span_handles_discontinuous_multi_segment_ranges():
    """Found while adjudicating Chapter 05's real Stage 4.5d candidates:
    source_lines can be "787-789, 815-816" (a chunk spliced around an
    interruption in the source, e.g. a box/page-break). The original
    implementation matched only the first "start-end" pair via re.search
    and silently dropped every later segment, producing spurious "added"
    candidates for content that was genuinely present in the source."""
    repaired = "\n".join([f"line{i}" for i in range(1, 20)]) + "\n"
    # 1-indexed: lines 3-4 are "line3\nline4", lines 8-9 are "line8\nline9"
    block = '---\nchunk_id: L2-01\nsource_lines: "3-4, 8-9"\n---\n\nbody'
    span, method = s45d.resolve_source_span(repaired, block)
    assert method == "source_lines"
    assert "line3" in span and "line4" in span
    assert "line8" in span and "line9" in span
    # segments must not be dropped -- both ranges' content present
    assert span.count("line") == 4
