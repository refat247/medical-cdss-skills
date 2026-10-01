# Changelog

All notable changes to the `cdss-unicode-mojibake-guard` skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.6.0] - 2026-10-01

### Changed
- fix: protected directories are skipped with their subdirectories; UTF-16/32 and binary files are never rewritten; --dry-run; ISMP 'U' rule no longer rewrites U.S./U-wave; Q.D./I.U. with trailing dot handled; lab denominators like g/24 h kept; ion charges and isotopes no longer become citation brackets; file names and currency pairs left alone; 15 more mojibake sequences repaired and flagged (minus sign, approx, Greek, fractions, bullets, accents). SKILL.md/README corrected.

## [1.5.2] - 2026-09-25

### Fixed
- Legacy-corruption pattern now also catches the spaced forms 'mcg g' and 'mcg mol' (from LaTeX \mu g / \mu mol); 243 such values in Kumar & Clark were passing the audit

## [1.5.1] - 2026-09-25

### Changed
- audit_directory and fix_directory skip non-text folders (assets, figures, pages, images, __pycache__) so whole-package audits finish; test proves planted corruption in those folders is not scanned or rewritten

## [1.5.0] - 2026-09-25

### Changed
- fix is now source-safe: repairs encoding damage to the original characters (Âµg -> µg) and keeps printed text/LaTeX verbatim; gate blocks only real corruption (mojibake, invisible chars, mcgmol/mcgg/109/L/fraction-slash legacy corruption); raw µg and LaTeX are non-blocking advisories normalised in output only; output LaTeX powers of ten render as superscripts (10^{9} -> 10⁹)

## [1.4.0] - 2026-09-25

### Changed
- Claude audit fixes: source text kept verbatim (fix no longer rewrites doses/lab values); ISMP dose rewrites only in generated output (cleanroom, sanitize_for_llm, sanitize --rewrite-doses) and limited to dose units; ISMP issues are non-blocking audit advisories; legacy mcgmol/109/L corruption is blocking; audit/gate --include-outputs

## [1.3.2] - 2026-09-25

### Changed
- Safely decode mixed UTF-8 and CP1252 bytes via surrogateescape without corrupting Greek letters or superscripts; protect currency amounts in LaTeX de-delimiter; enforce ISMP trailing zeros, leading decimals, QD, and units

## [1.3.1] - 2026-09-25

### Changed
- Fix lone LaTeX \mu converting to micro prefix instead of mcgmol, reorder LaTeX cleanroom before ISMP, support prefix-based _CHECKPOINT.json directory protection, and add CP1252 0xB5 fallback decoding.

## [1.3.0] - 2026-09-25

### Changed
- ### Fixed
- Replaced dangerous Unicode NFKC normalization with NFC + safe typographic ligature mapping to protect superscripts (e.g. 10⁹/L) and fractional dosing.
- Fixed unit corruption where 'Âµ' corrupted 'Âµmol/L' into 'mcgmol/L'; only micrograms are converted to 'mcg'.
- Preserved clinical approximation tilde ('~5%') by removing unconditional tilde stripping.
- Restricted LaTeX subscript cleaner to explicit braces or digit-only indices to protect snake_case identifier words (e.g., 'drug_dosing').
- Handled LaTeX microgram syntax: \mu g, \mu\text{g}, \mu\mathrm{g} -> mcg.
- Prevented fix_directory from mutating protected RAG pipeline outputs, checkpoints, and trust status markers.
- Added non-zero exit code to audit command on violations.

## [1.2.0] - 2026-09-20

### Changed
- Add Layer 8 Clinical Math & Physics Normalizer and cleanroom-docx export filter

## [1.1.0] - 2026-09-20

### Added
- **Layer 7: Clinical LaTeX & Pseudo-Math De-Delimiter**:
  - Implemented `clean_clinical_latex()` to automatically de-delimit OCR-injected and LLM-generated LaTeX math markers.
  - Heart sounds (`$S_1$`, `$S_2$`, `$S_3$`, `$S_4$`, `\(S_1\)`) converted to standard clinical ASCII (`S1`, `S2`, `S3`, `S4`).
  - Valve split components (`$A_2$`, `$P_2$`, `$OS$`) converted to standard clinical ASCII (`A2`, `P2`, `OS`).
  - Clinical intervals (`$A_2\text{--}OS$`) converted to standard clinical ASCII (`A2-OS`).
  - Inequalities (`$\ge$`, `$\le$`, `\geq`, `\leq`, `\pm`) converted to standard plain text (`>=`, `<=`, `+/-`).
  - Stripped TeX hyphens (`\text{--}`, `\text{---}`) to standard dashes (`-`, ` - `).
- Added `--clean-latex` CLI flag (enabled by default in `fix` and `sanitize` commands).
- Added comprehensive unit tests in `tests/test_guard.py` covering Layer 7 de-delimiter and SemVer assertion.

### Changed
- Integrated `clean_clinical_latex()` directly into `sanitize_for_llm(enforce_ismp=True, clean_latex=True)`.
- Updated `audit_directory()` and `fix_directory()` to detect and de-delimit raw OCR LaTeX patterns across medical corpora.
- Declared `__version__ = "1.1.0"` in `scripts/guard.py`.

### Fixed
- Fixed unrendered LaTeX math tokens and pseudo-mojibake persisting in generated CDSS clinical notes.
- Ingestion-time bulk repair of 295 contaminated files in `D:\01_Medical_Study\CDSS_Retrieval_Package`.

## [1.0.0] - 2026-09-14

### Added
- Initial production release of `cdss-unicode-mojibake-guard`.
- **Layer 1**: Windows Console PEP 540 UTF-8 environment enforcement (`enforce_utf8_environment`).
- **Layer 2**: Double-encoded CP1252 to UTF-8 mojibake repair map (`repair_mojibake`).
- **Layer 3**: Unicode NFKC canonicalization (`unicodedata.normalize`).
- **Layer 4**: Invisible token-breaker stripping (zero-width spaces `\u200b`, BOM `\ufeff`, soft hyphens `\u00ad`).
- **Layer 5**: ISMP & FDA clinical symbol safety canonicalization (`µg` -> `mcg` overdose prevention, `≥` -> `>=`, `°C` -> `deg C`).
- **Layer 6**: Unicode-safe JSON serialization (`safe_json_dumps` with `ensure_ascii=False`).
- CLI tool (`scripts/guard.py`) supporting `audit`, `fix`, `gate`, and `sanitize` commands.
- Pre-flight blocking gate for CDSS automated pipelines.
- Unit test suite in `tests/test_guard.py`.
