#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HABIJABI CDSS & Socratic Preceptor Navigator (v1.0.0)
Authoritative Offline Engine for Dr. Kawsar Uddin's Clinical Medical Series

Implements 6 Core Clinical & Educational Modalities:
1. Interactive Socratic Preceptor (--preceptor <case_or_query>)
2. Postgraduate Exam SBA Generator (--exam-sba [record_id|topic|random])
3. Bedside Prescribing Safety Interceptor (--prescribing-safety <drug_or_condition>)
4. Federated 4-Textbook Grounding (--federated <topic>)
5. Tropical / Resource-Constrained Ward Companion (--tropical-calc <type> | --ward-facilities <test>)
6. Hybrid Bilingual Semantic Search Engine (--search <query> [--lang bn|en|any])
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

if (getattr(sys.stdout, "encoding", None) or "").lower() != "utf-8" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CORPUS_ROOT = Path(os.environ.get("CDSS_HABIJABI_ROOT", r"D:\HABIJABI_FULL"))
CONTROL_DIR = CORPUS_ROOT / "00_CONTROL"
NORMALIZED_DIR = CORPUS_ROOT / "03_NORMALIZED_CORPUS"
PERSONA_DIR = CORPUS_ROOT / "04_KAWSAR_PERSONA"
BRIDGE_DIR = CORPUS_ROOT / "05_DAVIDSON_BRIDGE"
EXPORTS_DIR = CORPUS_ROOT / "08_EXPORTS"

# ------------------------------------------------------------------------------
# Matching helpers. The old code used `any(term in text for term in query.split())`: no stop-words, no
# word boundaries, and a silent fall-back to record 0. "a" matched every vignette and "iron" matched
# "environment". Everything below is whole-word, stop-word-filtered, and never falls back silently.
# ------------------------------------------------------------------------------
_STOP = frozenset("a an the of in on at to for with by from as and or is are was were be been it its this that these those "
                  "management case patient pt has have had having plus start give given".split())
_WORD_RE = re.compile(r"[\w\u0980-\u09FF\u200c\u200d]+")


def query_terms(text: str) -> List[str]:
    """Lower-cased whole-word terms (Bengali vowel signs kept attached), minus stop-words; 2+ chars so TB/DM/MI survive."""
    return [t for t in (w.lower() for w in _WORD_RE.findall(text or "")) if len(t) >= 2 and t not in _STOP]


def _has(text: str, term: str) -> bool:
    """Whole-word / whole-phrase presence test (case-insensitive)."""
    pat = r"(?<![\w])" + r"\s+".join(re.escape(w) for w in term.split()) + r"(?![\w])"
    return re.search(pat, text, re.I) is not None


def _best_match(query: str, items: List[Dict[str, Any]], text_of) -> Optional[Dict[str, Any]]:
    """Item whose text shares the most whole-word terms with the query; None if nothing overlaps."""
    terms = set(query_terms(query))
    best, best_score = None, 0
    for it in items:
        words = set(query_terms(text_of(it)))
        score = len(terms & words)
        if score > best_score:
            best, best_score = it, score
    return best


def load_claims() -> List[Dict[str, str]]:
    claims_csv = NORMALIZED_DIR / "TABLES" / "clinical_claims.csv"
    if not claims_csv.exists():
        return []
    with claims_csv.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def load_bridge() -> List[Dict[str, str]]:
    bridge_csv = BRIDGE_DIR / "BRIDGE_TABLES" / "davidson_bridge_registry.csv"
    if not bridge_csv.exists():
        return []
    with bridge_csv.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def load_filtered_comments() -> List[Dict[str, str]]:
    c_csv = NORMALIZED_DIR / "TABLES" / "clinical_comments_filtered.csv"
    if not c_csv.exists():
        return []
    with c_csv.open("r", encoding="utf-8") as f:
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

