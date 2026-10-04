# Harrison CDSS Navigator (v1.0.2)

Production-grade Clinical Decision Support System and Index Retrieval Engine grounded directly in the 22nd Edition of *Harrison's Principles of Internal Medicine* (3,900+ pages, 20 clinical parts, 10,419 L2 micro-chunks, 7,811 indexed clinical concepts, and 57,015 indexed vocabulary terms).

## 🚀 Quick Usage

```powershell
# 1. Clinical query with span compression
python scripts/navigator.py --query "Acute myocardial infarction management" --compress

# 2. Case vignette decomposition
python scripts/navigator.py --vignette "65-year-old male with diabetes presenting with chest pain."

# 3. Medical outline checklist
python scripts/navigator.py --outline "Diabetic Ketoacidosis"

# 4. Differential diagnosis lookup
python scripts/navigator.py --diff "Meningitis"
```
