---
name: medical-cdss-unified-orchestrator
version: 1.5.1
description: |
  Unified Clinical Decision Support System (CDSS) and cross-book diagnostic retrieval orchestrator across
  Davidson's Principles and Practice of Medicine (25th Edition), Harrison's Principles of Internal Medicine
  (22nd Edition), Fuster & Hurst's The Heart (15th Edition), and Kumar and Clark's Clinical Medicine
  (11th Edition 2026). Provides multi-turn clinical QA, case vignette decomposition, zero-hallucination
  drug therapy safety verification, and sub-millisecond retrieval across 28,000+ clinical chunks.
  Use ONLY for multi-book (federated) queries; a query about one book goes to that book's navigator (harrison/hurst/kumar-cdss-navigator) and is not handled here.
---

# Unified Medical CDSS Orchestrator (v1.5.1)

Production-grade Clinical Decision Support System (CDSS) orchestrator that unifies and federates clinical queries across the four major pillars of clinical medicine:
- **General Practice & Primary Care**: *Davidson's Principles and Practice of Medicine (25th Edition)*
- **Internal Medicine Reference**: *Harrison's Principles of Internal Medicine (22nd Edition)*
- **Cardiovascular Medicine**: *Fuster & Hurst's The Heart (15th Edition)*
- **Clinical Practice & Medical Specialties**: *Kumar & Clark's Clinical Medicine (11th Edition 2026)*

---

## 🎯 When to Activate This Skill

