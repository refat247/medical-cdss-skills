"""Tests for v2.16.0 Provenance, Breadcrumbs, Figure Extensions, Stage 4.7, and MCQ Pairing."""
import json
import os
import pytest

from pipeline.checkpoint_utils import load_or_create_checkpoint
from pipeline.stages.stage_4_parse import (
    extract_figure_metadata,
    make_chunk,
    run_stage_4b,
)
from pipeline.stages.stage_4_7_serialize import (
    evaluate_clinical_completeness,
    evaluate_and_write_stage_4_7,
)
from pipeline.stages.stage_6_validation import check_6_6_provenance_and_breadcrumbs


def test_make_chunk_includes_provenance_and_breadcrumb():
    body = "Clinical features of acute myocardial infarction include central chest pain."
    chunk = make_chunk(
        cid="L2-001",
        level=2,
        sem_type="clinical_feature",
        disease="myocardial_infarction",
        topic="Clinical Features",
        start_l=10,
        end_l=25,
        body_text=body,
        page_numbers=[452, 453],
        pdf_page=18,
        breadcrumb="Cardiology > Ischaemic Heart Disease > Clinical Features",
    )

    assert "chunk_id: L2-001" in chunk
    assert "page_numbers: [452, 453]" in chunk
    assert "pdf_page: 18" in chunk
    assert 'breadcrumb: "Cardiology > Ischaemic Heart Disease > Clinical Features"' in chunk
    assert 'source_lines: "10-25"' in chunk


def test_dynamic_figure_extension_resolution(tmp_path):
    fig_dir = tmp_path / "assets" / "figures"
    fig_dir.mkdir(parents=True)
    
    target_img = fig_dir / "ch18_fig_04.jpeg"
    target_img.write_text("fake image content", encoding="utf-8")

    text_with_fig = "As illustrated in Fig. 18.4, coronary anatomy varies."
    has_fig, assets, captions = extract_figure_metadata(text_with_fig, out_dir=str(tmp_path))

    assert has_fig == "true"
    assert "assets/figures/ch18_fig_04.jpeg" in assets
    assert "assets/figures/ch18_fig_04.png" not in assets


def test_run_stage_4b_page_and_mcq_pairing(tmp_path):
    source_md = (
        "# Clinical Decision-Making\n\n"
        "<!-- page: 140 (pdf: 12) -->\n"
        "## Diagnostic Reasoning\n\n"
        "Diagnostic reasoning requires Bayesian probability.\n\n"
        "<!-- page: 141 -->\n"
        "### Cognitive Biases\n\n"
        "Heuristics often lead to cognitive errors.\n\n"
        "## Multiple Choice Questions\n\n"
        "1.1. Which cognitive bias represents anchoring?\n"
        "- A. Premature closure\n"
        "- B. Availability\n\n"
        "### Answers to Multiple Choice Questions\n\n"
        "1.1. Answer: A\n"
        "Premature closure occurs when an initial impression is fixed prematurely.\n"
    )

    prefix = "Davidson_25_Ch01_Clinical_decision_making"
    rep_file = tmp_path / f"{prefix}_REPAIRED_S2.md"
    rep_file.write_text(source_md, encoding="utf-8")

    load_or_create_checkpoint(
        source_path=str(rep_file),
        output_dir=str(tmp_path),
        prefix=prefix,
        ch_num="01",
        ch_slug="Clinical_decision_making",
    )

    res = run_stage_4b(
        rep_path=str(rep_file),
        out_dir=str(tmp_path),
        prefix=prefix,
    )

    assert res["l2_count"] >= 2
    chunks_file = tmp_path / f"{prefix}_chunks.md"
    chunks_content = chunks_file.read_text(encoding="utf-8")

    assert "page_numbers:" in chunks_content
    assert "breadcrumb:" in chunks_content
    assert "pdf_page: 12" in chunks_content

    assert "MCQ 1.1" in chunks_content
    assert "### Answer & Explanation" in chunks_content
    assert "Answer: A" in chunks_content
    assert "Premature closure occurs" in chunks_content