# ==============================================================================
# 1. INTERACTIVE SOCRATIC PRECEPTOR
# ==============================================================================
def run_preceptor(query: str):
    print("=" * 80)
    print("🩺 DR. KAWSAR UDDIN VIRTUAL PRECEPTOR — MORNING REPORT / WARD PRECEPTORSHIP")
    print("=" * 80)
    print(f"CASE PRESENTATION / QUERY: \"{query}\"\n")

    records = load_english_synthesis_records()
    if not records:
        print("NO CORPUS: no synthesis records could be loaded (check CDSS_HABIJABI_ROOT). Nothing was evaluated.")
        return 2
    matched = _best_match(query, records,
                          lambda r: f"{r.get('primary_condition','')} {r.get('title','')} {r.get('vignette','')}")
    if matched is None:
        print("NO MATCHING RECORD: no whole-word overlap between the query and any Habijabi record. "
              "Not showing an unrelated case.")
        return 2

    rid = matched["record_id"]
    print(f"📌 CLINICAL TOPIC ANCHOR: {matched['title']} (`{rid}`)")
    print(f"📁 DOMAIN: {matched['domain']}\n")

    print("--- 1. BEDSIDE CASE PRESENTATION ---")
    print(f"{matched['vignette']}\n")

    print("--- 2. PATHOPHYSIOLOGICAL MECHANISMS FIRST ---")
    print(f"{matched['pathophysiology']}\n")

    print("--- 3. SOCRATIC QUESTIONS FOR THE TRAINEE ---")
    if "hypertension" in matched["title"].lower():
        print("  Q1: Why does administering an ACE inhibitor in bilateral renal artery stenosis precipitate acute renal shutdown?")
        print("  Q2: If this young patient has low serum potassium, which zone of the adrenal cortex is hyperfunctioning, and what hormone controls it?")
    elif "dengue" in matched["title"].lower():
        print("  Q1: What is the primary cause of circulatory collapse in severe dengue—active hemorrhage or plasma leakage?")
        print("  Q2: How do you adjust the IV fluid drop rate based on hematocrit and urine output to avoid pulmonary edema?")
    elif "gout" in matched["title"].lower():
        print("  Q1: Why is it clinically dangerous to initiate allopurinol during an acute attack of gouty arthritis?")
        print("  Q2: What is the management rule for asymptomatic hyperuricemia with normal renal function?")
    else:
        print(f"  Q1: What underlying cellular or biochemical cascade explains this presentation in {matched['primary_condition']}?")
        print("  Q2: What anomalous laboratory finding would immediately redirect your differential diagnosis?")

    print("\n--- 4. COMMON PRESCRIBING TRAPS & COGNITIVE PITFALLS ---")
    print(f"⚠️  {matched['contraindications']}\n")

    print("--- 5. DR. KAWSAR'S CLINICAL HEURISTIC & BED-SIDE PEARL ---")
    print(f"💡 {matched['pearls']}\n")
    print(f"📖 Reference File: {CORPUS_ROOT / '03_NORMALIZED_CORPUS' / 'MARKDOWN' / (rid + '.md')}")
    print("=" * 80)
    return 0

