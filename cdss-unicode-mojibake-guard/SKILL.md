---
name: cdss-unicode-mojibake-guard
version: 1.5.2
description: |
  Autonomous Unicode, Anti-Mojibake, ISMP Clinical Safety, and LaTeX De-Delimiter Guard for medical textbook CDSS corpora.
  Provides pre-flight audits, in-place UTF-8 repair, Unicode NFKC canonicalization, zero-width token-breaker stripping,
  FDA/ISMP clinical symbol safety enforcement, and automatic LaTeX de-mathifying across all medical books.
---

# CDSS Unicode & Anti-Mojibake Guard (v1.5.2)

Production-grade encoding integrity guard and pre-flight sanitizer for medical textbook Clinical Decision Support Systems (CDSS). Prevents and repairs character corruption (**mojibake** like `â‰¥`, `Âµg`, `â€™`) and enforces clinical symbol safety before text is ingested into RAG pipelines or emitted into LLM prompt contexts.

---

## 🎯 1. When to Activate This Skill

Activate this skill automatically whenever:
- Starting or continuing the RAG conversion of any medical textbook or clinical practice guideline (*Davidson*, *Harrison*, *Hurst*, *Kumar & Clark*, *Braunwald*, *ADA*, *KDIGO*, *ESC*, *NICE*).
- Running **Gate 0 (Pre-Flight Ingestion)**: Auditing raw OCR markdown files before inlining tables and decoupling figures.
- User asks:
  - **"Audit this folder for mojibake or encoding errors"**.
  - **"Fix character corruption / double-encoded UTF-8"**.
  - **"Ensure LLM prompt tokens are safe from byte-splitting"**.
  - **"Strip BOM marks (\ufeff) or zero-width spaces"**.
  - **"Enforce ISMP/FDA clinical symbol safety (µg -> mcg, ≥ -> >=)"**.

---

## 🛡️ 2. The 6-Layer Protection Standard

| Layer | Guard Mechanism | Rationale & Safety Rule |
| :--- | :--- | :--- |
| **Layer 1** | **PEP 540 & Console Hardening** | Enforces `sys.stdout.reconfigure(encoding='utf-8')` to prevent Windows `cp1252` terminal crashes. |
| **Layer 2** | **Double-Encoding Repair Table** | Automatically repairs CP1252-decoded UTF-8 bytes (`â‰¥` $\to$ `>=`, `Âµg` $\to$ `mcg`, `â€”` $\to$ ` - `). |
| **Layer 3** | **Unicode NFKC Canonicalization** | Standardizes composite glyphs, ligatures (`ﬁ` $\to$ `fi`), and full-width forms via `unicodedata.normalize('NFKC')`. |
| **Layer 4** | **Token-Breaker Strip** | Strips invisible characters that confuse LLM tokenizers: zero-width space (`\u200b`), BOM (`\ufeff`), soft hyphens (`\u00ad`). |
| **Layer 5** | **ISMP / FDA Clinical Safety** | Replaces high-risk abbreviations per FDA "Do Not Use" list: `µg` $\to$ `mcg` (prevents 1,000× overdose), `≥` $\to$ `>=`, `±` $\to$ `+/-`. |
| **Layer 6** | **Unicode-Safe JSON Serialization** | Forces `ensure_ascii=False` so downstream LLMs receive clean UTF-8 text rather than escaped slash sequences (`\u2265`). |
| **Layer 7** | **Clinical LaTeX De-Delimiter** | Strips OCR and LLM math markers: `$\ge$` $\to$ `>=`, `$S_1$` $\to$ `S1`, `$A_2\text{--}OS$` $\to$ `A2-OS`, `\text{--}` $\to$ `-`. |
| **Layer 8** | **Clinical Math & Physics Normalizer** | Converts equations & physics symbols into clean clinical Unicode (`\Delta P` $\to$ `Delta P`, `\times` $\to$ `x`, `\approx` $\to$ `~`, `\rho` $\to$ `rho`, `\mu` $\to$ `mcg`/`mu`), with `--cleanroom-docx` pre-sanitizing before Word export. |