def test_evaluate_clinical_completeness():
    chunks_sample = (
        "---\nchunk_id: L2-001\nchunk_level: 2\nsemantic_type: pathophysiology\ndisease_focus: heart_failure\ntopic: Causes\n---\nCauses include CAD.\n\n"
        "---\nchunk_id: L2-002\nchunk_level: 2\nsemantic_type: clinical_feature\ndisease_focus: heart_failure\ntopic: Symptoms\n---\nSymptoms include dyspnoea.\n\n"
        "---\nchunk_id: L2-003\nchunk_level: 2\nsemantic_type: management_step\ndisease_focus: heart_failure\ntopic: Management\n---\nTreatment with ACE inhibitors and beta-blockers.\n\n"
        "---\nchunk_id: L2-004\nchunk_level: 2\nsemantic_type: laboratory_investigation\ndisease_focus: heart_failure\ntopic: Investigations\n---\nEchocardiography shows reduced EF.\n\n"
    )

    res = evaluate_clinical_completeness(chunks_sample)
    assert "heart_failure" in res["complete_diseases"]
    assert len(res["suspected_gap"]) == 0


def test_check_6_6_provenance_validation():
    valid_rag = (
        "---\nchunk_id: L2-001\nchunk_level: 2\npage_numbers: [142]\nbreadcrumb: \"Ch 1 > Section\"\n---\nValid chunk content.\n"
    )
    assert len(check_6_6_provenance_and_breadcrumbs(valid_rag)) == 0

    invalid_rag = (
        "---\nchunk_id: L2-002\nchunk_level: 2\npage_numbers: []\n---\nEmpty page numbers.\n"
    )
    fails = check_6_6_provenance_and_breadcrumbs(invalid_rag)
    assert len(fails) == 1
    assert "L2-002: page_numbers list is empty" in fails[0]


def test_stage_2_short_clinical_sentence_protection():
    from pipeline.stages.stage_2_repair import is_clinical
    line1 = "Administer intramuscular adrenaline 0.5 mg (0.5 mL of 1:1000) immediately."
    line2 = "Loading dose of IV amiodarone 300 mg over 30-60 min."
    line3 = "Contraindicated in severe renal failure with eGFR under 30 mL/min."
    line_junk = "Visit our telegram channel for more pirated medical books."

    assert is_clinical(line1) is True
    assert is_clinical(line2) is True
    assert is_clinical(line3) is True
    assert is_clinical(line_junk) is False


def test_stage_4_5d_expanded_medical_units():
    from pipeline.stages.stage_4_5d_clinical_fidelity import detect_unit
    src = "Infuse noradrenaline at 0.05 mcg/kg/min to maintain MAP over 65 mmHg (eGFR 45 mL/min/1.73m2, PaO2 10.2 kPa)."
    diffs, _ = detect_unit(src, src, "L2-001")
    assert len(diffs) == 0

    chunk_corrupt = "Infuse noradrenaline at 0.05 to maintain MAP over 65 (eGFR 45, PaO2 10.2)."
    diffs2, _ = detect_unit(src, chunk_corrupt, "L2-001")
    assert len(diffs2) >= 1


def test_detect_clinical_urgency_and_box():
    from pipeline.stages.stage_4_parse import detect_clinical_urgency_and_box
    emergency_text = "Immediate resuscitation with high-flow oxygen, IV access, and defibrillation."
    urgency, box_type = detect_clinical_urgency_and_box(emergency_text, "Cardiac Arrest Management", is_algo="false")
    assert urgency == "emergency"
    assert box_type == "emergency_management"

    prescribing_text = "Prescribing point: Check serum creatinine and electrolytes before starting ACE inhibitors."
    urgency2, box_type2 = detect_clinical_urgency_and_box(prescribing_text, "Prescribing Point: ACE Inhibitors", is_algo="false")
    assert box_type2 == "prescribing_point"

    routine_text = "Type 2 diabetes mellitus is characterised by progressive beta-cell dysfunction."
    urgency3, box_type3 = detect_clinical_urgency_and_box(routine_text, "Pathophysiology", is_algo="false")
    assert urgency3 == "routine"


def test_detect_drug_synonyms():
    from pipeline.stages.stage_4_parse import detect_drug_synonyms
    text = "Treatment of acute paracetamol poisoning with intravenous acetylcysteine or oral salbutamol in asthma."
    syns = detect_drug_synonyms(text)
    assert "acetaminophen" in syns
    assert "albuterol" in syns