# ==============================================================================
# 2. POSTGRADUATE EXAM SBA GENERATOR (FCPS / MRCP / MD)
# ==============================================================================
def run_exam_sba(target: Optional[str] = None):
    print("=" * 80)
    print("🎓 POSTGRADUATE CLINICAL MEDICINE EXAM ENGINE — SINGLE BEST ANSWER (SBA)")
    print("    Curriculum Standards: FCPS Part 1 / MRCP UK / MD Residency / BCS")
    print("=" * 80)

    sba_bank = {
        "HABIJABI-001": {
            "stem": "A 20-year-old male is evaluated for refractory severe hypertension (BP 195/115 mmHg) that has failed to respond to amlodipine 10 mg and ramipril 10 mg daily. His father also suffered from severe early-onset hypertension. Routine biochemistry reveals: Sodium 142 mmol/L, Potassium 2.9 mmol/L, Bicarbonate 31 mmol/L, Serum Creatinine 85 umol/L. Renal Doppler ultrasound is normal. Plasma aldosterone concentration is markedly elevated, and plasma renin activity is suppressed. Administration of low-dose dexamethasone results in complete normalization of aldosterone levels and blood pressure within 48 hours.",
            "question": "Which of the following is the most likely molecular mechanism underlying this patient's condition?",
            "options": [
                "A. Activating mutation in the mineralocorticoid receptor gene",
                "B. Chimeric gene resulting from unequal crossing over between CYP11B1 and CYP11B2",
                "C. Gain-of-function mutation in the epithelial sodium channel (ENaC)",
                "D. Paraganglioma hypersecreting norepinephrine in the organ of Zuckerkandl",
                "E. Loss-of-function mutation in 11-beta-hydroxysteroid dehydrogenase type 2"
            ],
            "key": "B",
            "explanation": "This patient has Familial Glucocorticoid Remediable Aldosteronism (GRA, or Familial Hyperaldosteronism Type 1). It is an autosomal dominant condition caused by an unequal crossover between the promoter region of 11-beta-hydroxylase (CYP11B1, ACTH-responsive) and the coding region of aldosterone synthase (CYP11B2). Consequently, aldosterone is ectopically produced in the zona fasciculata under the regulation of ACTH, resulting in early-onset severe hypertension and hypokalemia. Dexamethasone suppresses ACTH secretion, reversing the hyperaldosteronism.\n\nOption A describes pseudohypoaldosteronism type 2 or Geller syndrome. Option C describes Liddle's syndrome (characterized by low renin AND low aldosterone). Option E describes Apparent Mineralocorticoid Excess (AME).",
            "citation": "Habijabi-001 | Davidson's Principles and Practice of Medicine 25th Ed, Chapter 18 (Nephrology & Urology), Secondary Hypertension"
        },
        "HABIJABI-003": {
            "stem": "A 54-year-old male with chronic hypertension and obesity presents with sudden, excruciating pain, erythema, and marked swelling of the right first metatarsophalangeal joint that began 8 hours ago. Polarized light microscopy of synovial fluid confirms negatively birefringent needle-shaped crystals. Serum uric acid obtained in the ED is 5.8 mg/dL (345 umol/L). He is currently not taking any urate-lowering drugs.",
            "question": "Which of the following is the most appropriate initial pharmacological management?",
            "options": [
                "A. Initiate Allopurinol 100 mg daily immediately",
                "B. Initiate Febuxostat 40 mg daily immediately",
                "C. Prescribe Colchicine or oral Prednisolone; delay urate-lowering therapy until flare resolution",
                "D. Administer intravenous Rasburicase immediately",
                "E. Reassure the patient that gout is excluded due to the normal serum uric acid level"
            ],
            "key": "C",
            "explanation": "During an acute flare of gouty arthritis, management focuses on rapid anti-inflammatory relief using colchicine, NSAIDs, or oral corticosteroids. Urate-lowering therapy (ULT such as Allopurinol or Febuxostat) should NOT be initiated during an acute attack because rapid changes in serum urate levels destabilize crystal deposits in the joint, precipitating prolonged or recurrent arthritis. Initiation of ULT should be delayed until the acute flare has fully resolved (~4-6 weeks).\n\nSerum uric acid levels frequently fall into the normal range during acute attacks due to inflammatory cytokines promoting renal uricosuria (Option E is wrong). Options A and B violate the acute flare contraindication rule.",
            "citation": "Habijabi-003 | Davidson's Principles and Practice of Medicine 25th Ed, Chapter 25 (Rheumatology), Crystal Arthropathies"
        },
        "HABIJABI-005": {
            "stem": "A 24-year-old primigravida at 8 weeks of gestation presents with heat intolerance, tremor, persistent tachycardia (pulse 114 bpm), and modest diffuse thyromegaly. Laboratory testing confirms primary thyrotoxicosis: TSH < 0.01 mIU/L, Free T4 34 pmol/L (normal 10-22 pmol/L). TSH-receptor antibodies (TRAb) are strongly positive.",
            "question": "Which of the following therapeutic regimens is the most appropriate first-line antithyroid drug therapy?",
            "options": [
                "A. Carbimazole 20 mg daily throughout the entire pregnancy",
                "B. Radioactive Iodine (I-131) ablation",
                "C. Propylthiouracil (PTU) for the first trimester, switching to Carbimazole in the second trimester",
                "D. High-dose Lugol's iodine monotherapy",
                "E. Immediate total thyroidectomy under general anesthesia"
            ],
            "key": "C",
            "explanation": "In pregnancy-associated Graves' disease, Propylthiouracil (PTU) is preferred during the first trimester (weeks 1-12) because Carbimazole/Methimazole is associated with a distinct teratogenic embryopathy (choanal atresia, aplasia cutis congenita, and esophageal atresia) during embryogenesis. However, because PTU carries a cumulative risk of maternal fulminant hepatotoxicity, current international guidelines recommend switching back to Carbimazole/Methimazole starting in the second trimester.\n\nOption B (Radioactive Iodine) is strictly contraindicated in pregnancy due to immediate destruction of the fetal thyroid gland.",
            "citation": "Habijabi-005 | Davidson's Principles and Practice of Medicine 25th Ed, Chapter 30 (Maternal Medicine), Thyroid Disease in Pregnancy"
        },
        "HABIJABI-012": {
            "stem": "A 28-year-old female weighing 50 kg presents on Day 5 of fever with defervescence, severe abdominal pain, persistent vomiting, and lethargy. Examination reveals cold clammy extremities, blood pressure 90/70 mmHg, pulse 118 bpm, and tender hepatomegaly. CBC reveals hematocrit (HCT) 52% (baseline 36%) and platelet count 24,000/uL. Dengue NS1 antigen is positive.",
            "question": "According to national and WHO dengue fluid resuscitation guidelines, what is the initial fluid management strategy?",
            "options": [
                "A. Rapid bolus of 3 liters of normal saline over 1 hour",
                "B. Fluid restriction to 500 mL/day to prevent third-space pleural effusion",
                "C. Immediate transfusion of 4 units of random donor platelets before fluid resuscitation",
                "D. Isotonic crystalloid calculated as maintenance plus 5% deficit, titrated dynamically to urine output >= 0.5 mL/kg/hr",
                "E. Intravenous furosemide 40 mg to accelerate renal clearance"
            ],
            "key": "D",
            "explanation": "This patient has Dengue Shock Syndrome characterized by plasma leakage (rising hematocrit > 20% above baseline, hemoconcentration, narrowing pulse pressure <= 20 mmHg). The cornerstone of treatment is calculated fluid therapy: Maintenance + 5% deficit using isotonic crystalloids (Normal Saline or Ringer's Lactate). Drop rates must be titrated step-by-step according to serial HCT and urine output (targeting 0.5-1.0 mL/kg/hr). Blind excessive fluid bolusing (Option A) causes fatal pulmonary edema during the recovery reabsorption phase. Platelet transfusion (Option C) does not reverse plasma leakage.",
            "citation": "Habijabi-012 | Davidson's Principles and Practice of Medicine 25th Ed, Chapter 14 (Infectious Disease), Arboviruses: Dengue Fever"
        }
    }

    if not target or target.lower() == "random":
        selected_id = random.choice(list(sba_bank.keys()))
    elif target.upper() in sba_bank:
        selected_id = target.upper()
    else:
        print(f"NO SBA ITEM for {target!r}. Only {len(sba_bank)} items exist: {', '.join(sorted(sba_bank))}. "
              f"(Topic lookup is not implemented; use an item id or 'random'.)")
        return 2

    item = sba_bank[selected_id]
    print(f"\n[SBA ITEM ID: {selected_id}]")
    print(f"CLINICAL SCENARIO:\n{item['stem']}\n")
    print(f"QUESTION:\n{item['question']}\n")
    print("OPTIONS:")
    for opt in item["options"]:
        print(f"  {opt}")
    print("\n" + "-" * 40)
    print(f"CORRECT ANSWER: [{item['key']}]")
    print("-" * 40)
    print(f"DETAILED CLINICAL RATIONALE:\n{item['explanation']}\n")
    print(f"AUTHORITATIVE DUAL CITATION:\n📖 {item['citation']}")
    print("=" * 80)
    return 0

