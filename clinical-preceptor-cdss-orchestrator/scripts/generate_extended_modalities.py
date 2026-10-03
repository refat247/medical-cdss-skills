#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
GENERATE EXTENDED MODALITIES (v1.2.1)
Extracts and manufactures the 7 Additional Untapped Clinical & Educational Modalities
from D:\HABIJABI_FULL:
1. Multimodal Clinical Image VQA & OSCE Visual Spotters (169 Media Files)
2. Tiered Residency Progression Curriculum (Tier 1 Intern -> Tier 2 MO -> Tier 3 FCPS/MRCP)
3. GraphRAG / Pathophysiological Causal Knowledge Graph (Entity-Relation Triplets)
4. Ward SBAR On-Call Shift Handover Checklists
5. Patient-Facing Health Literacy & Folk Counseling Leaflets (বাংলা)
6. High-Yield Anki Spaced-Repetition Cloze Decks (.tsv)
7. Ward Pharmacovigilance & "Never-Events" Toxic Drug Matrix
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
from pathlib import Path
import argparse
from typing import List, Dict, Any, Tuple

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

__version__ = "1.2.1"
VERSION = "1.2.1"

CORPUS_ROOT = Path(r"D:\HABIJABI_FULL")
MEDIA_DIR = CORPUS_ROOT / "02_RAW_MEDIA"
NORMALIZED_DIR = CORPUS_ROOT / "03_NORMALIZED_CORPUS"
PERSONA_DIR = CORPUS_ROOT / "04_PERSONA" if (CORPUS_ROOT / "04_PERSONA").exists() else CORPUS_ROOT / "04_KAWSAR_PERSONA"
BRIDGE_DIR = CORPUS_ROOT / "05_TEXTBOOK_BRIDGE" if (CORPUS_ROOT / "05_TEXTBOOK_BRIDGE").exists() else CORPUS_ROOT / "05_DAVIDSON_BRIDGE"
EXPORTS_DIR = CORPUS_ROOT / "08_EXPORTS"

def configure_workspace(ws: Path):
    global CORPUS_ROOT, MEDIA_DIR, NORMALIZED_DIR, PERSONA_DIR, BRIDGE_DIR, EXPORTS_DIR
    CORPUS_ROOT = ws
    MEDIA_DIR = CORPUS_ROOT / "02_RAW_MEDIA"
    NORMALIZED_DIR = CORPUS_ROOT / "03_NORMALIZED_CORPUS"
    PERSONA_DIR = CORPUS_ROOT / "04_PERSONA" if (CORPUS_ROOT / "04_PERSONA").exists() else CORPUS_ROOT / "04_KAWSAR_PERSONA"
    BRIDGE_DIR = CORPUS_ROOT / "05_TEXTBOOK_BRIDGE" if (CORPUS_ROOT / "05_TEXTBOOK_BRIDGE").exists() else CORPUS_ROOT / "05_DAVIDSON_BRIDGE"
    EXPORTS_DIR = CORPUS_ROOT / "08_EXPORTS"

def _md_uri(record_id: str) -> str:
    """Link to a record's markdown INSIDE the configured workspace (links were hard-coded to file:///D:/HABIJABI_FULL)."""
    p = (NORMALIZED_DIR / "MARKDOWN" / f"{record_id}.md")
    try:
        return p.resolve().as_uri()
    except ValueError:
        return p.as_posix()


def _has_word(text: str, kw: str) -> bool:
    """Whole-word keyword test ('gra' must not match 'Graves', 'iv' must not match 'Hypertensive')."""
    return re.search(r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])", text) is not None


def load_claims() -> List[Dict[str, str]]:
    claims_csv = NORMALIZED_DIR / "TABLES" / "clinical_claims.csv"
    if not claims_csv.exists():
        return []
    with claims_csv.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def load_english_synthesis_records() -> List[Dict[str, Any]]:
    rag_file = EXPORTS_DIR / "RAG" / "habijabi_english_cdss.jsonl"
    if not rag_file.exists():
        return []
    records = []
    with rag_file.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records

