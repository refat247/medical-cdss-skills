"""v2.6.2 — deterministic-portion tests for stage_4_6_sonnet_verification.py
(audit finding: this module had zero dedicated tests despite being used by
every chapter's Stage 4.6). Covers only what's actually deterministic:
title/body rule classification, unparsed-chunk accounting, metadata
construction, manual-review export/apply, and control-flow around the
Anthropic API path (mocked — never calls the live API). These tests prove
control flow and error handling, NOT semantic classification accuracy —
that would require real chapter data and a human reviewer, same limitation
already documented for Stage 4.5d.
"""
import sys
from unittest.mock import MagicMock, patch

from pipeline import stage_4_6_sonnet_verification as s46


def _chunk(cid, semantic_type, topic, body, level=2):
    return (
        f"---\nchunk_id: {cid}\nchunk_level: {level}\nsemantic_type: {semantic_type}\n"
        f"topic: {topic}\n---\n\n{body}\n"
    )


# --- Title-rule classification (auto-applied) ----------------------------

def test_title_rule_adverse_effects_reclassifies_to_drug_info():
    chunks = _chunk("L2-01", "management_step", "Adverse effects of bisphosphonates",
                     "Nausea and jaw osteonecrosis can occur.")
    new_text, changed, review_priority = s46._regex_remap_all(chunks, levels=(2,))
    assert changed == 1
    assert "semantic_type: drug_info" in new_text


def test_title_rule_investigations_reclassifies_to_laboratory_investigation():
    chunks = _chunk("L2-02", "clinical_feature", "Investigations",
                     "Blood tests are performed to confirm the diagnosis.")
    new_text, changed, _ = s46._regex_remap_all(chunks, levels=(2,))
    assert changed == 1
    assert "semantic_type: laboratory_investigation" in new_text


def test_title_rule_does_not_fire_when_already_correct():
    chunks = _chunk("L2-03", "drug_info", "Adverse effects of steroids", "Weight gain occurs.")
    new_text, changed, _ = s46._regex_remap_all(chunks, levels=(2,))
    assert changed == 0


# --- Body-rule classification (advisory only, never auto-applied) --------

def test_body_rules_never_auto_apply_only_flag_review_priority():
    """Audit-relevant control-flow guarantee: BODY_RULES matching must
    show up in review_priority but must NOT change semantic_type in the
    output text -- this is the core v2.1.0 design decision this module's
    own docstring documents (auto-applying BODY_RULES caused more
    regressions than it fixed)."""
    chunks = _chunk("L2-04", "clinical_feature", "Generic heading",
                     "The dosing regimen has a long half-life and antibiotic properties.")
    new_text, changed, review_priority = s46._regex_remap_all(chunks, levels=(2,))
    assert changed == 0  # not auto-applied
    assert "semantic_type: clinical_feature" in new_text  # unchanged
    assert any(p["chunk_id"] == "L2-04" and p["candidate_type"] == "drug_info"
               for p in review_priority)


def test_classify_by_rules_title_wins_over_body():
    result = s46._classify_by_rules("Adverse effects of X", "some symptom text")
    assert result == "drug_info"


def test_classify_by_rules_falls_back_to_body_when_no_title_match():
    result = s46._classify_by_rules("Generic heading", "the dosing regimen has a half-life")
    assert result == "drug_info"


def test_classify_by_rules_pure_epidemiology_detector():
    body = "Incidence is 2-10 per 100 000. Prevalence is around 1%. Mortality of about 10%."
    result = s46._classify_by_rules("Overview", body)
    assert result == "epidemiology_concept"


def test_backmatter_chunks_skipped_entirely():
    chunks = _chunk("L2-05", "clinical_feature", "Further information",
                     "See journal articles and websites for more.")
    new_text, changed, review_priority = s46._regex_remap_all(chunks, levels=(2,))
    assert changed == 0
    assert review_priority == []


# --- Unparsed-chunk accounting / metadata construction --------------------

def test_build_metadata_status_success_when_unparsed_ratio_low():
    text = _chunk("L2-01", "drug_info", "X", "body")
    meta = s46._build_metadata(text, sonnet_used=True, sonnet_failed_fallback=False,
                                sonnet_failure_reason=None, corrected=1,
                                unparsed_ids=[], tokens_used=100, chunks_reviewed=20)
    assert meta["status"] == "success"
    assert meta["chunks_unparsed"] == 0