# ==============================================================================
# 3. BEDSIDE PRESCRIBING SAFETY INTERCEPTOR
# ==============================================================================
def run_prescribing_safety(order: str):
    """Keyword screen against SIX fixed rules. It is NOT a drug-interaction checker and NEVER clears an order:
    when no rule matches the result is NOT_EVALUATED (exit 3), because 'no rule' is not 'safe'."""
    print("=" * 80)
    print("🛡️  BEDSIDE PRESCRIBING SAFETY & STEWARDSHIP INTERCEPTOR")
    print("=" * 80)
    print(f"PROPOSED CLINICAL PRESCRIPTION / ORDER: \"{order}\"\n")
    if not (order or "").strip():
        print("ERROR: empty order -- nothing was evaluated.")
        return 2

    has = lambda *terms: any(_has(order, t) for t in terms)   # noqa: E731
    serotonergic = ["ssri", "snri", "fluoxetine", "sertraline", "escitalopram", "duloxetine", "paroxetine", "citalopram",
                    "fluvoxamine", "venlafaxine", "desvenlafaxine", "amitriptyline", "nortriptyline", "tramadol", "tricyclic"]
    rules = [
        {
            "trigger": has("gout", "flare") and has("allopurinol", "febuxostat"),
            "status": "HARD_STOP_CONTRAINDICATION",
            "title": "Contraindicated Urate-Lowering Therapy During Acute Gout Flare",
            "harm": "Initiating xanthine oxidase inhibitors during an active flare causes rapid fluctuations in synovial fluid urate levels, destabilizing intra-articular microtophi and severely prolonging acute synovitis.",
            "action": "Delay Allopurinol/Febuxostat until ~4-6 weeks after the flare has completely resolved. Treat the acute flare with Colchicine, NSAIDs, or systemic Corticosteroids.",
            "citation": "CLM-HABIJABI-003-002 | Davidson 25th Ed, Ch 25"
        },
        {
            "trigger": has("dengue") and (has("bolus", "unrestricted", "rapid fluid") or re.search(r"\b3\s*lit(?:er|re)s?\b", order, re.I) is not None),
            "status": "WARNING_HIGH_RISK",
            "title": "Fluid Overload Risk in Critical Phase Dengue",
            "harm": "Indiscriminate rapid crystalloid bolusing during the endothelial plasma leakage phase leads to massive third-space extravasation, pleural effusion, and fatal pulmonary edema upon vascular reabsorption.",
            "action": "Enforce strict weight-based Maintenance + 5% deficit protocol. Titrate hourly infusion rates targeting urine output >= 0.5 mL/kg/hr.",
            "citation": "CLM-HABIJABI-012-001 | Bangladesh National Dengue Guidelines / Davidson Ch 14"
        },
        {
            "trigger": has("microcytic", "anemia", "anaemia") and has("iron") and not has("ferritin"),
            "status": "WARNING_SAFETY_CHECK",
            "title": "Unscreened Empirical Iron in Microcytic Anemia",
            "harm": "Prescribing empirical oral iron in patients with Thalassemia trait causes progressive iatrogenic hemosiderosis and organ iron overload without correcting the genetic globin synthesis defect.",
            "action": "Calculate Mentzer Index (MCV / RBC count). If < 13, perform Hemoglobin Electrophoresis and Serum Ferritin before initiating iron therapy.",
            "citation": "CLM-HABIJABI-022-001 | Davidson 25th Ed, Ch 24"
        },
        {
            "trigger": has("linezolid") and has(*serotonergic),
            "status": "HARD_STOP_CONTRAINDICATION",
            "title": "Severe Drug Interaction: Serotonin Syndrome",
            "harm": "Linezolid is a reversible non-selective monoamine oxidase inhibitor (MAOI). Co-administration with serotonergic agents causes severe accumulation of serotonin, precipitating hyperthermia, clonus, autonomic instability, and death.",
            "action": "Discontinue SSRI with appropriate washout period or switch antibiotic to Vancomycin, Teicoplanin, or Daptomycin for MRSA/VRE.",
            "citation": "CLM-HABIJABI-086-001 | Davidson 25th Ed, Ch 02"
        },
        {
            "trigger": has("ttp", "thrombotic thrombocytopenic") and has("platelet", "transfusion"),
            "status": "HARD_STOP_CONTRAINDICATION",
            "title": "Absolute Contraindication of Platelet Transfusion in TTP",
            "harm": "Transfusing platelets in TTP fuels disseminated microvascular thrombi by supplying substrate for ultralarge von Willebrand factor multimers, triggering acute stroke, myocardial infarction, and death.",
            "action": "Immediate Therapeutic Plasma Exchange (TPE) with fresh frozen plasma and systemic corticosteroids. Withhold platelets unless catastrophic life-threatening hemorrhage.",
            "citation": "CLM-HABIJABI-095-001 | Davidson 25th Ed, Ch 24"
        },
        {
            "trigger": has("covid", "viral") and has("dexamethasone", "steroid") and has("mild", "normal o2", "spo2 98", "no o2"),
            "status": "HARD_STOP_INAPPROPRIATE_THERAPY",
            "title": "Inappropriate Steroid Use in Mild Non-Hypoxemic Viral Infection",
            "harm": "Systemic corticosteroids administered during the early replication phase without hypoxemia blunt host innate antiviral immunity, increase viral replication, and fail to reduce mortality (RECOVERY trial).",
            "action": "Reserve systemic steroids strictly for hospitalized patients requiring supplemental oxygen or mechanical ventilation.",
            "citation": "CLM-HABIJABI-126-001 | RECOVERY Trial / Davidson 25th Ed, Ch 14"
        }
    ]

    fired = [r for r in rules if r["trigger"]]
    for r in fired:                       # ALL matching rules, not just the first
        print(f"🚨 INTERCEPT STATUS: [{r['status']}]")
        print(f"🛑 ALERT: {r['title']}\n")
        print(f"💥 MECHANISM OF HARM:\n{r['harm']}\n")
        print(f"✅ CORRECT CLINICAL ACTION:\n{r['action']}\n")
        print(f"📚 EVIDENCE CITATION: {r['citation']}\n")
    if fired:
        print("NOTE: keyword screen against 6 fixed rules only; absence of other alerts is NOT a safety clearance.")
        print("=" * 80)
        return 0

    print("⚠️  STATUS: [NOT_EVALUATED]")
    print("No rule matched this order. This is NOT a safety clearance: the screen covers only 6 fixed rules and")
    print("does not check doses, renal/hepatic function, allergies or general drug interactions. Use a full")
    print("prescribing reference / pharmacist review.")
    print("=" * 80)
    return 3

