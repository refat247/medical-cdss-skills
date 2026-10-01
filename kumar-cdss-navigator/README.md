# Kumar & Clark CDSS Navigator (v1.0.1)

Production-grade Clinical Decision Support System (CDSS) and Index Retrieval Engine grounded directly in the 11th Edition of *Kumar and Clark's Clinical Medicine (2026)*.

## 🚀 Quick Usage

```powershell
# 1. Clinical query with span compression
python scripts/navigator.py --query "Acute liver failure management" --compress

# 2. Case vignette decomposition
python scripts/navigator.py --vignette "45-year-old male with hematemesis, ascites, and spider angiomas."

# 3. Medical concept checklist / outline
python scripts/navigator.py --outline "Acute abdomen"

# 4. Drug safety guardrails
python scripts/navigator.py --validate-therapy "Amiodarone" "atrial fibrillation"

# 5. Differential diagnosis
python scripts/navigator.py --diff "Conjunctivitis"
```

## 🏗️ Architecture
* **Underlying Engine**: `04_Kumar_and_Clark_11/Index/cdss_qa_router.py`
* **Coverage**: 50 clinical chapters, 9,394 L2 micro-chunks, 1,803 visual figure assets, and 33,454 indexed vocabulary terms.
* **Retrieval Latency**: < 2 ms average query latency with early-exit section bounding.
