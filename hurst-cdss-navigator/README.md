# Hurst CDSS Navigator (v1.0.2)

Production-grade Clinical Decision Support System (CDSS) and index retrieval navigator for *Fuster & Hurst's The Heart (15th Edition)*.

---

## 📖 Overview

The `hurst-cdss-navigator` skill provides autonomous, sub-millisecond, zero-token overhead clinical question answering, case vignette decomposition, landmark trial citations, and drug therapy safety guardrails directly grounded in *Fuster & Hurst's The Heart*.

### Key Capabilities
- **Case Vignette Decomposition**: Extracts patient demographics, hemodynamics (BP, HR, LVEF, Cr), shock classifications, drug reconciliation warnings, and look-alike differentials.
- **Span Compression**: Emits ~35-word high-yield excerpts directly from textbook micro-chunks (**96.2% token savings**).
- **Zero-Hallucination Grounding**: Cites exact Sections, Chapter Topics, and Chunk IDs from the 4,006-page corpus.
- **Drug Safety Guardrails**: Validates indications, contraindications, and dosing precautions across 717 drugs and 249 cardiac diseases.

---

## 🚀 Quick-Start CLI Commands

The engine script is located at:
`D:\01_Medical_Study\Fcps\cardiology_book\Fuster & Hurst's The Heart_split\Index\rag_pipeline_output\cdss_qa_router.py`

### 1. Complex Case Vignette Action Plan
```powershell
python "D:\01_Medical_Study\Fcps\cardiology_book\Fuster & Hurst's The Heart_split\Index\rag_pipeline_output\cdss_qa_router.py" --vignette "65yo male with anterior STEMI and EF 28% in pulmonary edema, BP 88/54, HR 115, Cr 2.6 on ARNI, spironolactone, furosemide."
```

### 2. Extractive Span-Compressed Search (-96% Tokens)
```powershell
python "D:\01_Medical_Study\Fcps\cardiology_book\Fuster & Hurst's The Heart_split\Index\rag_pipeline_output\cdss_qa_router.py" --query "Cardiogenic shock inotropic support" --compress
```

### 3. Prompt-Ready Medical Outline Checklist (120 Tokens)
```powershell
python "D:\01_Medical_Study\Fcps\cardiology_book\Fuster & Hurst's The Heart_split\Index\rag_pipeline_output\cdss_qa_router.py" --outline "Acute heart failure"
```

### 4. Differential Diagnosis & "Vs." Comparator
```powershell
python "D:\01_Medical_Study\Fcps\cardiology_book\Fuster & Hurst's The Heart_split\Index\rag_pipeline_output\cdss_qa_router.py" --diff "Takotsubo"
```

### 5. Therapy Validation Guardrail
```powershell
python "D:\01_Medical_Study\Fcps\cardiology_book\Fuster & Hurst's The Heart_split\Index\rag_pipeline_output\cdss_qa_router.py" --validate-therapy "Sacubitril/valsartan" "heart failure"
```

---

## 🔒 Versioning & Compliance
Maintained under [SemVer 2.0.0](https://semver.org/) and verified using `version-manager`.
Verification command:
```powershell
python C:\Users\User\.gemini\config\skills\version-manager\scripts\bump_version.py "C:\Users\User\.gemini\config\skills\hurst-cdss-navigator" --verify
```
