# CDSS Retrieval Packager (v1.5.1)

Installed (v1.5.1)

Production-grade utility for compiling, pruning, and validating lean, high-performance **CDSS Retrieval Packages** from compiled medical textbook libraries (*Davidson*, *Harrison*, *Hurst*, *Braunwald*, *Kumar & Clark*).

## 🚀 Quick Usage

```powershell
# 1. End-to-end autonomous optimization (prune, patch, federate, verify)
python scripts/packager.py auto --package-dir "D:\01_Medical_Study\CDSS_Retrieval_Package"

# 2. Prune build-time QA scorecards while preserving clinical images
python scripts/packager.py prune --package-dir "D:\01_Medical_Study\CDSS_Retrieval_Package"

# 3. Patch router scripts for dynamic relative path portability
python scripts/packager.py patch-paths --package-dir "D:\01_Medical_Study\CDSS_Retrieval_Package"

# 4. Generate unified cross-book federated search CLI
python scripts/packager.py federate --package-dir "D:\01_Medical_Study\CDSS_Retrieval_Package"

# 5. Execute sub-millisecond retrieval smoke tests
python scripts/packager.py verify --package-dir "D:\01_Medical_Study\CDSS_Retrieval_Package"
```