def load_bridge() -> Dict[str, Dict[str, str]]:
    bridge_csv = BRIDGE_DIR / "BRIDGE_TABLES" / "davidson_bridge_registry.csv"
    bridge_map = {}
    if bridge_csv.exists():
        with bridge_csv.open("r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rid = row.get("habijabi_record_id", "")
                if rid:
                    bridge_map[rid] = row
    return bridge_map

# ==============================================================================
# MODALITY 1: MULTIMODAL CLINICAL IMAGE VQA & OSCE VISUAL SPOTTERS
# ==============================================================================
def build_modality_1_visual_spotters(records: List[Dict[str, Any]], claims: List[Dict[str, str]]):
    print("📸 [1/7] Building Multimodal Clinical Image VQA & OSCE Visual Spotters...")
    osce_dir = EXPORTS_DIR / "OSCE"
    osce_dir.mkdir(parents=True, exist_ok=True)

    # Map record_id -> record
    rec_map = {r["record_id"]: r for r in records}
    claim_map = {}
    for c in claims:
        rid = c.get("record_id", "")
        if rid not in claim_map:
            claim_map[rid] = []
        claim_map[rid].append(c)

    # Find all images
    images = sorted(list(MEDIA_DIR.glob("*/*/*.jpeg")) + list(MEDIA_DIR.glob("*/*/*.jpg")) + list(MEDIA_DIR.glob("*/*/*.png")))
    
    catalog_rows = []
    spotter_records = []

    for img_path in images:
        rel_path = img_path.relative_to(CORPUS_ROOT)
        media_id = img_path.stem
        # Extract record_id from path
        # Typically 02_RAW_MEDIA\HABIJABI-001\ORIGINAL_POST\HABIJABI-001__MEDIA_001.jpeg
        parts = img_path.parts
        record_id = "UNKNOWN"
        for p in parts:
            if p.startswith("HABIJABI-"):
                record_id = p
                break

        # Compute SHA-256
        sha256 = hashlib.sha256(img_path.read_bytes()).hexdigest()
        rec = rec_map.get(record_id, None)

        domain = rec["domain"] if rec else "General Medicine"
        condition = rec["primary_condition"] if rec else "Clinical Pathology"
        title = rec["title"] if rec else "Clinical Case Photograph"

        # Determine visual modality heuristic
        fname_lower = img_path.name.lower()
        if "ecg" in fname_lower or "cardio" in domain.lower() and "ecg" in title.lower():
            vis_modality = "ECG Rhythm Strip / 12-Lead Tracing"
        elif "xray" in fname_lower or "cxr" in fname_lower or "radiolog" in domain.lower():
            vis_modality = "Radiology (X-Ray / CT)"
        elif "pbf" in fname_lower or "blood" in fname_lower or "haematolog" in domain.lower():
            vis_modality = "Haematology (Peripheral Blood Film Photomicrograph)"
        elif "chart" in fname_lower or "algorithm" in fname_lower:
            vis_modality = "Clinical Diagnostic Flowchart"
        else:
            vis_modality = "Clinical Bedside Physical Sign / Pathology Plate"

        # Spot question & answer
        finding = f"Visual evidence associated with {condition} ({title})"
        question = (
            f"Examine the clinical image from {record_id} ({vis_modality}).\n"
            f"1. Identify the primary clinical or pathological anomaly demonstrated.\n"
            f"2. What underlying pathophysiological mechanism accounts for this appearance in {condition}?\n"
            f"3. What is the definitive confirmatory investigation or immediate bedside precaution?"
        )
        answer = (
            f"DIAGNOSTIC SYNTHESIS ({condition}):\n"
            f"• Finding: Characteristic features of {condition}.\n"
            f"• Mechanism: {rec['pathophysiology'][:280] if rec else 'Pathological anomaly as documented in clinical synthesis.'}...\n"
            f"• Bedside Action / Precautions: {rec['treatment'][:200] if rec else 'Follow protocol.'}..."
        )

        row = {
            "media_id": media_id,
            "record_id": record_id,
            "file_path": str(rel_path).replace("\\", "/"),
            "sha256": sha256,
            "clinical_domain": domain,
            "primary_condition": condition,
            "visual_modality": vis_modality,
            "diagnostic_finding": finding,
            "spot_question": question.replace("\n", " "),
            "answer_key": answer.replace("\n", " ")
        }
        catalog_rows.append(row)

        spotter_records.append({
            "station_id": f"OSCE-{media_id}",
            "record_id": record_id,
            "image_uri": str(rel_path).replace("\\", "/"),
            "domain": domain,
            "condition": condition,
            "modality": vis_modality,
            "question": question,
            "answer_key": answer,
            "pearls": rec["pearls"] if rec else ""
        })

    # Write CSV catalog
    catalog_csv = MEDIA_DIR / "image_catalog.csv"
    with catalog_csv.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["media_id", "record_id", "file_path", "sha256", "clinical_domain", "primary_condition", "visual_modality", "diagnostic_finding", "spot_question", "answer_key"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(catalog_rows)

    # Write JSONL spotter
    spotter_jsonl = osce_dir / "visual_spotters.jsonl"
    with spotter_jsonl.open("w", encoding="utf-8") as f:
        for s in spotter_records:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"  ✅ Cataloged {len(catalog_rows)} media assets in {catalog_csv}")
    print(f"  ✅ Exported {len(spotter_records)} interactive OSCE stations in {spotter_jsonl}")

# ==============================================================================
# MODALITY 2: TIERED RESIDENCY PROGRESSION CURRICULUM
# ==============================================================================
def build_modality_2_curriculum(records: List[Dict[str, Any]], bridge_map: Dict[str, Dict[str, str]]):
    print("🎓 [2/7] Building Tiered Residency Progression Curriculum...")
    curr_dir = EXPORTS_DIR / "CURRICULUM"
    curr_dir.mkdir(parents=True, exist_ok=True)

    tier_rows = []
    tier_counts = {"Tier 1": 0, "Tier 2": 0, "Tier 3": 0}

    # Classification Heuristics
    t1_keywords = ["fluid", "drop", "dengue", "hypothyroidism", "anemia", "mentzer", "iron", "malaria", "vomiting", "diarrhea", "iv", "cbc"]
    t3_keywords = ["aldosteronism", "gra", "liddle", "channelopathy", "dmpk", "anticipation", "multiple myeloma", "aflp", "ttp", "hus", "linezolid", "adamts13", "cyp11b1", "chimeric"]

    for r in records:
        rid = r["record_id"]
        title = r["title"]
        domain = r["domain"]
        cond = r["primary_condition"]
        text_corpus = (title + " " + domain + " " + cond).lower()

        if any(_has_word(text_corpus, k) for k in t3_keywords):
            tier = "Tier 3"
            cadre = "Postgraduate Trainee / FCPS Part II / MD Residency / MRCP UK"
            competency = "Complex Syndromic Differential, Genetic Channelopathies & High-Risk Pharmacotherapy"
            prereq = "Advanced systemic pathophysiology, molecular genetics, and toxic drug interactions"
        elif any(_has_word(text_corpus, k) for k in t1_keywords):
            tier = "Tier 1"
            cadre = "Intern / House Officer / Foundation Year Doctor"
            competency = "Bedside Emergency Triage, Dynamic Fluid Drop Calculations, Routine Panel Interpretation"
            prereq = "Basic undergraduate medicine, normal laboratory ranges, gravity IV calibration"
        else:
            tier = "Tier 2"
            cadre = "Medical Officer / General Practitioner / Ward Registrar"
            competency = "Acute Disease Exacerbation Management, Outpatient Pitfalls & Safe Polypharmacy"
            prereq = "Clinical pharmacology, disease staging, and inpatient admission criteria"

        tier_counts[tier] += 1
        b_entry = bridge_map.get(rid, {})
        davidson_ref = f"{b_entry.get('davidson_chapter_number', '')} ({b_entry.get('davidson_chapter_title', '')})" if b_entry else "General Internal Medicine"

        tier_rows.append({
            "record_id": rid,
            "series_number": r.get("series_number", ""),
            "title": title,
            "clinical_domain": domain,
            "primary_condition": cond,
            "curriculum_tier": tier,
            "target_cadre": cadre,
            "core_competencies": competency,
            "prerequisite_knowledge": prereq,
            "davidson_textbook_bridge": davidson_ref,
            "exam_yield": "High (FCPS/MRCP SBA Stem)"
        })

    # Save CSV
    tiers_csv = NORMALIZED_DIR / "TABLES" / "residency_curriculum_tiers.csv"
    tiers_csv.parent.mkdir(parents=True, exist_ok=True)      # crashed with FileNotFoundError on an unscaffolded workspace
    with tiers_csv.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "record_id", "series_number", "title", "clinical_domain", "primary_condition",
            "curriculum_tier", "target_cadre", "core_competencies", "prerequisite_knowledge",
            "davidson_textbook_bridge", "exam_yield"
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(tier_rows)

    # Save Markdown Curriculum Guide
    curr_md = curr_dir / "residency_progression_guide.md"
    with curr_md.open("w", encoding="utf-8") as f:
        f.write("# HABIJABI Clinical Residency Progression Curriculum\n\n")
        f.write("A 3-Tier Structured Competency Framework mapping Dr. Kawsar Uddin's 137 clinical cases across postgraduate medical training milestones.\n\n")
        f.write(f"- **Tier 1 (Intern / House Officer)**: {tier_counts['Tier 1']} cases\n")
        f.write(f"- **Tier 2 (Medical Officer / General Practitioner)**: {tier_counts['Tier 2']} cases\n")
        f.write(f"- **Tier 3 (Postgraduate Trainee / FCPS / MRCP)**: {tier_counts['Tier 3']} cases\n\n")
        f.write("---\n\n")

        for current_tier in ["Tier 1", "Tier 2", "Tier 3"]:
            f.write(f"## {current_tier} Milestone Curriculum\n\n")
            f.write("| Record ID | Topic | Domain | Core Clinical Competency | Davidson 25th Reference |\n")
            f.write("|---|---|---|---|---|\n")
            for item in tier_rows:
                if item["curriculum_tier"] == current_tier:
                    f.write(f"| [`{item['record_id']}`]({_md_uri(item['record_id'])}) | **{item['title']}** | {item['clinical_domain']} | {item['core_competencies']} | {item['davidson_textbook_bridge']} |\n")
            f.write("\n---\n\n")

    print(f"  ✅ Classified {len(records)} cases: Tier 1 ({tier_counts['Tier 1']}), Tier 2 ({tier_counts['Tier 2']}), Tier 3 ({tier_counts['Tier 3']})")
    print(f"  ✅ Saved {tiers_csv}")
    print(f"  ✅ Generated {curr_md}")

# ==============================================================================
# MODALITY 3: GRAPHRAG / PATHOPHYSIOLOGICAL CAUSAL KNOWLEDGE GRAPH
# ==============================================================================
def build_modality_3_causal_graph(records: List[Dict[str, Any]], claims: List[Dict[str, str]]):
    print("🕸️ [3/7] Building GraphRAG / Pathophysiological Causal Knowledge Graph...")
    graph_dir = EXPORTS_DIR / "GRAPH"
    graph_dir.mkdir(parents=True, exist_ok=True)

    triplets = []
    
    # 1. From Claims
    for c in claims:
        cid = c.get("claim_id", "")
        rid = c.get("record_id", "")
        dis = c.get("disease", "").strip() or "General Condition"
        dom = c.get("clinical_domain", "").strip()
        ctype = c.get("claim_type", "").strip()
        text = c.get("claim_text", "").strip()

        if ctype == "CONTRAINDICATION":
            # Extract subject and contraindication
            triplets.append({
                "source_id": cid,
                "record_id": rid,
                "subject_entity": dis,
                "predicate": "CONTRAINDICATES",
                "object_entity": text[:120],
                "relation_type": "CLINICAL_SAFETY_GATE",
                "clinical_domain": dom,
                "evidence_class": "Class B (Kawsar Clinical Teaching)"
            })
        elif ctype == "DIFFERENTIAL" or ctype == "DIAGNOSIS":
            triplets.append({
                "source_id": cid,
                "record_id": rid,
                "subject_entity": dis,
                "predicate": "DIAGNOSTIC_PATHWAY",
                "object_entity": text[:120],
                "relation_type": "DIAGNOSTIC_LOGIC",
                "clinical_domain": dom,
                "evidence_class": "Class B (Kawsar Clinical Teaching)"
            })
        elif ctype == "MECHANISM":
            triplets.append({
                "source_id": cid,
                "record_id": rid,
                "subject_entity": dis,
                "predicate": "PATHOPHYSIOLOGICAL_MECHANISM",
                "object_entity": text[:120],
                "relation_type": "CELLULAR_CAUSATION",
                "clinical_domain": dom,
                "evidence_class": "Class B (Kawsar Clinical Teaching)"
            })
        elif ctype in ["TREATMENT", "TREATMENT_PROTOCOL", "CALCULATION_HEURISTIC"]:
            triplets.append({
                "source_id": cid,
                "record_id": rid,
                "subject_entity": dis,
                "predicate": "THERAPEUTIC_ACTION",
                "object_entity": text[:120],
                "relation_type": "THERAPEUTIC_MANAGEMENT",
                "clinical_domain": dom,
                "evidence_class": "Class B (Kawsar Clinical Teaching)"
            })

    # 2. Add Handcrafted High-Precision Core Physiological Triplet Rules
    hardcoded_triplets = [
        ("Severe HTN + Hypokalemia in Young Patient", "INDICATES_MECHANISM", "Mineralocorticoid Excess (Aldosteronism)", "Endocrinology", "HABIJABI-001"),
        ("Familial Glucocorticoid Remediable Aldosteronism (GRA)", "CAUSED_BY", "Chimeric CYP11B1/CYP11B2 Gene under ACTH Control", "Genetics / Endocrinology", "HABIJABI-001"),
        ("Familial Glucocorticoid Remediable Aldosteronism (GRA)", "TREATED_BY", "Exogenous Glucocorticoids (Suppresses Pituitary ACTH)", "Therapeutics", "HABIJABI-001"),
        ("Bilateral Renal Artery Stenosis", "CONTRAINDICATES", "ACE Inhibitors / ARBs (Causes Acute Intraglomerular Pressure Collapse)", "Nephrology / Safety", "HABIJABI-001"),
        ("Myotonic Dystrophy Type 1", "CAUSED_BY", "CTG Triplet Repeat Expansion in DMPK Gene (19q13.3)", "Neurology / Genetics", "HABIJABI-002"),
        ("Myotonic Dystrophy Type 1", "EXHIBITS", "Genetic Anticipation via Maternal Transmission", "Genetics", "HABIJABI-002"),
        ("Acute Gouty Arthritis Flare", "CONTRAINDICATES", "Initiation of Urate-Lowering Therapy (Allopurinol/Febuxostat)", "Rheumatology / Safety", "HABIJABI-003"),
        ("Pregnancy 1st Trimester Thyrotoxicosis", "PREFERS", "Propylthiouracil (PTU) over Carbimazole", "Obstetrics / Endocrinology", "HABIJABI-005"),
        ("Pregnancy", "STRICTLY_CONTRAINDICATES", "Radioactive Iodine I-131 (Permanent Fetal Thyroid Ablation)", "Obstetrics / Safety", "HABIJABI-005"),
        ("Subacute Thyroiditis (De Quervain's)", "DIFFERENTIATES_FROM_GRAVES", "Severe Anterior Neck Pain + Markedly Elevated ESR", "Endocrinology", "HABIJABI-006"),
        ("Subclinical Hypothyroidism", "DEFINED_BY", "Elevated TSH with Normal Free T4/T3", "Endocrinology", "HABIJABI-007"),
        ("Acute Fatty Liver of Pregnancy (AFLP)", "EMERGENCY_HALLMARK", "Third Trimester Jaundice + Profound Hypoglycemia + Coagulopathy", "Obstetrics / Hepatology", "HABIJABI-010"),
        ("Severe Dengue Shock Syndrome", "PATHOPHYSIOLOGICAL_TRIGGER", "Endothelial Plasma Leakage into Third Spaces (Not Blood Loss Alone)", "Infectious Disease", "HABIJABI-011"),
        ("Dengue Fluid Resuscitation", "CALCULATED_AS", "Maintenance Fluid + 5% Deficit over 24-48 Hours", "Critical Care", "HABIJABI-012"),
        ("Standard IV Infusion Set (20 gtt/mL)", "DROP_FORMULA", "Drops per Minute = mL per Hour divided by 3", "Emergency Arithmetic", "HABIJABI-013"),
        ("Rheumatic Mitral Stenosis", "AUSCULTATORY_TRIAD", "Loud S1 + Opening Snap + Low-Pitched Mid-Diastolic Murmur", "Cardiology", "HABIJABI-014"),
        ("Liddle's Syndrome", "CAUSED_BY", "Constitutive Gain-of-Function Activation of ENaC Channels", "Nephrology / Genetics", "HABIJABI-015"),
        ("Liddle's Syndrome", "TREATED_BY", "Amiloride / Triamterene (Spironolactone is Ineffective)", "Therapeutics", "HABIJABI-015"),
        ("Pregnancy 1st Trimester", "CONTRAINDICATES", "High-dose Vitamin A (>10,000 IU/day Retinol)", "Obstetrics / Safety", "HABIJABI-016"),
        ("Anemia of Chronic Disease", "MECHANISM", "IL-6 Induces Hepcidin degrading Ferroportin -> Iron Trapped in Macrophages", "Haematology", "HABIJABI-017"),
        ("Microcytic Anemia with Mentzer Index < 13", "INDICATES", "Thalassemia Trait (Iron Therapy Contraindicated)", "Haematology / Safety", "HABIJABI-022"),
        ("Linezolid Administration", "CONTRAINDICATES_COPRESCRIPTION", "SSRIs / SNRIs (Precipitates Fatal Serotonin Syndrome via MAO Inhibition)", "Pharmacology / Safety", "HABIJABI-086"),
        ("Thrombotic Thrombocytopenic Purpura (TTP)", "CONTRAINDICATES", "Platelet Transfusion (Fuels Microvascular Thrombosis)", "Haematology / Safety", "HABIJABI-095")
    ]

    for idx, (subj, pred, obj, dom, rid) in enumerate(hardcoded_triplets, start=1):
        triplets.append({
            "source_id": f"TRIP-CORE-{idx:03d}",
            "record_id": rid,
            "subject_entity": subj,
            "predicate": pred,
            "object_entity": obj,
            "relation_type": "EXPERT_HEURISTIC_TRIPLET",
            "clinical_domain": dom,
            "evidence_class": "Class B (Kawsar Clinical Teaching)"
        })

    # Save CSV
    graph_csv = NORMALIZED_DIR / "TABLES" / "causal_knowledge_graph_triplets.csv"
    with graph_csv.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["source_id", "record_id", "subject_entity", "predicate", "object_entity", "relation_type", "clinical_domain", "evidence_class"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(triplets)

    # Save JSONL
    graph_jsonl = graph_dir / "causal_knowledge_graph.jsonl"
    with graph_jsonl.open("w", encoding="utf-8") as f:
        for t in triplets:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    print(f"  ✅ Built {len(triplets)} pathophysiological causal triplets in {graph_csv}")
    print(f"  ✅ Exported GraphRAG dataset to {graph_jsonl}")

# ==============================================================================
# MODALITY 4: WARD SBAR ON-CALL SHIFT HANDOVER CHECKLISTS
# ==============================================================================
def build_modality_4_sbar_handovers(records: List[Dict[str, Any]]):
    print("📋 [4/7] Building Ward SBAR On-Call Shift Handover Checklists...")
    sbar_dir = EXPORTS_DIR / "SBAR_HANDOVERS"
    sbar_dir.mkdir(parents=True, exist_ok=True)

    # Select high-acuity cases for SBAR cards
    high_acuity_cases = [
        {
            "id": "SBAR-001",
            "record_id": "HABIJABI-012",
            "condition": "Severe Dengue with Plasma Leakage / Dengue Shock Syndrome",
            "situation": "Patient in Critical Phase of Dengue (Day 4-6 of fever) with rising hematocrit and signs of plasma leakage.",
            "background": "Dengue hemorrhagic fever; plasma is leaking into pleural and peritoneal third-spaces; external bleeding may be minimal.",
            "assessment": "High risk of sudden hypovolemic shock. Hematocrit rising > 20% indicates worsening hemoconcentration. Urine output < 0.5 mL/kg/hr indicates renal hypoperfusion.",
            "recommendation": "Strictly calculate Maintenance + 5% Deficit over 24-48 hours. Titrate gravity drip using formula: drops/min = mL/hr ÷ 3. Check HCT every 6 hours. DO NOT administer blind large-volume fluid boluses which trigger fatal pulmonary edema."
        },
        {
            "id": "SBAR-002",
            "record_id": "HABIJABI-001",
            "condition": "Severe Young-Onset Hypertension with Hypokalemia",
            "situation": "22-year-old male admitted with BP 210/120 mmHg, persistent headache, and serum K+ 2.7 mmol/L.",
            "background": "Resistant to triple-therapy antihypertensives. Strong suspicion of secondary hypertension (Bilateral RAS vs Familial Glucocorticoid Remediable Aldosteronism / GRA).",
            "assessment": "Critical risk: ACE inhibitors or ARBs can precipitate acute kidney shutdown if bilateral RAS is present. Severe hypokalemia predisposes to cardiac dysrhythmias.",
            "recommendation": "Replenish potassium immediately with IV/oral KCl under ECG monitoring. HOLD ACE inhibitors and ARBs pending Renal Doppler ultrasound. Send Aldosterone/Renin ratio prior to starting spironolactone."
        },
        {
            "id": "SBAR-003",
            "record_id": "HABIJABI-010",
            "condition": "Acute Fatty Liver of Pregnancy (AFLP)",
            "situation": "Third-trimester primigravida presenting with acute onset jaundice, encephalopathy, and severe hypoglycemia.",
            "background": "Mitochondrial defect in fetal-maternal fatty acid beta-oxidation. Medical and obstetric emergency.",
            "assessment": "Impending hepatic failure, DIC, and maternal-fetal demise.",
            "recommendation": "Start 10% or 25% Dextrose continuous infusion immediately to maintain blood glucose > 4 mmol/L. Check PT/INR and fibrinogen for DIC. Alert obstetrics senior registrar and neonatal ICU for emergent delivery regardless of gestational age."
        },
        {
            "id": "SBAR-004",
            "record_id": "HABIJABI-003",
            "condition": "Acute Monoarthritis (Gout Flare vs Septic Joint)",
            "situation": "52-year-old male with acute, excruciating swelling and erythema of the 1st MTP joint / knee.",
            "background": "History of alcohol intake and hyperuricemia; acute severe pain waking patient from sleep.",
            "assessment": "Severe acute inflammation. Inadvertent allopurinol initiation will destabilize urate crystals and aggravate flare.",
            "recommendation": "Start Colchicine (0.5 mg BD/TDS) or oral NSAID with PPI gastroprotection. DO NOT start Allopurinol or Febuxostat tonight; defer urate lowering therapy for 4-6 weeks post flare resolution. If fever is present, perform diagnostic arthrocentesis to rule out septic arthritis."
        },
        {
            "id": "SBAR-005",
            "record_id": "HABIJABI-086",
            "condition": "Severe MRSA/VRE Infection — Linezolid Co-administration",
            "situation": "Inpatient prescribed IV Linezolid 600mg BD for hospital-acquired MRSA pneumonia.",
            "background": "Patient has concurrent major depression treated with Escitalopram (SSRI) or Venlafaxine (SNRI).",
            "assessment": "Extreme risk of fatal Serotonin Syndrome due to non-selective MAO inhibition by Linezolid interacting with serotonin reuptake blockade.",
            "recommendation": "HALT Linezolid immediately. Contact prescribing physician to switch to Vancomycin or Teicoplanin. If Linezolid is mandatory, wash out SSRI and monitor for hyperthermia, tremor, hyperreflexia, and clonus."
        },
        {
            "id": "SBAR-006",
            "record_id": "HABIJABI-095",
            "condition": "Thrombotic Thrombocytopenic Purpura (TTP)",
            "situation": "Patient presenting with profound thrombocytopenia (platelets 12,000/uL), microangiopathic hemolytic anemia, and fluctuating confusion.",
            "background": "ADAMTS13 deficiency leading to ultra-large vWF multimer microvascular thrombosis.",
            "assessment": "Impending massive stroke or renal infarction. Transfusing platelets fuels the thrombi.",
            "recommendation": "STRICTLY FORBID platelet transfusion despite severe thrombocytopenia. Initiate emergent Therapeutic Plasma Exchange (TPE) with fresh frozen plasma. Administer systemic corticosteroids."
        }
    ]

    # Save JSONL
    sbar_jsonl = sbar_dir / "ward_sbar_handover_cards.jsonl"
    with sbar_jsonl.open("w", encoding="utf-8") as f:
        for card in high_acuity_cases:
            f.write(json.dumps(card, ensure_ascii=False) + "\n")

    # Save Markdown Reference
    sbar_md = sbar_dir / "ward_sbar_handover_cards.md"
    with sbar_md.open("w", encoding="utf-8") as f:
        f.write("# Acute Inpatient SBAR Handover Cards (Habijabi Ward Protocols)\n\n")
        f.write("Rapid, standardized Situation-Background-Assessment-Recommendation on-call handover protocols for night-duty registrars and medical officers.\n\n")
        f.write("---\n\n")

        for card in high_acuity_cases:
            f.write(f"### 🚨 [{card['id']}] {card['condition']} ([{card['record_id']}]({_md_uri(card['record_id'])}))\n\n")
            f.write(f"**S — Situation**:\n{card['situation']}\n\n")
            f.write(f"**B — Background**:\n{card['background']}\n\n")
            f.write(f"**A — Assessment**:\n{card['assessment']}\n\n")
            f.write(f"**R — Recommendation**:\n{card['recommendation']}\n\n")
            f.write("---\n\n")

    print(f"  ✅ Built {len(high_acuity_cases)} acute SBAR handover protocols in {sbar_md}")

# ==============================================================================
# MODALITY 5: PATIENT-FACING HEALTH LITERACY & FOLK COUNSELING LEAFLETS (বাংলা)
# ==============================================================================
def build_modality_5_patient_leaflets():
    print("🗣️ [5/7] Building Patient-Facing Health Literacy & Folk Counseling Leaflets (বাংলা)...")
    leaflets_dir = EXPORTS_DIR / "PATIENT_LEAFLETS"
    leaflets_dir.mkdir(parents=True, exist_ok=True)

    leaflets = [
        {
            "id": "LEAFLET-BN-001",
            "topic": "ডায়াবেটিস কী এবং কেন ঘন ঘন প্রস্রাব হয়? (রাজা বকুলের গল্প)",
            "allegory_id": "ANA-003",
            "record_id": "HABIJABI-066",
            "target_patient": "নতুন শনাক্ত হওয়া ডায়াবেটিস রোগী ও তাদের পরিবার",
            "bengali_content": (
                "### ডায়াবেটিস কী এবং কেন ঘন ঘন প্রস্রাব হয়?\n"
                "**সহজ ভাষায় রোগীর জন্য পরামর্শ পত্র**\n\n"
                "অনেকেই ভাবেন, ডায়াবেটিস হলে শুধু রক্তে চিনি বাড়ে, এর বেশি কিছু নয়। কিন্তু শরীরে আসলে কী ঘটে?\n\n"
                "**রাজা বকুলের গল্প:**\n"
                "অনেক দিন আগের কথা। কুল বংশের রাজা বকুল হঠাৎ দেখলেন রাতে তিনি ঘুমাতে পারছেন না। ঘন ঘন প্রস্রাবের বেগ হয়, "
                "প্রচণ্ড পানির তৃষ্ণা পায়, আর সকালে উঠে দেখা যায় প্রস্রাবের জায়গায় পিঁপড়া জটলা পাকিয়ে আছে!\n\n"
                "**শরীরের ভেতরে কী হচ্ছে?**\n"
                "আমরা যখন খাবার খাই, খাবার ভেঙে রক্তে গ্লুকোজ (চিনি) তৈরি হয়। ইনসুলিন নামের হরমোন এই চিনিকে রক্ত থেকে কোষে পৌঁছে দেয় যাতে শরীর শক্তি পায়। "
                "কিন্তু ডায়াবেটিসে ইনসুলিন কাজ না করায় রক্তে চিনির মাত্রা উপচে পড়ে।\n\n"
                "কিডনি তখন বাধ্য হয়ে অতিরিক্ত চিনি প্রস্রাবের সাথে বের করে দিতে থাকে। চিনি একলা যায় না—চিনি স্পঞ্জের মতো শরীর থেকে প্রচুর পানি টেনে বের করে নিয়ে যায়। "
                "এজন্যই প্রচুর প্রস্রাব হয়, শরীর পানিশূন্য হয়ে প্রচণ্ড পানির তৃষ্ণা লাগে।\n\n"
                "**আপনার করণীয়:**\n"
                "১. মিষ্টি বা চিনিযুক্ত খাবার ও কোমল পানীয় সম্পূর্ণ পরিহার করুন।\n"
                "২. ডাক্তারের পরামর্শ ছাড়া কখনোই ডায়াবেটিসের ওষুধ বা ইনসুলিন বন্ধ করবেন না।\n"
                "৩. রাতে বারবার প্রস্রাব বা পিপাসা লাগলে ভয় না পেয়ে দ্রুত রক্তের সুগার মেপে চিকিৎসকের পরামর্শ নিন।"
            )
        },
        {
            "id": "LEAFLET-BN-002",
            "topic": "প্রেসারের ওষুধ কেন নিয়ম করে খাবেন? (পুরান ঢাকার বিয়ের দাওয়াত)",
            "allegory_id": "ANA-004",
            "record_id": "HABIJABI-070",
            "target_patient": "উচ্চ রক্তচাপের রোগী যারা সুস্থ বোধ করলেই ওষুধ খাওয়া বন্ধ করে দেন",
            "bengali_content": (
                "### প্রেসারের ওষুধ কেন নিয়ম করে খাবেন?\n"
                "**সহজ ভাষায় রোগীর জন্য পরামর্শ পত্র**\n\n"
                "অনেকে মনে করেন, 'মাথা ব্যথা নেই, শরীর ভালো লাগছে, তাই আজকে প্রেসারের ওষুধ খাওয়ার দরকার নেই।' এটা মারাত্মক ভুল ধারণা।\n\n"
                "**পুরান ঢাকার বিয়ের দাওয়াতের উদাহরণ:**\n"
                "কল্পনা করুন, পুরান ঢাকার এক সরু গলিতে এক বিশাল বিয়ের দাওয়াত। হাজার হাজার মেহমান একসাথে সরু গেট দিয়ে ঢোকার চেষ্টা করছে। "
                "গেট যদি চেপে রাখা হয়, গেটের ওপর প্রচণ্ড চাপ পড়ে এবং মানুষ পদদলিত হওয়ার ঝুঁকি তৈরি হয়।\n\n"
                "আমাদের রক্তনালীগুলো হলো সেই সরু গলি, আর হৃদপিণ্ড হলো পাম্প। প্রেসারের ওষুধ রক্তনালীর সেই সরু গেটগুলোকে আলগা বা চওড়া করে দেয়, "
                "যাতে রক্ত সহজে চলাচল করতে পারে এবং হার্ট ও মস্তিষ্কের ওপর অহেতুক চাপ না পড়ে।\n\n"
                "আপনি যেদিন ওষুধ বন্ধ করেন, রক্তনালী আবার চেপে যায়। কোনো লক্ষণ না থাকলেও নিঃশব্দে কিডনি নষ্ট হতে পারে বা মস্তিষ্কে রক্তক্ষরণ (ব্রেন স্ট্রোক) হতে পারে।\n\n"
                "**আপনার করণীয়:**\n"
                "১. প্রেসারের ওষুধ কোনো লক্ষণ বা কষ্টের ওষুধ নয়—এটি ব্রেন স্ট্রোক ও হার্ট অ্যাটাক প্রতিরোধের রক্ষাকবচ।\n"
                "২. সুস্থ বোধ করলেও প্রতিদিন নির্দিষ্ট সময়ে প্রেসারের ওষুধ নিয়মিত খেয়ে যান।"
            )
        },
        {
            "id": "LEAFLET-BN-003",
            "topic": "থ্যালাসেমিয়া ক্যারিয়ার: আয়রন ক্যাপসুল কেন আপনার বিষ?",
            "allegory_id": "NONE",
            "record_id": "HABIJABI-022",
            "target_patient": "থ্যালাসেমিয়া ট্রেইট (বাহক) রোগী যাদের ভুল করে বারবার আয়রন সিরাপ/ক্যাপসুল দেওয়া হয়",
            "bengali_content": (
                "### থ্যালাসেমিয়া ক্যারিয়ার: আয়রন ক্যাপসুল কেন আপনার বিষ?\n"
                "**সহজ ভাষায় রোগীর জন্য পরামর্শ পত্র**\n\n"
                "রক্তে হিমোগ্লোবিন কম দেখলেই আমাদের দেশের সাধারণ মানুষ ফার্মেসিতে গিয়ে আয়রন ক্যাপসুল বা রক্ত তৈরির সিরাপ কিনে খান। এটা মারাত্মক ক্ষতির কারণ হতে পারে!\n\n"
                "**রক্তস্বল্পতা মানেই কি আয়রনের অভাব?**\n"
                "না! রক্তে লোহিত রক্তকণিকা ছোট হওয়ার (Microcytic) দুটি প্রধান কারণ থাকে:\n"
                "১. শরীরে আয়রনের সত্যিকারের ঘাটতি।\n"
                "২. জন্মগত রক্তের ত্রুটি বা থ্যালাসেমিয়া ট্রেইট (বাহক)।\n\n"
                "থ্যালাসেমিয়া বাহকদের শরীরে আয়রনের কোনো ঘাটতি থাকে না, বরং পর্যাপ্ত আয়রন থাকে। সমস্যা হলো হিমোগ্লোবিন তৈরির জেনেটিক চেইন দুর্বল।\n\n"
                "আপনি যদি থ্যালাসেমিয়া বাহক হয়ে চিকিৎসকের পরামর্শ ছাড়া দিনের পর দিন আয়রন খান, সেই অতিরিক্ত আয়রন আপনার লিভার (যকৃত) এবং হার্টে জমা হয়ে স্থায়ীভাবে অঙ্গগুলো বিকল করে দেয় (হিমোসিডারোসিস)।\n\n"
                "**আপনার করণীয়:**\n"
                "১. রক্তে হিমোগ্লোবিন কম হলে নিজে নিজে আয়রন খাবেন না।\n"
                "২. রক্তের সিরাম ফেরিটিন (Serum Ferritin) এবং হিমোগ্লোবিন ইলেক্ট্রোফোরেসিস পরীক্ষা করে নিশ্চিত হোন আপনি থ্যালাসেমিয়া বাহক কিনা।"
            )
        },
        {
            "id": "LEAFLET-BN-004",
            "topic": "তীব্র বাতের ব্যথায় কেন সাথে সাথে ইউরিক এসিড কমানোর ওষুধ খাবেন না?",
            "allegory_id": "NONE",
            "record_id": "HABIJABI-003",
            "target_patient": "তীব্র গেঁটে বাত (Gout) এ আক্রান্ত রোগী",
            "bengali_content": (
                "### তীব্র বাতের ব্যথায় কেন সাথে সাথে ইউরিক এসিড কমানোর ওষুধ খাবেন না?\n"
                "**সহজ ভাষায় রোগীর জন্য পরামর্শ পত্র**\n\n"
                "হঠাৎ রাতে পায়ের বুড়ো আঙুল বা হাঁটু ফুলে লাল হয়ে তীব্র ব্যথা শুরু হয়েছে? রক্ত পরীক্ষায় ইউরিক এসিড বেশি এসেছে?\n\n"
                "**সবচেয়ে বড় যে ভুলটি মানুষ করে:**\n"
                "ব্যথা শুরু হওয়ার সাথে সাথে অনেকেই ইউরিক এসিড কমানোর ওষুধ (যেমন: Allopurinol বা Febuxostat) খাওয়া শুরু করে দেন। এতে ব্যথা কমার বদলে কয়েকগুণ বেড়ে যায় এবং ব্যথা দীর্ঘস্থায়ী হয়!\n\n"
                "**কেন এমন হয়?**\n"
                "গাঁটের ভেতরে জমে থাকা ইউরিক এসিডের দানার ওপর শরীর এক ধরণের প্রতিরক্ষা স্তর তৈরি করে রাখে। "
                "তীব্র ব্যথার মুহূর্তে হঠাৎ ইউরিক এসিড কমানোর ওষুধ খেলে রক্তের ঘনত্ব দ্রুত ওঠানামা করে, ফলে জমে থাকা দানাগুলো ভেঙে গিয়ে নতুন করে মারাত্মক প্রদাহ তৈরি করে।\n\n"
                "**আপনার করণীয়:**\n"
                "১. তীব্র ব্যথার সময় শুধুমাত্র ডাক্তারের পরামর্শে প্রদাহ ও ব্যথা কমানোর ওষুধ (যেমন কলচিসিন বা এনএসএআইডি) খাবেন।\n"
                "২. ইউরিক এসিড কমানোর ওষুধ ব্যথা পুরোপুরি ভালো হওয়ার অন্তত ৪ থেকে ৬ সপ্তাহ পর শুরু করতে হয়।"
            )
        }
    ]

    master_md = leaflets_dir / "patient_counseling_leaflets_bengali.md"
    with master_md.open("w", encoding="utf-8") as f:
        f.write("# রোগীবান্ধব স্বাস্থ্য সচেতনতা ও পরামর্শ পত্র (HABIJABI Patient Leaflets)\n\n")
        f.write("ডাঃ কাওসার উদ্দীনের শিক্ষণীয় রূপক ও মেটাফোর থেকে প্রস্তুতকৃত সহজ বাংলা ভাষায় রোগী ও তাদের পরিবারের জন্য পরামর্শ নির্দেশিকা।\n\n")
        f.write("---\n\n")

        for l in leaflets:
            f.write(f"## [{l['id']}] {l['topic']}\n")
            f.write(f"- **উৎস কেস**: [`{l['record_id']}`]({_md_uri(l['record_id'])})\n")
            f.write(f"- **উদ্দিষ্ট ব্যক্তি**: {l['target_patient']}\n\n")
            f.write(f"{l['bengali_content']}\n\n")
            f.write("---\n\n")

    print(f"  ✅ Compiled {len(leaflets)} patient counseling leaflets in Bengali in {master_md}")

# ==============================================================================
# MODALITY 6: ANKI SPACED-REPETITION DECKS (.tsv WITH CLOZE DELETIONS)
# ==============================================================================
def build_modality_6_anki_deck(records: List[Dict[str, Any]], claims: List[Dict[str, str]], bridge_map: Dict[str, Dict[str, str]]):
    print("🃏 [6/7] Building High-Yield Anki Spaced-Repetition Cloze Decks (.tsv)...")
    anki_dir = EXPORTS_DIR / "ANKI"
    anki_dir.mkdir(parents=True, exist_ok=True)

    cards = []
    card_idx = 1

    # 1. From Claims
    for c in claims:
        cid = c.get("claim_id", "")
        rid = c.get("record_id", "")
        dis = c.get("disease", "").strip() or "General"
        dom = c.get("clinical_domain", "").strip()
        text = c.get("claim_text", "").strip()
        ctype = c.get("claim_type", "").strip()
        b_entry = bridge_map.get(rid, {})
        d_ref = b_entry.get("davidson_chapter_number", "Davidson 25th")

        # Create Cloze
        if ctype == "CONTRAINDICATION":
            cloze_text = f"In {dis}, the following clinical action is CONTRAINDICATED: {{{{c1::{text}}}}}"
        elif ctype == "MECHANISM":
            cloze_text = f"The underlying pathophysiological mechanism of {dis} is: {{{{c1::{text}}}}}"
        elif ctype in ["TREATMENT", "TREATMENT_PROTOCOL"]:
            cloze_text = f"The evidence-based clinical management for {dis} is: {{{{c1::{text}}}}}"
        else:
            cloze_text = f"Regarding {dis}: {{{{c1::{text}}}}}"

        extra = f"Source: {rid} | Claim: {cid} | Domain: {dom} | Reference: {d_ref}"
        tags = f"CDSS Habijabi {dom.replace(' ', '_').replace('/', '_')} {ctype}"

        cards.append({
            "card_id": f"ANKI-HABIJABI-{card_idx:04d}",
            "text": cloze_text,
            "extra": extra,
            "tags": tags
        })
        card_idx += 1

    # 2. Key High-Yield Numerical & Pharmacological Flashcards
    high_yield_specifics = [
        (
            "In Familial Glucocorticoid Remediable Aldosteronism (GRA), severe refractory hypertension is paradoxically cured by administering {{c1::low-dose dexamethasone / glucocorticoids}}, which acts by suppressing {{c2::pituitary ACTH}} secretion.",
            "HABIJABI-001 | Endocrinology / Genetics | Davidson Ch20",
            "CDSS Habijabi Endocrinology Genetics GRA"
        ),
        (
            "In bilateral Renal Artery Stenosis, administering an ACE inhibitor or ARB blunts {{c1::efferent arteriolar vasoconstriction}}, precipitating {{c2::acute intraglomerular pressure collapse and severe renal decline}}.",
            "HABIJABI-001 | Nephrology / Pharmacology | Davidson Ch18",
            "CDSS Habijabi Nephrology ACEi Renal_Artery_Stenosis"
        ),
        (
            "Myotonic Dystrophy Type 1 is caused by an unstable {{c1::CTG}} triplet repeat expansion in the {{c2::DMPK}} gene located on chromosome {{c3::19q13.3}}.",
            "HABIJABI-002 | Neurology / Medical Genetics | Davidson Ch26",
            "CDSS Habijabi Neurology Genetics Triplet_Repeats"
        ),
        (
            "Urate-lowering therapy (Allopurinol or Febuxostat) should {{c1::NOT be initiated}} during an acute attack of gout, and should be delayed until {{c2::4 to 6 weeks}} post-resolution.",
            "HABIJABI-003 | Rheumatology / Therapeutics | Davidson Ch25",
            "CDSS Habijabi Rheumatology Gout Allopurinol"
        ),
        (
            "In the first trimester of pregnancy, {{c1::Propylthiouracil (PTU)}} is preferred over Carbimazole because Carbimazole carries a higher risk of embryopathies, specifically {{c2::choanal atresia}} and {{c3::aplasia cutis}}.",
            "HABIJABI-005 | Obstetrics / Endocrinology | Davidson Ch30",
            "CDSS Habijabi Endocrinology Obstetrics Teratogenicity"
        ),
        (
            "Radioactive iodine (I-131) is strictly {{c1::contraindicated}} in pregnancy because it freely crosses the placenta and causes permanent {{c2::fetal thyroid destruction / congenital hypothyroidism}}.",
            "HABIJABI-005 | Obstetrics / Nuclear Medicine | Davidson Ch30",
            "CDSS Habijabi Endocrinology Pregnancy I131"
        ),
        (
            "For adult dengue fluid resuscitation during the plasma leakage phase using standard IV giving sets (20 drops/mL), the bedside drop calculation formula is: {{c1::drops/minute = mL/hour ÷ 3}}.",
            "HABIJABI-013 | Emergency Medicine / Fluid Arithmetic | Davidson Ch02",
            "CDSS Habijabi Critical_Care Dengue Drop_Factor"
        ),
        (
            "Liddle's syndrome is an autosomal dominant channelopathy characterized by constitutive activation of the {{c1::ENaC (epithelial sodium channel)}} in the cortical collecting duct, which is treated definitively with {{c2::amiloride or triamterene}} (Spironolactone is {{c3::ineffective}}).",
            "HABIJABI-015 | Nephrology / Genetics | Davidson Ch18",
            "CDSS Habijabi Nephrology Liddles ENaC"
        ),
        (
            "In microcytic anemia, a Mentzer index (MCV ÷ RBC count) of {{c1::< 13}} strongly suggests {{c2::Thalassemia Trait}}, in which empirical iron administration is strictly contraindicated.",
            "HABIJABI-022 | Haematology / Laboratory Diagnostics | Davidson Ch24",
            "CDSS Habijabi Haematology Mentzer Thalassemia"
        ),
        (
            "Co-administration of IV or oral Linezolid with SSRIs or SNRIs precipitates fatal {{c1::Serotonin Syndrome}} due to non-selective {{c2::monoamine oxidase (MAO) inhibition}} by Linezolid.",
            "HABIJABI-086 | Pharmacology / Infectious Disease | Davidson Ch09",
            "CDSS Habijabi Pharmacology Linezolid Serotonin_Syndrome"
        ),
        (
            "In Thrombotic Thrombocytopenic Purpura (TTP), platelet transfusion is strictly {{c1::contraindicated}} because it fuels {{c2::microvascular thrombosis}}, leading to acute stroke and renal infarction.",
            "HABIJABI-095 | Haematology / Critical Care | Davidson Ch24",
            "CDSS Habijabi Haematology TTP Platelet_Transfusion"
        )
    ]

    for cloze, ext, tgs in high_yield_specifics:
        cards.append({
            "card_id": f"ANKI-HABIJABI-{card_idx:04d}",
            "text": cloze,
            "extra": ext,
            "tags": tgs
        })
        card_idx += 1

    # Save TSV
    deck_tsv = anki_dir / "habijabi_high_yield_anki_deck.tsv"
    with deck_tsv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["#Card_ID", "Text_Cloze", "Extra_Notes_and_Source", "Tags"])
        for c in cards:
            w.writerow([c["card_id"], c["text"], c["extra"], c["tags"]])

    print(f"  ✅ Compiled {len(cards)} high-yield cloze deletion flashcards in {deck_tsv}")

# ==============================================================================
# MODALITY 7: WARD PHARMACOVIGILANCE & "NEVER-EVENTS" TOXIC DRUG MATRIX
# ==============================================================================
def build_modality_7_pharmacovigilance(claims: List[Dict[str, str]]):
    print("⚠️ [7/7] Building Ward Pharmacovigilance & 'Never-Events' Toxic Drug Matrix...")
    pharma_dir = EXPORTS_DIR / "PHARMACOVIGILANCE"
    pharma_dir.mkdir(parents=True, exist_ok=True)

    matrix_rows = [
        {
            "id": "SAFETY-001",
            "record_id": "HABIJABI-001",
            "prescribed_agent": "ACE Inhibitors / ARBs (e.g. Enalapril, Ramipril, Losartan)",
            "forbidden_clinical_context": "Bilateral Renal Artery Stenosis (or solitary kidney RAS)",
            "lethal_adverse_consequence": "Acute GFR shutdown, anuric renal failure, severe refractory hyperkalemia",
            "underlying_pathophysiology": "Angiotensin II maintains efferent arteriolar tone to preserve glomerular filtration pressure; ACEi removes this defense mechanism, causing intraglomerular pressure collapse.",
            "safe_clinical_alternative": "Calcium Channel Blockers (Amlodipine), Alpha-blockers; revascularization workup."
        },
        {
            "id": "SAFETY-002",
            "record_id": "HABIJABI-003",
            "prescribed_agent": "Urate-Lowering Therapy (Allopurinol, Febuxostat)",
            "forbidden_clinical_context": "Acute Gouty Arthritis Flare",
            "lethal_adverse_consequence": "Severe exacerbation and prolongation of acute synovitis",
            "underlying_pathophysiology": "Sudden fluctuations in serum uric acid destabilize synovial microtophi, releasing inflammatory crystals into synovial fluid.",
            "safe_clinical_alternative": "Colchicine (0.5 mg BD/TDS) or NSAIDs with PPI; defer ULT initiation for 4-6 weeks post flare resolution."
        },
        {
            "id": "SAFETY-003",
            "record_id": "HABIJABI-005",
            "prescribed_agent": "Carbimazole / Methimazole",
            "forbidden_clinical_context": "First Trimester of Pregnancy (Weeks 1-12)",
            "lethal_adverse_consequence": "Major Congenital Malformations (Carbimazole Embryopathy)",
            "underlying_pathophysiology": "Teratogenic disruption of cranial ectoderm and branchial arches causing aplasia cutis congenita, choanal atresia, and tracheoesophageal fistula.",
            "safe_clinical_alternative": "Propylthiouracil (PTU) during 1st trimester; may switch back to Carbimazole in 2nd/3rd trimester."
        },
        {
            "id": "SAFETY-004",
            "record_id": "HABIJABI-005",
            "prescribed_agent": "Radioactive Iodine (I-131)",
            "forbidden_clinical_context": "Pregnancy and Breastfeeding",
            "lethal_adverse_consequence": "Permanent fetal/infant thyroid ablation, congenital cretinism, intellectual disability",
            "underlying_pathophysiology": "Beta emissions destroy fetal thyroid tissue; radioactive isotope is concentrated and secreted in breast milk.",
            "safe_clinical_alternative": "Antithyroid drugs (PTU) or second-trimester subtotal thyroidectomy if medically refractory."
        },
        {
            "id": "SAFETY-005",
            "record_id": "HABIJABI-012",
            "prescribed_agent": "Blind Rapid IV Crystalloid Boluses (Normal Saline / Ringer's Lactate)",
            "forbidden_clinical_context": "Dengue Plasma Leakage Phase without dynamic hematocrit titration",
            "lethal_adverse_consequence": "Iatrogenic pulmonary edema, massive pleural effusion, refractory respiratory failure",
            "underlying_pathophysiology": "Endothelial gap widening allows rapid fluid shifts into interstitial spaces; volume overload occurs before capillary seal recovers.",
            "safe_clinical_alternative": "Maintenance + 5% Deficit fluid protocol titrated strictly to target urine output >= 0.5 mL/kg/hr."
        },
        {
            "id": "SAFETY-006",
            "record_id": "HABIJABI-016",
            "prescribed_agent": "High-Dose Preformed Vitamin A (Retinol > 10,000 IU/day)",
            "forbidden_clinical_context": "First Trimester of Pregnancy (Organogenesis)",
            "lethal_adverse_consequence": "Craniofacial, cardiac, and central nervous system congenital defects",
            "underlying_pathophysiology": "Excess retinoic acid disrupts homeobox (HOX) gene expression and neural crest cell migration.",
            "safe_clinical_alternative": "Dietary provitamin A (Beta-carotene) which is non-teratogenic."
        },
        {
            "id": "SAFETY-007",
            "record_id": "HABIJABI-022",
            "prescribed_agent": "Empirical Oral / IV Iron Therapy (Ferrous Sulfate, Iron Sucrose)",
            "forbidden_clinical_context": "Microcytic Anemia with Mentzer Index < 13 (Thalassemia Trait)",
            "lethal_adverse_consequence": "Secondary systemic hemosiderosis, hepatic cirrhosis, bronze diabetes, cardiomyopathy",
            "underlying_pathophysiology": "Intact or elevated iron stores cannot be utilized due to globin chain deficiency; extra iron deposits in reticuloendothelial parenchymal organs.",
            "safe_clinical_alternative": "Serum Ferritin & Hb-electrophoresis confirmation; genetic counseling; folic acid supplementation."
        },
        {
            "id": "SAFETY-008",
            "record_id": "HABIJABI-086",
            "prescribed_agent": "Linezolid (Oxazolidinone Antibiotic)",
            "forbidden_clinical_context": "Concomitant SSRIs / SNRIs / Tricyclics (e.g. Escitalopram, Fluoxetine, Sertraline)",
            "lethal_adverse_consequence": "Lethal Serotonin Syndrome (Hyperthermia, autonomic storm, myoclonus, seizures)",
            "underlying_pathophysiology": "Linezolid is a reversible, non-selective MAO-A inhibitor; blocking MAO combined with reuptake inhibition leads to massive synaptic serotonin accumulation.",
            "safe_clinical_alternative": "Vancomycin, Teicoplanin, Daptomycin; or mandatory 2-week washout of SSRI prior to linezolid."
        },
        {
            "id": "SAFETY-009",
            "record_id": "HABIJABI-095",
            "prescribed_agent": "Platelet Transfusion",
            "forbidden_clinical_context": "Thrombotic Thrombocytopenic Purpura (TTP)",
            "lethal_adverse_consequence": "Acute widespread microvascular thrombosis, cerebral infarction (stroke), sudden death",
            "underlying_pathophysiology": "Infused platelets bind to circulating ultra-large von Willebrand factor multimers, fueling microthrombotic occlusion.",
            "safe_clinical_alternative": "Therapeutic Plasma Exchange (TPE) with FFP; systemic corticosteroids; Caplacizumab; Rituximab."
        },
        {
            "id": "SAFETY-010",
            "record_id": "HABIJABI-126",
            "prescribed_agent": "Systemic Corticosteroids (Dexamethasone / Methylprednisolone)",
            "forbidden_clinical_context": "Mild Non-Hypoxemic Viral Infections (SpO2 > 94% on room air)",
            "lethal_adverse_consequence": "Delayed viral clearance, secondary bacterial sepsis, invasive fungal infections (mucormycosis)",
            "underlying_pathophysiology": "Suppression of innate interferon pathways without clinical benefit in the absence of systemic hyperinflammatory hypoxemia.",
            "safe_clinical_alternative": "Supportive care, hydration, antipyretics; restrict steroids strictly to hypoxemic patients requiring supplemental oxygen."
        }
    ]

    # Save CSV
    matrix_csv = pharma_dir / "never_events_toxic_drug_matrix.csv"
    with matrix_csv.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "id", "record_id", "prescribed_agent", "forbidden_clinical_context",
            "lethal_adverse_consequence", "underlying_pathophysiology", "safe_clinical_alternative"
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(matrix_rows)

    # Save Markdown
    matrix_md = pharma_dir / "never_events_toxic_drug_matrix.md"
    with matrix_md.open("w", encoding="utf-8") as f:
        f.write("# Ward Pharmacovigilance & 'Never-Events' Toxic Drug Matrix\n\n")
        f.write("A master clinical reference documenting lethal prescribing traps, biochemical mechanisms of toxicity, and evidence-based alternatives derived from Dr. Kawsar Uddin's teachings.\n\n")
        f.write("---\n\n")
        f.write("| ID | Prescribed Agent | Forbidden Context | Adverse Consequence | Safe Clinical Alternative |\n")
        f.write("|---|---|---|---|---|\n")
        for m in matrix_rows:
            f.write(f"| **{m['id']}** | `{m['prescribed_agent']}` | **{m['forbidden_clinical_context']}** | {m['lethal_adverse_consequence']} | {m['safe_clinical_alternative']} |\n")
        f.write("\n---\n\n")

        for m in matrix_rows:
            f.write(f"### 🛑 [{m['id']}] {m['prescribed_agent']} in {m['forbidden_clinical_context']} ([{m['record_id']}]({_md_uri(m['record_id'])}))\n\n")
            f.write(f"- **Consequence**: {m['lethal_adverse_consequence']}\n")
            f.write(f"- **Mechanism**: {m['underlying_pathophysiology']}\n")
            f.write(f"- **Safe Alternative**: {m['safe_clinical_alternative']}\n\n")

    print(f"  ✅ Built {len(matrix_rows)} toxic drug never-events in {matrix_md}")

# ==============================================================================
# MASTER RUNNER
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Generate 7 Extended Clinical & Educational Modalities")
    parser.add_argument("--workspace", type=str, default=r"D:\HABIJABI_FULL", help="Target corpus workspace root")
    args = parser.parse_args()

    ws = Path(args.workspace)
    configure_workspace(ws)

    print("=" * 80)
    print("🚀 MANUFACTURING 7 EXTENDED CLINICAL & EDUCATIONAL MODALITIES")
    print(f"   Corpus Target: {CORPUS_ROOT}")
    print("=" * 80)

    claims = load_claims()
    records = load_english_synthesis_records()
    bridge_map = load_bridge()

    print(f"Loaded: {len(claims)} claims, {len(records)} English synthesis records, {len(bridge_map)} bridge links.\n")

    build_modality_1_visual_spotters(records, claims)
    build_modality_2_curriculum(records, bridge_map)
    build_modality_3_causal_graph(records, claims)
    build_modality_4_sbar_handovers(records)
    build_modality_5_patient_leaflets()
    build_modality_6_anki_deck(records, claims, bridge_map)
    build_modality_7_pharmacovigilance(claims)

    print("\n" + "=" * 80)
    print("🎉 ALL 7 EXTENDED MODALITIES SUCCESSFULLY MANUFACTURED!")
    print("=" * 80)

if __name__ == "__main__":
    main()