def test_build_metadata_status_partial_success_when_unparsed_ratio_high():
    text = _chunk("L2-01", "drug_info", "X", "body")
    meta = s46._build_metadata(text, sonnet_used=True, sonnet_failed_fallback=False,
                                sonnet_failure_reason=None, corrected=1,
                                unparsed_ids=["L2-01", "L2-02", "L2-03"],
                                tokens_used=100, chunks_reviewed=20)
    assert meta["status"] == "partial_success"
    assert meta["chunks_unparsed"] == 3


def test_build_metadata_semantic_type_distribution():
    text = _chunk("L2-01", "drug_info", "X", "b1") + _chunk("L2-02", "drug_info", "Y", "b2")
    meta = s46._build_metadata(text, sonnet_used=False, sonnet_failed_fallback=False,
                                sonnet_failure_reason=None, corrected=0,
                                unparsed_ids=[], tokens_used=0)
    assert meta["semantic_type_distribution"]["drug_info"] == 2
    assert meta["total_chunks"] == 2


# --- Manual-review export / apply ------------------------------------------

def test_export_for_manual_review_batches_and_flags_priority():
    chunks = (_chunk("L2-01", "clinical_feature", "Generic",
                      "the dosing regimen has a half-life")
              + _chunk("L2-02", "drug_info", "Other", "unrelated body text"))
    _, _, review_priority = s46._regex_remap_all(chunks, levels=(2,))
    batches = s46.export_for_manual_review(chunks, levels=(2,), batch_size=25,
                                            review_priority=review_priority)
    assert len(batches) == 1
    assert "[CHECK: regex suggests drug_info]" in batches[0]
    assert "L2-01" in batches[0] and "L2-02" in batches[0]


def test_apply_manual_corrections_changes_matching_chunk():
    chunks = _chunk("L2-01", "clinical_feature", "X", "body")
    new_text, meta = s46.apply_manual_corrections(chunks, {"L2-01": "drug_info"})
    assert "semantic_type: drug_info" in new_text
    assert meta["chunks_corrected"] == 1
    assert meta["verification_method"] == "manual"


def test_apply_manual_corrections_ignores_chunk_id_with_no_matching_chunk():
    """Documents ACTUAL current behavior (not a v2.6.2 change): the loop
    only ever visits chunk_ids that exist in chunks_data, so a corrections
    key with no matching chunk is silently never applied and never
    reported in unparsed_chunk_ids either -- it simply isn't iterated over.
    This is a real gap in the legacy module (a truly bogus key is neither
    applied nor flagged), documented here as existing control flow, not
    fixed here (out of this stabilization release's narrow scope)."""
    chunks = _chunk("L2-01", "clinical_feature", "X", "body")
    new_text, meta = s46.apply_manual_corrections(chunks, {"L2-99-does-not-exist": "drug_info"})
    assert meta["chunks_corrected"] == 0
    assert meta["unparsed_chunk_ids"] == []  # silently ignored, not reported
    assert new_text == chunks  # unchanged


def test_apply_manual_corrections_invalid_semantic_type_is_a_silent_noop():
    """Also documents actual current behavior: an existing chunk_id paired
    with a NEW type outside SEMANTIC_TYPES is treated as a no-op (same
    code path as 'already correct'), NOT added to unparsed_chunk_ids --
    `unparsed` is only ever populated by the (hard to trigger under normal
    conditions) case where _get_semantic_type()'s regex-derived current
    type doesn't literally appear as 'semantic_type: X' in the chunk text."""
    chunks = _chunk("L2-01", "clinical_feature", "X", "body")
    new_text, meta = s46.apply_manual_corrections(chunks, {"L2-01": "not_a_real_type"})
    assert meta["chunks_corrected"] == 0
    assert meta["unparsed_chunk_ids"] == []
    assert new_text == chunks


def test_apply_manual_corrections_noop_when_new_type_equals_current():
    chunks = _chunk("L2-01", "drug_info", "X", "body")
    new_text, meta = s46.apply_manual_corrections(chunks, {"L2-01": "drug_info"})
    assert meta["chunks_corrected"] == 0


# --- Malformed model response handling (deterministic parsing) -----------

def test_parse_sonnet_verification_valid_json():
    response = '[{"chunk_id": "L2-01", "semantic_type": "drug_info", "confidence": 0.9}]'
    corrections, unparsed = s46._parse_sonnet_verification(response, ["L2-01", "L2-02"])
    assert corrections == {"L2-01": "drug_info"}
    assert unparsed == ["L2-02"]


