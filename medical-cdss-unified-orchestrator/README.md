# Unified Medical CDSS Orchestrator (v1.5.1)

Installed (v1.5.1)

Production-grade Clinical Decision Support System (CDSS) orchestrator that unifies and federates clinical queries across the four major pillars of clinical medicine:
- **General Practice & Primary Care**: *Davidson's Principles and Practice of Medicine (25th Edition)*
- **Internal Medicine Reference**: *Harrison's Principles of Internal Medicine (22nd Edition)*
- **Cardiovascular Medicine**: *Fuster & Hurst's The Heart (15th Edition)*
- **Clinical Practice & Medical Specialties**: *Kumar & Clark's Clinical Medicine (11th Edition 2026)*

## 🚀 CLI Reference

```powershell
# Cross-book search
python scripts/unified_orchestrator.py --query "Acute pulmonary embolism" --book all

# Case vignette decomposition
python scripts/unified_orchestrator.py --vignette "65-year-old male with diabetes and CKD presenting with chest pain."

# Drug therapy safety guardrails
python scripts/unified_orchestrator.py --validate-therapy "Sacubitril/valsartan" "heart failure"
```