# ==============================================================================
# 4. FEDERATED GROUNDING (bridge lookup only)
# ==============================================================================
def run_federated(topic: str):
    """Habijabi -> Davidson bridge lookup. Harrison / Hurst / Kumar & Clark are NOT queried here (this tool has no
    access to those corpora); it says so and points at the real federation instead of printing generic text."""
    print("=" * 80)
    print("🌐 HABIJABI → DAVIDSON BRIDGE LOOKUP")
    print("=" * 80)
    print(f"QUERY / CLINICAL TOPIC: \"{topic}\"\n")

    bridge_rows = load_bridge()
    matched_bridge = _best_match(topic, bridge_rows,
                                 lambda b: f"{b.get('habijabi_topic','')} {b.get('davidson_chapter_title','')}")
    if matched_bridge is None:
        print("NO BRIDGE MATCH for this topic (whole-word match against Habijabi topics and Davidson chapter titles). "
              "Not showing an unrelated row.")
        return 2

    rid = matched_bridge["habijabi_record_id"]
    print(f"📌 HABIJABI CLINICAL ANCHOR: {matched_bridge['habijabi_topic']} (`{rid}`)")
    print(f"🔗 BRIDGE ID: `{matched_bridge['bridge_id']}` | RELATIONSHIP: `{matched_bridge['relationship_type']}`\n")
    print(f"1. 📘 DAVIDSON (25th Edition) [Chapter {matched_bridge['davidson_chapter_number']}: {matched_bridge['davidson_chapter_title']}]:")
    print(f"   Section: {matched_bridge['davidson_section_heading']}")
    print(f"   Bridge note: {matched_bridge['concordance_notes']}\n")
    print("2-4. HARRISON 22 / HURST'S THE HEART 15 / KUMAR & CLARK 11: NOT QUERIED by this tool.")
    print("     For retrieved evidence from all four textbooks run the unified orchestrator, e.g.:")
    print(f"       python medical-cdss-unified-orchestrator/scripts/unified_orchestrator.py --query \"{topic}\" --book all")
    print("=" * 80)
    return 0

