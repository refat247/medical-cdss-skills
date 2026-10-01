# CDSS Unicode & Anti-Mojibake Guard (v1.6.1)

Installed (v1.6.1)

Production-grade encoding integrity guard and pre-flight sanitizer for medical textbook Clinical Decision Support Systems (CDSS). Prevents and repairs character corruption (mojibake) and enforces ISMP/FDA clinical symbol safety across all corpora.

## 🚀 Quick Usage

```powershell
# 1. Audit a textbook or guideline directory for encoding defects
python scripts/guard.py audit --target-dir "D:\01_Medical_Study\SPLIT Pdfs\Davidson_25_Split"

# 2. Fix encoding in-place and enforce ISMP safe abbreviations (µg -> mcg)
python scripts/guard.py fix --target-dir "D:\01_Medical_Study\SPLIT Pdfs\Davidson_25_Split" --enforce-ismp

# 3. Cleanroom pre-sanitization before Word (.docx) export
python scripts/guard.py fix --target-dir "D:\01_Medical_Study\CDSS_human_test" --dry-run   # preview first, then run without --dry-run
python scripts/guard.py cleanroom-docx --file note.md --out clean/note.md   # separate subcommand for generated notes
```