def test_rule_j4_bold_micro_splitting(tmp_path):
    lines = ["# Cardiology", "<!-- page: 100 -->", "## Overview of Antiarrhythmic Drugs", "Antiarrhythmic drugs are classified by Vaughan Williams."]
    lines.extend([f"Paragraph fill line {i} to extend section length beyond forty lines for rule test." for i in range(35)])
    lines.append("**Class I Agents**")
    lines.append("Class I agents block sodium channels and slow phase 0 depolarisation.")
    lines.append("**Class II Agents**")
    lines.append("Class II agents are beta-blockers that decrease pacemaker automaticity.")
    lines.append("**Class III Agents**")
    lines.append("Class III agents block potassium channels and prolong action potential duration.")
    
    source_md = "\n\n".join(lines)
    prefix = "Davidson_25_Ch18_Cardiology"
    rep_file = tmp_path / f"{prefix}_REPAIRED_S2.md"
    rep_file.write_text(source_md, encoding="utf-8")

    load_or_create_checkpoint(
        source_path=str(rep_file),
        output_dir=str(tmp_path),
        prefix=prefix,
        ch_num="18",
        ch_slug="Cardiology",
    )

    res = run_stage_4b(
        rep_path=str(rep_file),
        out_dir=str(tmp_path),
        prefix=prefix,
    )

    assert res["l2_count"] >= 3
    chunks_file = tmp_path / f"{prefix}_chunks.md"
    content = chunks_file.read_text(encoding="utf-8")
    assert "Class I Agents" in content
    assert "Class II Agents" in content
    assert "Class III Agents" in content


def test_stage_5_4_stem_based_autolink(tmp_path):
    from pipeline.stages.stage_5_chunks import run_stage_5_4_autolink
    chunks_data = (
        "---\nchunk_id: L2-001\nchunk_level: 2\ndisease_focus: asthma\ntopic: Pathophysiology\n---\nAsthma overview.\n\n"
        "---\nchunk_id: L2-002\nchunk_level: 2\ndisease_focus: acute_severe_asthma\ntopic: Management\n---\nOxygen and salbutamol.\n\n"
        "---\nchunk_id: L2-003\nchunk_level: 2\ndisease_focus: diabetes_mellitus\ntopic: Overview\n---\nDiabetes overview.\n"
    )
    prefix = "Davidson_25_Ch19_Respiratory"
    c_file = tmp_path / f"{prefix}_chunks.md"
    c_file.write_text(chunks_data, encoding="utf-8")

    load_or_create_checkpoint(
        source_path=str(c_file),
        output_dir=str(tmp_path),
        prefix=prefix,
        ch_num="19",
        ch_slug="Respiratory",
    )

    res = run_stage_5_4_autolink(str(c_file), str(tmp_path), prefix)
    assert res["linked_chunks"] >= 2

    updated = c_file.read_text(encoding="utf-8")
    assert "related_chunks: [L2-002]" in updated or "related_chunks: [L2-001]" in updated


def test_mcq_multi_item_true_false_pairing(tmp_path):
    source_md = (
        "# Endocrinology\n\n"
        "<!-- page: 320 -->\n"
        "## Multiple Choice Questions\n\n"
        "2.1. Regarding diabetic ketoacidosis:\n"
        "- A. Arterial pH is typically > 7.35\n"
        "- B. Serum bicarbonate is elevated\n"
        "- C. Potassium replacement is required\n"
        "- D. Plasma glucose is usually elevated\n"
        "- E. Insulin should be given as an IV bolus\n\n"
        "### Answers to Multiple Choice Questions\n\n"
        "2.1. A: False, B: False, C: True, D: True, E: False\n"
        "In DKA, acidosis lowers pH, bicarbonate is reduced, and insulin infusion is preferred.\n"
    )
    prefix = "Davidson_25_Ch20_Endocrinology"
    rep_file = tmp_path / f"{prefix}_REPAIRED_S2.md"
    rep_file.write_text(source_md, encoding="utf-8")

    load_or_create_checkpoint(
        source_path=str(rep_file),
        output_dir=str(tmp_path),
        prefix=prefix,
        ch_num="20",
        ch_slug="Endocrinology",
    )

    res = run_stage_4b(
        rep_path=str(rep_file),
        out_dir=str(tmp_path),
        prefix=prefix,
    )

    assert res["l2_count"] >= 1
    chunks_file = tmp_path / f"{prefix}_chunks.md"
    chunks_content = chunks_file.read_text(encoding="utf-8")

    assert "MCQ 2.1" in chunks_content
    assert "### Answer & Explanation" in chunks_content
    assert "A: False, B: False, C: True, D: True, E: False" in chunks_content
    assert "acidosis lowers pH" in chunks_content