# ==============================================================================
# 5. TROPICAL & RESOURCE-CONSTRAINED WARD COMPANION
# ==============================================================================
def maintenance_ml_per_24h(weight_kg: float) -> float:
    """Holliday-Segar: 100 mL/kg (<=10 kg); 1000 + 50/kg above 10 kg (<=20 kg); 1500 + 20/kg above 20 kg.
    Continuous at the band edges (the previous code jumped from 2000 mL at 20 kg to 1520 mL at 21 kg)."""
    if weight_kg <= 10:
        return weight_kg * 100
    if weight_kg <= 20:
        return 1000 + 50 * (weight_kg - 10)
    return 1500 + 20 * (weight_kg - 20)


def _arg(args: List[str], i: int, name: str, lo: float, hi: float) -> float:
    """Required, finite, plausible numeric argument -- never a silent default patient."""
    if len(args) <= i:
        raise ValueError(f"missing required input: {name}")
    try:
        v = float(args[i])
    except ValueError:
        raise ValueError(f"{name} must be a number, got {args[i]!r}")
    if v != v or v in (float("inf"), float("-inf")):
        raise ValueError(f"{name} must be a finite number")
    if not (lo <= v <= hi):
        raise ValueError(f"{name}={v:g} is outside the plausible range {lo:g}-{hi:g}")
    return v


def run_tropical_calc(calc_type: str, args: List[str]):
    print("=" * 80)
    print("🌴 TROPICAL & RESOURCE-CONSTRAINED WARD CALCULATOR")
    print("=" * 80)

    c_type = calc_type.lower()
    try:
        if "dengue" in c_type:
            weight = _arg(args, 0, "weight (kg)", 3, 200)
            maint_24 = maintenance_ml_per_24h(weight)
            deficit = weight * 50
            total_48 = (maint_24 * 2) + deficit
            hourly_rate = total_48 / 48
            drops_min = hourly_rate / 3  # 20 drops/mL giving set
            print(f"PATIENT WEIGHT: {weight:.1f} kg")
            print(f"1. 24-Hour Maintenance Fluid (Holliday-Segar): {maint_24:.0f} mL")
            print(f"2. 5% Dehydration Deficit: {deficit:.0f} mL")
            print(f"3. Total 48-Hour Fluid Quota: {total_48:.0f} mL")
            print(f"4. Base Infusion Rate: {hourly_rate:.1f} mL/hour")
            print(f"5. Standard Giving Set Rate (20 gtt/mL): {drops_min:.0f} drops/minute")
            print("\n⚠️  STATIC ESTIMATE ONLY -- not a prescription. Dengue fluid therapy must be titrated to haematocrit, vital signs and")
            print("    urine output (target >= 0.5 mL/kg/hr) per the current local/national protocol; reduce the rate if HCT falls or")
            print("    respiratory distress develops. This calculator has not been clinician-validated.")
        elif "drop" in c_type:
            ml_hr = _arg(args, 0, "rate (mL/hour)", 1, 2000)
            print(f"DESIRED INFUSION RATE: {ml_hr:.1f} mL/hour\n")
            print(f"• Standard Adult Giving Set (20 drops/mL): {ml_hr / 3:.0f} drops/min  (Formula: mL/hr ÷ 3)")
            print(f"• Blood Transfusion Set (15 drops/mL)   : {ml_hr / 4:.0f} drops/min  (Formula: mL/hr ÷ 4)")
            print(f"• Micro-Drip / Pediatric Set (60 gtt/mL): {ml_hr:.0f} drops/min  (Formula: mL/hr = drops/min)")
        elif "anion" in c_type:
            na = _arg(args, 0, "sodium (mmol/L)", 90, 190)
            cl = _arg(args, 1, "chloride (mmol/L)", 50, 150)
            hco3 = _arg(args, 2, "bicarbonate (mmol/L)", 2, 60)
            ag = na - (cl + hco3)
            low_hco3 = hco3 < 22
            print(f"SERUM ELECTROLYTES: Na+ = {na:g}, Cl- = {cl:g}, HCO3- = {hco3:g}")
            print(f"CALCULATED ANION GAP: {ag:.1f} mEq/L (usual reference 8–12; assay dependent; NOT albumin-corrected)\n")
            if ag > 12 and low_hco3:
                print("🔴 RESULT: HIGH ANION GAP METABOLIC ACIDOSIS (HAGMA)")
                print("   Differential: Ketoacidosis (DKA/alcoholic), Lactic acidosis, Uremia (renal failure), Toxic ingestions (methanol, ethylene glycol, salicylate).")
            elif ag > 12:
                print("🟠 RESULT: RAISED ANION GAP with bicarbonate >= 22 -- no metabolic acidosis pattern on these values; interpret in context.")
            elif low_hco3:
                print("🟢 RESULT: NORMAL ANION GAP METABOLIC ACIDOSIS (NAGMA)")
                print("   Differential: Diarrhea (GI bicarbonate loss), Renal Tubular Acidosis (RTA), Saline over-infusion.")
            else:
                print("⚪ RESULT: normal anion gap and normal bicarbonate -- no metabolic acidosis pattern on these values.")
        elif "mentzer" in c_type:
            mcv = _arg(args, 0, "MCV (fL)", 40, 130)
            rbc = _arg(args, 1, "RBC count (x10^12/L)", 1, 10)
            index = mcv / rbc
            print(f"RED CELL INDICES: MCV = {mcv:.1f} fL, RBC Count = {rbc:.2f} x 10^12/L")
            print(f"CALCULATED MENTZER INDEX: {index:.2f}\n")
            if mcv >= 80:
                print("⚪ RESULT: NOT APPLICABLE -- MCV is not microcytic (< 80 fL); the Mentzer index only helps in microcytosis.")
            elif index < 13:
                print("🔵 RESULT: SUGGESTIVE OF THALASSEMIA TRAIT (Index < 13)")
                print("   Action: Hold empirical iron therapy. Confirm with Hemoglobin Electrophoresis.")
            elif index > 13:
                print("🟠 RESULT: SUGGESTIVE OF IRON DEFICIENCY ANEMIA (Index > 13)")
                print("   Action: Confirm with Serum Ferritin and Transferrin Saturation prior to iron replacement.")
            else:
                print("⚪ RESULT: INDETERMINATE (Index = 13). Confirm with Serum Ferritin and Hemoglobin Electrophoresis.")
        else:
            print("Unknown calculator type. Supported: 'dengue', 'drop', 'anion', 'mentzer'.")
            return 2
    except ValueError as e:
        print(f"INPUT ERROR: {e}. No result was produced.")
        print("Usage: --tropical-calc dengue --calc-args <kg> | drop <mL/h> | anion <Na> <Cl> <HCO3> | mentzer <MCV> <RBC>")
        return 2
    print("=" * 80)
    return 0

