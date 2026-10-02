# Architecture

## Separation of responsibilities

### Deterministic layer
- copy/hash source
- render slides
- extract text/tables/notes
- detect duplicates
- allocate timing
- validate JSON contracts
- build DOCX
- inject PPTX notes
- reopen/render verification
- QA status computation

### Model reasoning layer
- whole-deck narrative analysis
- slide semantic briefs
- spoken script generation
- semantic coverage judgement
- claim-to-source review

This separation prevents fluent prose from bypassing file-safety and artifact-validation gates.

## Project artifact model

```text
project/
  source/
  slides/
  deck_manifest.json
  preflight_report.json
  deck_analysis.json
  slide_briefs.json
  timing_plan.json
  scripts.json
  validation_report.json
  clinical_lint.json
  final/
    rehearsal.docx
    live-presenter.docx
    *_WITH_SPEAKER_NOTES.pptx
  qa/
  quality_report.json
  quality_report.md
```
