# Speaker Notes Builder v1.0.0

A reusable Work/agent skill for turning an existing PPTX or PDF deck into deck-aware, timed, evidence-bounded speaker notes plus polished presenter companion documents.

## What it builds

- Rehearsal DOCX: slide preview + delivery intent + main script + emphasis + transition + caution + short-on-time fallback.
- Live presenter DOCX: low-cognitive-load slide preview + main script + concise cues.
- Optional PPTX with clean `main_script` injected into each slide's Notes pane.
- Machine-readable deck manifest, timing plan, validation results, and QA report.

## Why this is not a prompt wrapper

The workflow separates deterministic file handling from model reasoning:

1. source copy and hash
2. slide rendering and extraction
3. deck-level narrative analysis
4. per-slide semantic inventory
5. clinical high-risk claim ledger when enabled
6. weighted timing allocation
7. three-layer script authoring
8. clinical/regulatory lint when enabled
9. DOCX/PPTX build
10. render/reopen verification
11. explicit certification status

## Install

Python 3.11+ recommended.

```bash
python -m pip install -e .
```

External render tools used when available:

- LibreOffice / `soffice`
- Poppler / `pdftoppm` (optional; PyMuPDF is used by default for PDF rasterization)

## Quick start

```bash
python -m speaker_notes_builder.cli inspect --input deck.pptx --project ./run --profile clinical_cme
python -m speaker_notes_builder.cli allocate --project ./run --talk-minutes 15 --qa-minutes 2
```

Then use the model to author `deck_analysis.json`, `slide_briefs.json`, and `scripts.json` according to the schemas and `SKILL.md`.

```bash
python -m speaker_notes_builder.cli validate --project ./run
python -m speaker_notes_builder.cli clinical-lint --project ./run
python -m speaker_notes_builder.cli build-docx --project ./run --mode rehearsal
python -m speaker_notes_builder.cli build-docx --project ./run --mode live
python -m speaker_notes_builder.cli verify-docx --project ./run --docx ./run/final/rehearsal.docx --output-dir ./run/qa/rehearsal-render
python -m speaker_notes_builder.cli qa --project ./run
```

If the source is PPTX and embedded notes are desired:

```bash
python -m speaker_notes_builder.cli inject --project ./run --output ./run/final/deck_WITH_SPEAKER_NOTES.pptx
python -m speaker_notes_builder.cli verify-pptx --project ./run --pptx ./run/final/deck_WITH_SPEAKER_NOTES.pptx
```

## Clinical/CME profile

`clinical_cme` defaults to strict source-bounded behavior. It flags high-risk wording around dosing, indications, contraindications, pregnancy, paediatrics, boxed warnings, comparative efficacy, regulatory approval, and jurisdiction-specific claims.

This is an **authoring/QA control**, not a substitute for clinician review or current local product information.

## Release status

v1.0.0 engineering validation includes:

- unit tests for duplicate detection, timing reconciliation, clinical lint, DOCX generation, and PPTX note injection;
- a deterministic inspection run against the 31-page Tirzepatide CME PDF used during development;
- successful detection of the duplicate terminal reference page in that PDF;
- synthetic PPTX note-injection and reopen validation;
- DOCX render verification using LibreOffice/PyMuPDF.

Not verified in this environment: manual import into the user's Work Mode UI and note injection into the exact original Tirzepatide PPTX (the current development attachment was PDF).

See `validation/VALIDATION_REPORT.md`.
