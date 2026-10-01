"""v2.7.0 — deterministic-portion tests for stage_4_6_gemini_verification.py
Testing title/body rule classification, pure epidemiology detection, unparsed-chunk
accounting, metadata construction, manual-review export/apply, and control-flow
around the Gemini API path (mocked — never calls live network API).
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from pipeline import stage_4_6_gemini_verification as s46


def _chunk(cid, semantic_type, topic, body, level=2):
    return (
        f"---\nchunk_id: {cid}\nchunk_level: {level}\nsemantic_type: {semantic_type}\n"
        f"topic: {topic}\n---\n\n{body}\n"
    )


# --- Title-rule classification (auto-applied) ----------------------------

def test_gemini_title_rule_adverse_effects_reclassifies_to_drug_info():
    chunks = _chunk("L2-01", "management_step", "Adverse effects of bisphosphonates",
                     "Nausea and jaw osteonecrosis can occur.")
    new_text, changed, review_priority = s46._regex_remap_all(chunks, levels=(2,))
    assert changed == 1
    assert "semantic_type: drug_info" in new_text


def test_gemini_title_rule_investigations_reclassifies_to_laboratory_investigation():
    chunks = _chunk("L2-02", "clinical_feature", "Investigations",
                     "Blood tests are performed to confirm the diagnosis.")
    new_text, changed, _ = s46._regex_remap_all(chunks, levels=(2,))
    assert changed == 1
    assert "semantic_type: laboratory_investigation" in new_text


def test_gemini_title_rule_does_not_fire_when_already_correct():
    chunks = _chunk("L2-03", "drug_info", "Adverse effects of steroids", "Weight gain occurs.")
    new_text, changed, _ = s46._regex_remap_all(chunks, levels=(2,))
    assert changed == 0


# --- Body-rule classification (advisory only, never auto-applied) --------

def test_gemini_body_rules_never_auto_apply_only_flag_review_priority():
    chunks = _chunk("L2-04", "clinical_feature", "Generic heading",
                     "The dosing regimen has a long half-life and antibiotic properties.")
    new_text, changed, review_priority = s46._regex_remap_all(chunks, levels=(2,))
    assert changed == 0  # not auto-applied
    assert "semantic_type: clinical_feature" in new_text  # unchanged
    assert any(p["chunk_id"] == "L2-04" and p["candidate_type"] == "drug_info"
               for p in review_priority)


def test_gemini_classify_by_rules_title_wins_over_body():
    result = s46._classify_by_rules("Adverse effects of X", "some symptom text")
    assert result == "drug_info"


def test_gemini_classify_by_rules_falls_back_to_body_when_no_title_match():
    result = s46._classify_by_rules("Generic heading", "the dosing regimen has a half-life")
    assert result == "drug_info"


def test_gemini_classify_by_rules_pure_epidemiology_detector():
    body = "Incidence is 2-10 per 100 000. Prevalence is around 1%. Mortality of about 10%."
    result = s46._classify_by_rules("Overview", body)
    assert result == "epidemiology_concept"


def test_gemini_backmatter_chunks_skipped_entirely():
    chunks = _chunk("L2-05", "clinical_feature", "Further information",
                     "See journal articles and websites for more.")
    new_text, changed, review_priority = s46._regex_remap_all(chunks, levels=(2,))
    assert changed == 0
    assert review_priority == []


# --- Unparsed-chunk accounting / metadata construction --------------------

def test_gemini_build_metadata_status_success():
    text = _chunk("L2-01", "drug_info", "X", "body")
    meta = s46._build_metadata(text, gemini_used=True, gemini_failed_fallback=False,
                                gemini_failure_reason=None, corrected=1,
                                unparsed_ids=[], tokens_used=100, chunks_reviewed=20)
    assert meta["status"] == "success"
    assert meta["chunks_unparsed"] == 0
    assert meta["gemini_verification_used"] is True
    assert meta["sonnet_verification_used"] is True  # alias check


def test_gemini_build_metadata_status_partial_success_when_unparsed_ratio_high():
    text = _chunk("L2-01", "drug_info", "X", "body")
    meta = s46._build_metadata(text, gemini_used=True, gemini_failed_fallback=False,
                                gemini_failure_reason=None, corrected=0,
                                unparsed_ids=["L2-01", "L2-02", "L2-03"],
                                tokens_used=50, chunks_reviewed=10)
    assert meta["status"] == "partial_success"
    assert meta["chunks_unparsed"] == 3


# --- Manual review export and application --------------------------------

def test_gemini_export_for_manual_review_batches():
    chunks = (
        _chunk("L2-01", "clinical_feature", "Title 1", "Body 1") +
        _chunk("L2-02", "clinical_feature", "Title 2", "Body 2")
    )
    batches = s46.export_for_manual_review(chunks, levels=(2,), batch_size=1)
    assert len(batches) == 2
    assert "[L2-01]" in batches[0]
    assert "[L2-02]" in batches[1]


def test_gemini_apply_manual_corrections():
    chunks = _chunk("L2-01", "clinical_feature", "Title 1", "Body 1")
    corrections = {"L2-01": "drug_info"}
    new_text, meta = s46.apply_manual_corrections(chunks, corrections)
    assert "semantic_type: drug_info" in new_text
    assert meta["chunks_corrected"] == 1
    assert meta["chunks_unparsed"] == 0
    assert meta["verification_method"] == "manual"


# --- Parsing responses ---------------------------------------------------

def test_gemini_parse_verification_json():
    response = json.dumps([
        {"chunk_id": "L2-01", "semantic_type": "drug_info", "confidence": 0.95},
        {"chunk_id": "L2-02", "semantic_type": "management_step", "confidence": 0.90},
    ])
    corrections, unparsed = s46._parse_gemini_verification(response, ["L2-01", "L2-02", "L2-03"])
    assert corrections == {"L2-01": "drug_info", "L2-02": "management_step"}
    assert unparsed == ["L2-03"]


def test_offline_adjudicate_all():
    chunks = (
        _chunk("L2-01", "clinical_feature", "Pharmacologic therapy", "Administer metformin 500 mg daily.") +
        _chunk("L2-02", "clinical_feature", "Recommendations", "Recommendation 9.4: In adults with T2D, initiate GLP-1.") +
        _chunk("L2-03", "clinical_feature", "Screening and Diagnostic Tests", "Measure HbA1c and eGFR twice yearly.")
    )
    new_text, meta = s46.offline_adjudicate_all(chunks, levels=(2,))
    assert "semantic_type: drug_info" in new_text or "semantic_type: management_step" in new_text
    assert meta["verification_method"] == "offline_deterministic_clinical_rules"
    assert meta["needs_manual_verification"] is False
    assert meta["chunks_reviewed"] == 3
    assert meta["chunks_unparsed"] == 0
    assert meta["status"] == "success"