def test_parse_sonnet_verification_malformed_json_returns_all_unparsed():
    response = "this is not json at all, the model said something weird"
    corrections, unparsed = s46._parse_sonnet_verification(response, ["L2-01", "L2-02"])
    assert corrections == {}
    assert set(unparsed) == {"L2-01", "L2-02"}


def test_parse_sonnet_verification_extracts_json_array_from_surrounding_prose():
    response = 'Sure, here is the answer:\n[{"chunk_id": "L2-01", "semantic_type": "drug_info"}]\nHope that helps!'
    corrections, unparsed = s46._parse_sonnet_verification(response, ["L2-01"])
    assert corrections == {"L2-01": "drug_info"}


def test_parse_sonnet_verification_ignores_invalid_semantic_type_value():
    response = '[{"chunk_id": "L2-01", "semantic_type": "not_a_real_type"}]'
    corrections, unparsed = s46._parse_sonnet_verification(response, ["L2-01"])
    assert corrections == {}
    assert unparsed == ["L2-01"]


# --- No-key/manual path (the common case in Claude Code sessions) --------

def test_stage_4_with_verification_below_budget_floor_flags_manual_verification():
    chunks = _chunk("L2-01", "clinical_feature", "Generic", "the dosing regimen has a half-life")
    final_text, meta = s46.stage_4_with_verification(
        chunks, "repaired source text", levels=(2,), min_budget_to_run=100,
    )
    assert meta["needs_manual_verification"] is True
    assert meta["sonnet_verification_used"] is False


# --- API-failure fallback behavior (mocked -- never calls the live API) --

def test_stage_4_with_verification_falls_back_when_api_call_raises():
    """Mocks _stage_4_6_sonnet_verification_all to raise, confirming
    stage_4_with_verification catches it and falls back to the regex
    baseline with needs_manual_verification=True rather than propagating
    the exception or silently shipping unverified output as final."""
    chunks = _chunk("L2-01", "clinical_feature", "Generic", "some body text here")
    with patch.object(s46, "_stage_4_6_sonnet_verification_all", side_effect=RuntimeError("API down")):
        final_text, meta = s46.stage_4_with_verification(
            chunks, "repaired source text", levels=(2,), min_budget_to_run=4000,
        )
    assert meta["sonnet_verification_used"] is False
    assert meta["sonnet_failed_fallback"] is True
    assert meta["needs_manual_verification"] is True
    assert "API down" in meta["sonnet_failure_reason"]


def test_stage_4_6_sonnet_verification_all_success_path_with_mocked_anthropic_client():
    """Mocks the Anthropic client entirely -- confirms the success path
    parses a well-formed response and applies corrections. No network call
    is made; `anthropic.Anthropic` is replaced with a MagicMock."""
    chunks = _chunk("L2-01", "clinical_feature", "Generic", "the dosing regimen has a half-life")

    fake_response = MagicMock()
    fake_response.content = [MagicMock(text='[{"chunk_id": "L2-01", "semantic_type": "drug_info"}]')]
    fake_response.usage.input_tokens = 100
    fake_response.usage.output_tokens = 50

    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_response

    fake_anthropic_module = MagicMock()
    fake_anthropic_module.Anthropic.return_value = fake_client

    with patch.dict(sys.modules, {"anthropic": fake_anthropic_module}):
        new_text, meta = s46._stage_4_6_sonnet_verification_all(
            chunks, "repaired source text", levels=(2,), max_output_tokens=1000,
        )
    assert meta["sonnet_verification_used"] is True
    assert meta["chunks_corrected"] == 1
    assert "semantic_type: drug_info" in new_text
    fake_client.messages.create.assert_called_once()


def test_stage_4_6_sonnet_verification_all_no_targets_returns_unchanged():
    """`from anthropic import Anthropic` is the first line of this function,
    unconditionally -- even a chapter with zero eligible targets requires
    the package to be importable. Mocked here for the same reason as the
    success-path test above, not because this path calls the API."""
    chunks = _chunk("L2-01", "clinical_feature", "Journal articles", "reference list here")
    with patch.dict(sys.modules, {"anthropic": MagicMock()}):
        new_text, meta = s46._stage_4_6_sonnet_verification_all(
            chunks, "repaired source text", levels=(2,), max_output_tokens=1000,
        )
    assert meta["chunks_corrected"] == 0
    assert new_text == chunks