def run_ward_facilities(test_query: str):
    print("=" * 80)
    print("🏥 SPECIALIZED DIAGNOSTIC LABORATORY DIRECTORY (BANGLADESH)")
    print("   Extracted from Dr. Kawsar Uddin's Clinical Guidance Threads")
    print("=" * 80)
    print(f"INVESTIGATION QUERY: \"{test_query}\"\n")

    directory = [
        {"test": "Aldosterone / Renin Ratio (ARR)", "facilities": "AFIP (Armed Forces Institute of Pathology), Dhaka CMH, BSMMU Dept of Endocrinology", "notes": "Special tube with iced plasma transport required; discontinue spironolactone 4-6 weeks prior."},
        {"test": "Hemoglobin Electrophoresis (HPLC)", "facilities": "BSMMU Dept of Hematology, Dhaka Medical College Hospital (DMCH), National Institute of Cancer (NICRH), Private reference labs", "notes": "Mandatory to exclude thalassemia minor before empirical iron."},
        {"test": "Serum Lipase / Amylase", "facilities": "All tertiary medical colleges, BSMMU, ICDDR,B diagnostic center, BIRDEM", "notes": "Lipase > 3x upper limit of normal is highly specific for acute pancreatitis."},
        {"test": "Urine Legionella Antigen", "facilities": "ICDDR,B (Diagnostic Unit, Mohakhali), BSMMU Microbiology, Evercare Hospital Lab", "notes": "Rapid immunochromatographic assay; retains positivity even after antibiotic initiation."},
        {"test": "Serum Antinuclear Antibodies (ANA) by IIF", "facilities": "BSMMU Immunology, AFIP Dhaka, Popular Diagnostic Center, LabAid", "notes": "Indirect immunofluorescence on HEp-2 cells is the gold standard screening method."},
        {"test": "ADAMTS13 Activity Assay", "facilities": "National Institute of Laboratory Medicine (NILMRC), BSMMU Hematology, Apollo/Evercare reference lab", "notes": "Crucial for confirming TTP; blood sample must be collected BEFORE starting plasma exchange."}
    ]

    terms = query_terms(test_query)
    matched = [d for d in directory if any(_has(d["test"], t) for t in terms)]
    if not matched:
        print("NO MATCH for this query -- showing the FULL directory below (these are not results for your query).\n")
        matched = directory

    for m in matched:
        print(f"🔬 INVESTIGATION: {m['test']}")
        print(f"📍 RELIABLE TESTING FACILITIES: {m['facilities']}")
        print(f"⚠️  CLINICAL COLLECTION NOTE: {m['notes']}\n")
    print("=" * 80)
    return 0

