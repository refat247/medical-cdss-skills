# Medical RAG Master Orchestrator (v1.4.0)

Installed (v1.4.0)

Production-grade lifecycle orchestrator that chains and governs the end-to-end transformation of raw medical textbook PDFs into production-grade Clinical Decision Support System (CDSS) retrieval packages and journal-grade Cognitive Bridge Notes.

## 🚀 Quick Usage

```powershell
# 1. Audit textbook chapter status (detects pre-done stages)
python scripts/orchestrator.py status --book-dir "D:\01_Medical_Study\SPLIT Pdfs\Davidson_25_Split"

# 2. Stage 1: Ingest and organize raw Mistral OCR downloads
python scripts/orchestrator.py organize --target-dir "D:\01_Medical_Study\SPLIT Pdfs\Davidson_25_Split"

# 3. Stage 2: Inline tables and figures (with skip-logic for pre-done chapters)
python scripts/orchestrator.py preready --chapter-dir "D:\path\to\ch01" --skip-completed

# 4. Stage 3: Run 18-stage RAG extraction (with skip-logic for pre-done chapters)
python scripts/orchestrator.py rag --source "D:\path\to\ch01.markdown_inlined.md" --skip-completed

# 5. Stage 4: Compile 26-asset index intelligence suite
python scripts/orchestrator.py index --book "Davidson" --edition "25th Edition" --corpus "D:\path" --index "D:\path\index.md" --output "D:\path\Index\rag_pipeline_output"

# 6. Stage 5: Package, prune build scorecards, and federate
python scripts/orchestrator.py package --package-dir "D:\01_Medical_Study\CDSS_Retrieval_Package"

# 7. Stage 6: Publish Cognitive Bridge Note & Word document
python scripts/orchestrator.py publish-note --topic "Cardiac Murmurs" --output-dir "D:\01_Medical_Study\CDSS_human_test"

# 8. Full automated lifecycle with smart chapter processing and skip-logic
python scripts/orchestrator.py auto --book-dir "D:\01_Medical_Study\SPLIT Pdfs\Davidson_25_Split" --process-chapters --skip-completed
```
