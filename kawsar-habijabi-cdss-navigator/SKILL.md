---
name: kawsar-habijabi-cdss-navigator
version: 1.0.0
description: |
  Clinical Decision Support System (CDSS) and Socratic Preceptor Navigator for Dr. Kawsar Uddin's
  Habijabi medical series and bedside clinical heuristics across 137 verified internal medicine records.
  Provides interactive ward-round preceptorship, FCPS/MRCP Single Best Answer (SBA) exam generation,
  bedside prescribing safety interception, federated 4-textbook cross-grounding (Davidson 25,
  Harrison 22, Hurst 15, Kumar & Clark 11), tropical fluid calculation heuristics, and bilingual
  sub-millisecond retrieval.
---

# Kawsar Habijabi CDSS & Socratic Preceptor Navigator (v1.0.0)

A specialized Clinical Decision Support System (CDSS) skill designed for junior doctors, interns, postgraduate trainees (FCPS, MRCP, MD), and medical officers practicing in hospital wards and outpatient clinics.

This skill bridges the gap between **international textbook theory** (*Davidson 25th Edition*, *Harrison 22nd Edition*) and **bedside clinical reality in high-volume, resource-constrained South Asian hospitals** using Dr. Kawsar Uddin's documented teaching heuristics.

---

## 🎯 When to Activate This Skill

Activate this skill automatically whenever:
- The user or physician asks about **Dr. Kawsar Uddin's clinical teaching or Habijabi medical posts**.
- Conducting an **interactive case presentation / morning report** or seeking Socratic preceptor feedback on a patient case.
- Preparing for **postgraduate clinical examinations** (FCPS Part 1, MRCP Part 1 & 2, MD Residency, BCS) requiring Single Best Answer (SBA) questions with dual textbook and bedside rationales.
- Validating **bedside prescribing safety** to intercept common cognitive traps (e.g. allopurinol during acute gout flare, empirical iron in microcytic anemia without ruling out thalassemia, indiscriminate fluid bolusing in dengue, linezolid + SSRI co-prescription).
- Seeking **tropical ward calculations** (fluid drop counting using standard gravity sets, maintenance + 5% deficit dengue regimens, Mentzer index, anion gap).
- Locating **specialized diagnostic testing facilities in Bangladesh** (where to order ARR, HPLC, ANA, or urine Legionella tests in Dhaka).
- Performing **bilingual semantic retrieval** across Bengali source posts, English clinical syntheses, and filtered peer Q&A threads.

---

## 💻 Engine CLI Reference

The master CLI runner is located at `scripts/habijabi_navigator.py`:

### 1. Interactive Socratic Ward Preceptor
Simulates a morning report / ward round preceptorship session, decomposing the patient presentation into mechanisms-first reasoning, posing Socratic reflection questions, and warning against knee-jerk prescribing:
```powershell
python "C:\Users\User\.gemini\config\skills\kawsar-habijabi-cdss-navigator\scripts\habijabi_navigator.py" `
  --preceptor "Young 20-year-old male with severe hypertension and hypokalemia"
```

### 2. Postgraduate Exam SBA Generator (FCPS / MRCP / MD)
Generates high-yield Single Best Answer (SBA) questions with realistic clinical stems, plausible distractors, answer keys, and dual citations to *Habijabi* and *Davidson 25th Edition*:
```powershell
python "C:\Users\User\.gemini\config\skills\kawsar-habijabi-cdss-navigator\scripts\habijabi_navigator.py" `
  --exam-sba "HABIJABI-003"
```
*(Or omit the ID for a random high-yield exam question)*:
```powershell
python "C:\Users\User\.gemini\config\skills\kawsar-habijabi-cdss-navigator\scripts\habijabi_navigator.py" `
  --exam-sba
```

### 3. Bedside Prescribing Safety Interceptor
Evaluates a proposed drug order or regimen against 43 clinical safety rules and error corrections, issuing immediate hard-stop alerts with mechanisms of harm and safer alternatives:
```powershell
python "C:\Users\User\.gemini\config\skills\kawsar-habijabi-cdss-navigator\scripts\habijabi_navigator.py" `
  --prescribing-safety "Acute gout flare: start allopurinol 100mg"
```

### 4. Federated 4-Textbook Cross-Grounding
Cross-references Habijabi clinical pearls with the 4 master textbooks on disk (*Davidson 25*, *Harrison 22*, *Hurst 15*, *Kumar & Clark 11*):
```powershell
python "C:\Users\User\.gemini\config\skills\kawsar-habijabi-cdss-navigator\scripts\habijabi_navigator.py" `
  --federated "Dengue fluid management"
```

### 5. Tropical & Resource-Constrained Ward Companion
Provides bedside gravity IV giving set calculators and specialized diagnostic facility routing:
- **Dengue fluid resuscitation (Maintenance + 5% deficit & drop count)**:
  ```powershell
  python "C:\Users\User\.gemini\config\skills\kawsar-habijabi-cdss-navigator\scripts\habijabi_navigator.py" `
    --tropical-calc dengue --calc-args 55
  ```
- **IV drop-rate conversions (mL/hr to drops/min for 20, 15, and 60 gtt/mL sets)**:
  ```powershell
  python "C:\Users\User\.gemini\config\skills\kawsar-habijabi-cdss-navigator\scripts\habijabi_navigator.py" `
    --tropical-calc drop --calc-args 120
  ```
- **Mentzer index calculator (MCV / RBC count)**:
  ```powershell
  python "C:\Users\User\.gemini\config\skills\kawsar-habijabi-cdss-navigator\scripts\habijabi_navigator.py" `
    --tropical-calc mentzer --calc-args 64 5.9
  ```
- **Specialized Diagnostic Laboratory Directory (Bangladesh)**:
  ```powershell
  python "C:\Users\User\.gemini\config\skills\kawsar-habijabi-cdss-navigator\scripts\habijabi_navigator.py" `
    --ward-facilities "Aldosterone Renin Ratio"
  ```

### 6. Hybrid Bilingual Semantic Retrieval Engine
Searches across 137 verbatim Bengali posts, 137 English clinical syntheses, 560 filtered clinical comments, and 43 clinical claims:
```powershell
python "C:\Users\User\.gemini\config\skills\kawsar-habijabi-cdss-navigator\scripts\habijabi_navigator.py" `
  --search "Thalassemia trait iron hemosiderosis" --lang en --top_k 2
```

---

## 🔒 Clinical Safety & Governance Guardrails
1. **Zero Overriding Precept**: Kawsar-derived clinical teaching provides historical, pedagogical, and bedside heuristic models; it never overrides current authoritative clinical evidence or institutional guidelines.
2. **Temporal Quarantine**: Early 2020 pandemic therapies (hydroxychloroquine, convalescent plasma, ivermectin) are preserved with strict `HISTORICAL_ONLY` tags and are never recommended for active patient care.
3. **Evidence Class Segregation**: The engine maintains absolute separation between authoritative textbooks (Class A), Kawsar clinical instruction (Class B), Kawsar persona/heuristics (Class C), peer learner discussions (Class D), and model translations (Class E).