def run_search(query: str, lang: str = "any", top_k: int = 3):
    print("=" * 80)
    print(f"🔍 HYBRID BILINGUAL CDSS RETRIEVAL ENGINE")
    print(f"   Query: \"{query}\" | Language Filter: {lang.upper()} | Top K: {top_k}")
    print("=" * 80)
    return 0

    terms = query_terms(query)
    if not terms:
        terms = [query.lower().strip()]
    if not terms[0]:
        print("ERROR: empty query -- nothing was searched.")
        return 2

    results = []

    # 1. Search English Synthesis
    if lang in ["any", "en"]:
        for p in (NORMALIZED_DIR / "ENGLISH_SYNTHESIS").glob("*__ENGLISH.json"):
            data = json.loads(p.read_text(encoding="utf-8"))
            score = 0
            text_dump = (data.get("english_title", "") + " " + data.get("pathophysiology_mechanics_english", "") + " " + data.get("kawsar_clinical_pearls_english", "")).lower()
            for t in terms:
                if t in text_dump:
                    score += 2
            if score > 0:
                results.append({
                    "score": score,
                    "record_id": data["record_id"],
                    "language": "ENGLISH",
                    "title": data["english_title"],
                    "excerpt": data["kawsar_clinical_pearls_english"][:140] + "...",
                    "file_path": f"03_NORMALIZED_CORPUS/ENGLISH_SYNTHESIS/{data['record_id']}__ENGLISH.md"
                })

    # 2. Search Bengali / Mixed Markdown
    if lang in ["any", "bn"]:
        for p in (NORMALIZED_DIR / "MARKDOWN").glob("*.md"):
            text = p.read_text(encoding="utf-8")
            rid = p.stem
            score = 0
            text_lower = text.lower()
            for t in terms:
                if t in text_lower:
                    score += 1
            if score > 0:
                # Find matching line
                lines = [l.strip() for l in text.split("\n") if any(t in l.lower() for t in terms)]
                excerpt = lines[0][:140] + "..." if lines else text[:140] + "..."
                results.append({
                    "score": score,
                    "record_id": rid,
                    "language": "BENGALI_SOURCE",
                    "title": f"Habijabi Post #{rid}",
                    "excerpt": excerpt,
                    "file_path": f"03_NORMALIZED_CORPUS/MARKDOWN/{rid}.md"
                })

    # Sort results
    results.sort(key=lambda x: -x["score"])
    unique_records = []
    seen = set()
    for r in results:
        key = (r["record_id"], r["language"])
        if key not in seen:
            unique_records.append(r)
            seen.add(key)

    if not unique_records:
        print("No matching records found. Try adjusting keywords (e.g. 'dengue', 'gout', 'myeloma', 'thyroid').")
    else:
        for idx, r in enumerate(unique_records[:top_k], 1):
            print(f"[{idx}] {r['title']} (`{r['record_id']}`) — [{r['language']}]")
            print(f"    Excerpt: \"{r['excerpt']}\"")
            print(f"    Link: {(CORPUS_ROOT / r['file_path']).as_uri() if CORPUS_ROOT.is_absolute() else CORPUS_ROOT / r['file_path']}\n")
    print("=" * 80)
    return 0

# ==============================================================================
# CLI DISPATCHER
# ==============================================================================
def _positive_int(s):
    v = int(s)
    if v < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return v


def main_cli(argv=None) -> int:
    parser = argparse.ArgumentParser(description="HABIJABI CDSS & Socratic Preceptor Navigator")
    parser.add_argument("--preceptor", type=str, help="Run Interactive Socratic Preceptor for a clinical case")
    parser.add_argument("--exam-sba", type=str, nargs="?", const="random", help="Generate Postgraduate SBA exam question (item id or 'random')")
    parser.add_argument("--prescribing-safety", type=str, help="Keyword screen against 6 fixed rules (NOT a safety clearance)")
    parser.add_argument("--federated", type=str, help="Habijabi -> Davidson bridge lookup (other books are not queried here)")
    parser.add_argument("--tropical-calc", type=str, help="Run tropical ward calculator (dengue, drop, anion, mentzer)")
    parser.add_argument("--calc-args", type=str, nargs="*", default=[], help="Arguments for tropical calculator")
    parser.add_argument("--ward-facilities", type=str, help="Lookup specialized diagnostic laboratory facilities")
    parser.add_argument("--search", type=str, help="Search bilingual corpus")
    parser.add_argument("--lang", type=str, default="any", choices=["any", "en", "bn"], help="Language filter for search")
    parser.add_argument("--top_k", type=_positive_int, default=3, help="Number of search results (>= 1)")

    args = parser.parse_args(argv)

    modes = [("preceptor", args.preceptor), ("exam_sba", args.exam_sba), ("prescribing_safety", args.prescribing_safety),
             ("federated", args.federated), ("tropical_calc", args.tropical_calc),
             ("ward_facilities", args.ward_facilities), ("search", args.search)]
    chosen = [(n, v) for n, v in modes if v is not None]   # `is not None`: an empty string is a (rejected) request, not "no request"
    if not chosen:
        parser.print_help()
        return 0
    if len(chosen) > 1:
        print(f"ERROR: choose exactly one mode, got {[n for n, _ in chosen]}", file=sys.stderr)
        return 2
    name, value = chosen[0]
    if name != "exam_sba" and not str(value).strip():
        print(f"ERROR: --{name.replace('_', '-')} requires a non-empty value; nothing was evaluated.", file=sys.stderr)
        return 2
    if name == "preceptor":
        return run_preceptor(value)
    if name == "exam_sba":
        return run_exam_sba(value)
    if name == "prescribing_safety":
        return run_prescribing_safety(value)
    if name == "federated":
        return run_federated(value)
    if name == "tropical_calc":
        return run_tropical_calc(value, args.calc_args)
    if name == "ward_facilities":
        return run_ward_facilities(value)
    return run_search(value, args.lang, args.top_k)


def main():
    sys.exit(main_cli())


if __name__ == "__main__":
    main()
