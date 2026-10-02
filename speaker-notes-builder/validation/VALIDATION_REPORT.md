# Validation Report — Speaker Notes Builder v1.0.0

**Validation time:** 2026-09-07 17:42 BDT (UTC+06:00)  
**Scope:** engineering release validation, Tirzepatide PDF regression inspection, DOCX presenter-companion render QA, and synthetic PPTX notes injection.

## Executive status

| Gate | Result |
|---|---|
| Python unit/integration tests | **PASS — 7/7** |
| Python source compile | **PASS** |
| Wheel build | **PASS** using installed build backend (`--no-build-isolation`) |
| Wheel resource packaging | **PASS** — JSON schemas present inside wheel |
| CLI load/help from installed wheel target | **PASS** |
| Tirzepatide source inspection | **PASS** |
| Duplicate-page detection | **PASS** — page 31 correctly matched page 30; sparse divider false positives repaired |
| Duplicate disposition | **PASS** — page 31 explicitly excluded from the 30-page presenter validation run |
| Deck/script structural validation | **PASS** |
| Clinical claim ledger validation | **PASS** |
| Clinical deterministic lint | **PASS** |
| Rehearsal DOCX build | **PASS** |
| Rehearsal DOCX render/pagination | **PASS — 30 expected / 30 rendered pages** |
| Live-presenter DOCX build | **PASS** |
| Live-presenter DOCX render/pagination | **PASS — 30 expected / 30 rendered pages** |
| Rendered-page boundary audit | **PASS** — no blank pages or out-of-page text blocks in either 30-page PDF render |
| Visual overview inspection | **PASS** — all 60 rendered presenter pages reviewed in 5-page contact sheets; no obvious clipping, overlap, missing slide images, or caution-box failures observed |
| Synthetic PPTX notes injection/reopen mapping | **PASS** |
| Exact original Tirzepatide PPTX notes injection | **NOT TESTED** — current regression attachment was PDF, not the original PPTX |
| Manual Work Mode ZIP import | **NOT TESTED / UI-SCOPE UNVERIFIED** |

## Tirzepatide regression evidence

Source used during validation:

- file: `CME_TIRZEPATIDE_COMBINED_PPTX_V4_FINAL_ggogle_slide.pdf`
- SHA-256: `268a2af92d6a8f91784290e976d251ec33d5ba6da2a3d535eac17daff2de5f8d`
- source pages: **31**
- unique presenter pages after explicit duplicate disposition: **30**

Duplicate detection initially produced false positives on visually similar sparse divider slides when perceptual image hash alone was used. The root cause was insufficient duplicate evidence. The detector was repaired to require either byte-identical raster output or a near-identical perceptual hash **plus >=0.96 normalized text similarity**. Re-test then identified only the true terminal duplicate:

- slide/page 31 -> duplicate of slide/page 30
- perceptual Hamming distance: 0
- normalized text similarity: 1.0

This failure and correction were preserved rather than hidden.

## Clinical/CME regression

The validation project used `profile=clinical_cme` and `source_mode=strict`.

The source deck's Bangladesh/DGDA caveat was preserved in the validation scripts and claim ledger. A 32-entry high-risk claim ledger was generated for the validation fixture. Final deterministic clinical lint returned:

- blockers: 0
- warnings: 0
- status: **PASS**

A prior lint false positive on the phrase `DGDA-authorized supply` was detected. Root cause: the local-approval regex was too broad and treated supply authorization wording as equivalent to a claim that the drug/indication was approved in Bangladesh. The regex was narrowed to explicit local approval/licensing constructions (for example, `approved in Bangladesh`, `approved by DGDA`, `DGDA-approved`). Re-test passed.

## DOCX artifact verification

Two 30-page presenter companions were generated from the regression project:

- rehearsal edition
- live-presenter edition

Both were converted to PDF by LibreOffice and rasterized to page PNGs. The verifier confirmed exact 30/30 pagination against the included script count. A page-boundary audit using PyMuPDF found:

- blank pages: 0
- text blocks outside page bounds: 0

All 60 rendered pages were visually reviewed through six 5-page contact sheets per edition. The review found no obvious overflow, clipping, image loss, caution-box breakage, or unintended extra pages.

## PPTX notes injection verification

The integration suite creates a synthetic 2-slide PPTX, injects only each slide's `main_script` into the PowerPoint Notes pane, reopens the output, and checks:

- slide count unchanged;
- source file not overwritten;
- notes map exactly to slide 1 and slide 2;
- injected text equals expected `main_script`.

Result: **PASS**.

## Packaging validation

The first wheel-build attempt used default PEP 517 build isolation. That attempt failed because the sandbox had no network access to fetch the requested build dependency index. The failure was contained and the build was rerun with `--no-build-isolation`, using the already installed build backend. The wheel then built successfully.

The final wheel was installed into an isolated target directory and the CLI loaded successfully. Packaged JSON schemas, including `claim_ledger.schema.json`, were confirmed present inside the wheel.

## Remaining scope limits

1. **Manual Work Mode import is UNVERIFIED.** The ZIP is structured with `SKILL.md` at its root and includes `WORK_MODE_QUICKSTART.md`, but this environment cannot prove the exact skill-import UI behavior of the user's client.
2. **Exact Tirzepatide PPTX injection is UNVERIFIED.** Only the PDF version of the current deck was available for this release regression. The injection mechanism itself is verified on a synthetic PPTX.
3. **Clinical correctness remains source-dependent.** Engineering PASS does not convert stale, missing, or jurisdiction-inappropriate source material into verified clinical truth. The skill's claim ledger and lint gates are controls, not substitutes for current authoritative source review.

## Release conclusion

**ENGINEERING RELEASE STATE: PASS**  
**WORK MODE MANUAL-IMPORT STATE: UNVERIFIED**  
**EXACT TIRZEPATIDE PPTX-INJECTION STATE: UNVERIFIED**

The package is suitable for manual upload/use as a reusable skill, with the scope limits above disclosed.