---

## 💻 3. CLI Quick-Start (`scripts/guard.py`)

### 1. Audit a Corpus Directory (Read-Only)
Scans all text, markdown, and JSON files in a directory and reports any encoding or mojibake anomalies:
```powershell
python "C:\Users\User\.gemini\config\skills\cdss-unicode-mojibake-guard\scripts\guard.py" audit `
  --target-dir "D:\01_Medical_Study\CDSS_Retrieval_Package"
```

### 2. In-Place Repair & Clean (`fix`)
Scans and automatically fixes double-encoded mojibake, strips BOMs, and normalizes Unicode in-place:
```powershell
python "C:\Users\User\.gemini\config\skills\cdss-unicode-mojibake-guard\scripts\guard.py" fix `
  --target-dir "D:\01_Medical_Study\guideline" `
  --enforce-ismp
```

### 3. Pre-Flight Blocking Gate (`gate`)
Returns exit code 0 if 100% clean, or exit code 1 if corruptions exist (for pipeline automation):
```powershell
python "C:\Users\User\.gemini\config\skills\cdss-unicode-mojibake-guard\scripts\guard.py" gate `
  --target-dir "D:\01_Medical_Study\SPLIT Pdfs\Braunwald_Split"
```

### 4. Sanitize a Single Text File or String (`sanitize`)
```powershell
python "C:\Users\User\.gemini\config\skills\cdss-unicode-mojibake-guard\scripts\guard.py" sanitize `
  --file "path\to\chapter_chunks.md" `
  --output "path\to\chapter_chunks_clean.md"
```

---

## 🔗 4. Python API Integration

Other skills and routers can directly import the guard:

```python
from guard import sanitize_for_llm, safe_json_dumps, enforce_utf8_environment, repair_mojibake

# 1. Enforce UTF-8 in current runtime
enforce_utf8_environment()

# 2. Prepare chunk text safely for LLM context prompts
clean_excerpt = sanitize_for_llm(raw_chunk_text, enforce_ismp=True)

# 3. Serialize JSON for LLM API without slash-escapes
payload = safe_json_dumps(results, indent=2)
```

---

## 🔗 5. Cross-References

| Relationship | Skill | Role |
| :--- | :--- | :--- |
| **Downstream** | `davidson-ocr-preready` | Receives sanitized markdown from this gate |
| **Downstream** | `davidson-rag-pipeline-antigravity` | Consumes clean text ensured by this guard |
| **Downstream** | `cdss-bridge-note-publisher` | Uses this guard for pre-publish sanitization |
| **Orchestrator** | `medical-rag-orchestrator` | Invokes this skill as Gate 0 (pre-flight ingestion) |

## Source-Verbatim Rule (2026-09-25)
- `fix` repairs encoding damage only, and restores the original character: `Âµg` -> `µg`, `â‰¥` -> `≥`, stray CP1252 bytes are decoded, and BOM, zero-width and soft-hyphen characters are stripped. It does NOT convert `µg`/`≥`/`±`, LaTeX or dose expressions, so source text matches the printed book and the trusted pipeline corpus.
- All output normalisation happens only in generated output, via `sanitize_for_llm()` and `cleanroom-docx`:
  - `µg` -> `mcg`, `≥` -> `>=`
  - LaTeX de-delimiting
  - ISMP dose rewrites: `5.0 mg` -> `5 mg`, `QD` -> `once daily`, `IU`/`U` -> `units`. Trailing-zero removal applies to dose units only, never to lab values such as `Hb 13.0 g/dL`.
- `audit` / `gate` block only on real corruption:
  - mojibake, U+FFFD and invisible characters
  - legacy corruption: `mcgmol`, `mcgg`, `109/L`, `1012/L` and the fraction slash (from the old guard's Unicode bug or from OCR)
- Raw `µg`, LaTeX and ISMP dose issues are reported as non-blocking `advisories`.
- `audit --include-outputs` also scans `rag_pipeline_output/`. Files with legacy corruption must be regenerated from source or re-copied from the trusted corpus.