Activate this skill automatically whenever:
- The user or physician asks an **evidence-based clinical question**, disease workup, or management query.
- Solving or analyzing **complex clinical case vignettes** (FCPS, USMLE Step 2/3, MRCP, ABIM, cardiology/internal medicine fellowship exams).
- Validating **drug therapy indications, contraindications, or safety** across multi-organ disorders (e.g., heart failure with chronic kidney disease).
- Comparing **differential diagnoses & look-alikes** (*DKA vs HHS*, *Athlete's Heart vs HCM*, *NSTEMI vs Takotsubo*).
- Cross-referencing **landmark clinical trials** (e.g. *PARADIGM-HF*, *DAPT*, *EMPEROR*, *ISCHEMIA*).
- Requiring **token-efficient prompt checklists** (`--outline`) or **span-compressed micro-windows** (`--compress`).

---

## 💻 Engine CLI Reference

The unified CLI runner is located at `scripts/unified_orchestrator.py`:

### 1. Cross-Book Federated Search (All Books)
Retrieves the top ranked clinical micro-chunks across Davidson, Harrison, and Hurst simultaneously:
```powershell
python "C:\Users\User\.gemini\config\skills\medical-cdss-unified-orchestrator\scripts\unified_orchestrator.py" `
  --query "Acute pulmonary embolism management" `
  --book all `
  --top_k 2
```

### 2. Complex Clinical Case Vignette Decomposition
Decomposes patient presentation, vital signs, and comorbidities across cardiology and internal medicine:
```powershell
python "C:\Users\User\.gemini\config\skills\medical-cdss-unified-orchestrator\scripts\unified_orchestrator.py" `
  --vignette "65-year-old male with type 2 diabetes and CKD stage 4 presents with crushing retrosternal chest pain, BP 84/50 mmHg, HR 112 bpm, diaphoresis, and elevated troponin."
```

### 3. Cross-Book Drug Therapy Safety Guardrail
Cross-validates drug indications, dosage safety, and contraindications across both Hurst and Harrison:
```powershell
python "C:\Users\User\.gemini\config\skills\medical-cdss-unified-orchestrator\scripts\unified_orchestrator.py" `
  --validate-therapy "Sacubitril/valsartan" "heart failure"
```

### 4. Differential Diagnosis & Look-Alike Comparators
Retrieves structured comparator tables directly from textbook differential trees:
```powershell
python "C:\Users\User\.gemini\config\skills\medical-cdss-unified-orchestrator\scripts\unified_orchestrator.py" `
  --diff "Takotsubo"
```

### 5. Prompt-Ready Medical Outline Checklist (~120 Tokens)
Generates structured diagnostic and therapeutic checklists for token-efficient prompt conditioning:
```powershell
python "C:\Users\User\.gemini\config\skills\medical-cdss-unified-orchestrator\scripts\unified_orchestrator.py" `
  --outline "Diabetic ketoacidosis"
```

### 6. Grounded 4-Book Context Packet Builder
Extracts and partitions grounded chunks across the 4 textbooks to prevent parametric hallucinations during bridge note generation:
```powershell
python "C:\Users\User\.gemini\config\skills\medical-cdss-unified-orchestrator\scripts\unified_orchestrator.py" `
  --build-context-packet "Cardiac Murmurs" `
  --output "path\to\context_packet.json"
```

---

## 🏛️ Federated Knowledge Base

The orchestrator sits directly atop the compiled library at `D:\01_Medical_Study\CDSS_Retrieval_Package`:
- **Kumar & Clark 11**: 9,394 discrete L2 micro-chunks, 33,454 indexed vocabulary terms, 50 clinical chapters.
- **Harrison 22**: 10,419 discrete L2 micro-chunks, 57,015 indexed vocabulary terms, 20 clinical parts.
- **Hurst 15**: 5,258 discrete L2 micro-chunks, 827 landmark randomized controlled trials, 12 clinical sections.
- **Davidson 25**: SQLite CDSS global index, clinical calculators, and L2/L3 semantic retrieval spans.

---

## 📋 CDSS Execution Protocol for AI Agents

When acting as a medical assistant:
1. **Clinical Intent Triage**:
   - Patient story / exam scenario $\rightarrow$ `--vignette`.
   - Disease protocol or quick lookup $\rightarrow$ `--query --compress`.
   - Drug prescribing or polypharmacy $\rightarrow$ `--validate-therapy`.
   - Distinguishing look-alike diseases $\rightarrow$ `--diff`.
2. **Inject Compressed Micro-Spans**: Never dump thousands of raw textbook tokens into the prompt context. Always use targeted excerpts or compressed micro-windows (< 150 words per chunk).
3. **Rigorous Clinical Provenance**: Always cite the Textbook, Edition, Part/Section, Chapter Topic, and Chunk ID.

---

## 🛡️ Sub-Skills Inventory & Handover Contracts

The Unified Orchestrator augments, federates, and routes queries across four dedicated sub-skills:

| Governed Sub-Skill | Clinical Domain | Handover Contract & Routing |
| :--- | :--- | :--- |
| [`harrison-cdss-navigator`](../harrison-cdss-navigator/SKILL.md) | Internal Medicine & Multisystem Disorders | Dispatches general medicine queries, complex polypharmacy vignettes, and differential trees via `02_Harrison_22/Index/cdss_qa_router.py`. |
| [`hurst-cdss-navigator`](../hurst-cdss-navigator/SKILL.md) | Cardiovascular Medicine & Hemodynamics | Dispatches ECG findings, valve gradients, landmark cardiology trials (PARADIGM-HF, DAPT), and heart failure safety checks via `03_Hurst_The_Heart_15/Index/cdss_qa_router.py`. |
| [`kumar-cdss-navigator`](../kumar-cdss-navigator/SKILL.md) | Clinical Specialties & Board Examination | Dispatches specialty disease protocols, board review MCQs, and reference intervals via `04_Kumar_and_Clark_11/Index/cdss_qa_router.py`. |
| [`davidson-rag-pipeline-antigravity`](../davidson-rag-pipeline-antigravity/SKILL.md) | General Practice & Curricular Truth | Queries Davidson 25 SQLite CDSS engine (`DAVIDSON_25_CDSS_ENGINE.db`) for baseline primary care truth and clinical calculators. |

---

## 🔄 Pre-Done Corpus Prerequisites & Fallback Protocol

As a query-time diagnostic router, the orchestrator operates on pre-compiled assets. The table below defines runtime behavior based on whether upstream assets are pre-done or pending:

| Upstream Asset / Sub-Skill | Status | Orchestrator Runtime Behavior |
| :--- | :--- | :--- |
| **All 4 Books Pre-Done** | Production Ready | Full federated search (`--book all`), 4-book vignette decomposition, and automated context packet generation are 100% active. |
| **Individual Book Missing / In-Progress** | Partial Corpus | **Graceful Degradation**: Vignette decomposition logs `[BOOK] Router not available` for the pending book, but successfully returns answers from all available books. |
| **Federated Search Script Missing** | Not Packaged | **Hard Error**: If `cdss_federated_search.py` is absent from `D:\01_Medical_Study\CDSS_Retrieval_Package`, cross-book queries cannot execute. Run `cdss-retrieval-packager auto` to compile the package. |
| **Book Updated / Re-Compiled** | Pre-Done Update | **Zero Cache Invalidation Needed**: Routers read SQLite DBs and JSON indexes dynamically relative to their installation directories. |

## Exit Codes & Fallbacks (2026-09-25)
- Every mode exits `1` when no textbook source is reachable.
- `--build-context-packet` writes nothing and exits `1` when retrieval fails or returns no chunks. Per-book retrieval errors are listed under `warnings` and are never counted as chunks.
- Davidson is included in `--diff` and `--outline`. Kumar & Clark uses the packaged router in every mode.
- If a packaged router is missing, the unpackaged build router is used only with a `[WARN]` on stderr.
- Paths: `CDSS_PACKAGE_DIR`, `CDSS_SKILLS_ROOT`, `CDSS_HARRISON_BUILD_ROUTER` and `CDSS_HURST_BUILD_ROUTER` override the defaults.
