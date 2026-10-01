"""Tests for CDSS Multi-Modal Figure Asset Mapping and Clinical Algorithm Detection (v2.15.0)."""
import pytest
from pipeline.stages.stage_4_parse import extract_figure_metadata, detect_clinical_algorithm, make_chunk
from pipeline.stages.stage_6_validation import check_6_5_cdss_features


def test_extract_figure_metadata_markdown_images():
    body = "Clinical features of pericarditis.\n\n![Figure 18.4 ECG](assets/figures/ch18_fig_04.png)\n\nObserve ST elevation."
    has_fig, assets, captions = extract_figure_metadata(body)
    assert has_fig == "true"
    assert "assets/figures/ch18_fig_04.png" in assets
    assert "Figure 18.4 ECG" in captions


def test_extract_figure_metadata_citation_patterns():
    body = "The patient had diffuse ST elevation (Fig. 18.4: 12-lead ECG in acute pericarditis). Immediate echocardiogram was arranged."
    has_fig, assets, captions = extract_figure_metadata(body)
    assert any("assets/figures/ch18_fig_04" in a for a in assets)


def test_extract_figure_metadata_no_figures():
    body = "Standard medical text without figures or images."
    has_fig, assets, captions = extract_figure_metadata(body)
    assert has_fig == "false"
    assert assets == []
    assert captions == []


def test_detect_clinical_algorithm_scoring_system():
    body = "Calculate CURB-65 score: Confusion (1 pt), Urea > 7 (1 pt), RR >= 30 (1 pt). Score >= 3 requires ICU admission."
    is_algo, atype = detect_clinical_algorithm(body, "Community-Acquired Pneumonia — Severity Assessment")
    assert is_algo == "true"
    assert atype == "scoring_system"


def test_detect_clinical_algorithm_stepwise_escalation():
    body = "Step 1: Inhaled SABA as needed.\nStep 2: Add low-dose ICS.\nStep 3: Escalate to LABA + medium-dose ICS."
    is_algo, atype = detect_clinical_algorithm(body, "Asthma — Stepwise Pharmacotherapy")
    assert is_algo == "true"
    assert atype == "stepwise_escalation"


def test_detect_clinical_algorithm_decision_tree():
    body = "If low risk: order D-dimer. If negative: exclude PE. If positive or high risk: proceed to CTPA."
    is_algo, atype = detect_clinical_algorithm(body, "Pulmonary Embolism — Diagnostic Algorithm")
    assert is_algo == "true"
    assert atype == "decision_tree"


def test_detect_clinical_algorithm_plain_prose():
    body = "The pericardium consists of two layers, the visceral and parietal pericardium."
    is_algo, atype = detect_clinical_algorithm(body, "Anatomy and Physiology")
    assert is_algo == "false"
    assert atype is None


def test_make_chunk_full_cdss_frontmatter():
    body = "![ECG](assets/figures/ch18_fig_04.png)\nStep 1: Give oxygen.\nStep 2: Aspirin 300 mg."
    chunk = make_chunk("L2-001", 2, "management_step", "stemi", "STEMI — Management", 100, 150, body)
    assert "contains_figures: true" in chunk
    assert 'figure_assets: ["assets/figures/ch18_fig_04.png"]' in chunk
    assert "is_clinical_algorithm: true" in chunk
    assert "algorithm_type: stepwise_escalation" in chunk


def test_check_6_5_cdss_features_pass():
    rag = """---
chunk_id: L2-001
chunk_level: 2
disease_focus: asthma
coverage_status: complete
gap_note: ""
contains_figures: true
figure_assets: ["assets/figures/ch01_fig_01.png"]
is_clinical_algorithm: true
algorithm_type: decision_tree
---

Sample clinical text.
"""
    fails = check_6_5_cdss_features(rag)
    assert fails == []


def test_check_6_5_cdss_features_fail_invalid_algorithm_type():
    rag = """---
chunk_id: L2-001
chunk_level: 2
disease_focus: asthma
coverage_status: complete
gap_note: ""
contains_figures: false
is_clinical_algorithm: true
algorithm_type: invalid_type_name
---

Sample clinical text.
"""
    fails = check_6_5_cdss_features(rag)
    assert len(fails) == 1
    assert "algorithm_type ('invalid_type_name') is invalid" in fails[0]
