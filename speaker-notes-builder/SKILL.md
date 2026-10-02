---
name: speaker-notes-builder
description: Build evidence-bounded, deck-aware speaker notes from PPTX/PDF; create rehearsal/live presenter DOCX companions; optionally inject clean notes back into PPTX; verify mapping, timing, clinical safety, and rendered artifacts.
version: 1.0.0
---

# Speaker Notes Builder

Use this skill when the user asks to create, rewrite, audit, time, format, or inject speaker notes for a presentation.

## Operating principle

Do **not** treat slides as independent prompts. Work in this order:

`SOURCE LOCK -> PREFLIGHT -> RENDER -> DECK ANALYSIS -> SLIDE SEMANTIC INVENTORY -> TIMING -> SCRIPT GENERATION -> SAFETY/CLAIM REVIEW -> COVERAGE AUDIT -> DOCX/PPTX BUILD -> RENDER/REOPEN VERIFY -> REPORT`

The visible slide plus approved source material are the content authority. Do not silently add external facts unless the user explicitly authorizes research/verification.

## Required output states

Keep these states distinct:

`DISCOVERED -> ANALYZED -> WRITTEN -> BUILT -> TESTED -> VERIFIED`

Never report `VERIFIED` solely because a file was created.

Final certification is one of:

- `PASS` — all required gates passed.
- `PASS_WITH_WARNINGS` — artifact gates passed; non-blocking content/jurisdiction warnings remain.
- `FAIL` — a required gate failed.
- `UNCERTIFIED` — a required check could not be executed.

## Source modes

- `strict`: use only the deck, existing notes, and user-provided sources. Default for clinical/CME.
- `explanatory`: may add non-factual explanation, analogies, and transitions; no new external factual claims.
- `research_enhanced`: external facts may be added only when the user explicitly requests research/verification and sources are tracked.

If the user says “use only this deck/file/project,” remain in `strict` mode.

## Profiles

### default
General professional presentations.

### clinical_cme
Use for medical, pharmaceutical, clinical, patient-safety, CME, guideline, therapeutic, diagnostic, or regulatory presentations.

In `clinical_cme` mode:

1. Treat these as high-risk claims: dose, route, frequency, titration, indication, age cut-off, contraindication, pregnancy/lactation, interaction, boxed warning, comparative efficacy, mortality/MACE, procedural/anaesthesia advice, regulatory approval, paediatric use, and off-label use.
2. Classify substantive claims as one of:
   `SUPPORTED`, `EXPLANATORY_ONLY`, `SOURCE_PARTIAL`, `SOURCE_CONFLICT`, `JURISDICTION_SENSITIVE`, `UNVERIFIED`, `BLOCKED`.
3. Never convert a foreign-label statement into a local approval claim without local-label evidence.
4. Never invent studies, guidelines, indications, doses, contraindications, safety conclusions, or treatment recommendations.
5. If a high-risk claim cannot be grounded, preserve the uncertainty in the spoken wording or block it.
6. Clinical caution metadata belongs in the rehearsal/live companion and audit report; only clean spoken prose belongs in PowerPoint notes.

## Workflow

### Step 1 — Create project and inspect

Never overwrite the source presentation.

```bash
python -m speaker_notes_builder.cli inspect \
  --input /path/to/deck.pptx \
  --project ./speaker-notes-project \
  --profile clinical_cme
```

For PDF input, the same command applies.

Expected artifacts:

- `source/source.*`
- `slides/slide-NNN.png`
- `deck_manifest.json`
- `preflight_report.json`

Duplicate pages are **flagged**, not silently deleted.

### Step 2 — Analyze the whole deck

Read `deck_manifest.json` and all rendered slide images in slide order. Create `deck_analysis.json` using `schemas/deck_analysis.schema.json`.

Freeze:

- purpose
- audience
- requested total talk time and Q&A reserve
- source mode
- narrative arc
- sections
- slide roles
- high-risk claims
- known gaps/conflicts

Do not write per-slide scripts before the deck-level analysis exists.

### Step 3 — Build slide briefs

Create `slide_briefs.json` using `schemas/slide_briefs.schema.json`.

For every slide, inventory:

- visible title/subtitle
- independent claims
- decisive numbers/trends
- charts/tables/relationships
- qualifiers/uncertainty
- citations/attribution that materially affect meaning
- slide role
- core message
- presenter job
- transition target
- risk level
- claim status

Coverage rule: every information-bearing element must be either:

- represented in narration,
- intentionally omitted with a reason, or
- marked unresolved.

### Step 4 — Build the clinical claim ledger when applicable

For `clinical_cme`, create `claim_ledger.json` using `schemas/claim_ledger.schema.json` and `prompts/claim_ledger.md`. Every high-risk spoken claim must have an explicit source trail and status. `UNVERIFIED` or `BLOCKED` high-risk claims must not survive into the final script.

### Step 5 — Allocate timing

```bash
python -m speaker_notes_builder.cli allocate \
  --project ./speaker-notes-project \
  --talk-minutes 15 \
  --qa-minutes 2
```

Timing is semantic-density weighted. Section dividers should not receive the same time budget as evidence, safety, dosing, or clinical-case slides.

### Step 6 — Generate three linked scripts

Create `scripts.json` using `schemas/scripts.schema.json`.

For each included slide generate:

- `main_script` — normal live delivery.
- `compressed_script` — short-on-time fallback; preserve the core claim and any safety-critical qualifier.
- `optional_expansion` — additional explanation if time permits.

Also generate presenter metadata:

- `delivery_intent`
- `key_emphasis`
- `pause_or_point`
- `transition`
- `estimated_seconds`
- `cautions`

Writing rules:

- Write natural spoken prose, not expanded bullets.
- Prefer proposition -> evidence/mechanism -> implication/bridge.
- Do not narrate slide furniture, colors, positions, page numbers, IDs, or decorative elements.
- For charts/tables, state the takeaway, decisive values/trend, comparison basis, implication, and material uncertainty; do not read every row/axis.
- Transition language should sound natural. Metadata may store a transition, but the spoken script should not say “Transition:”.
- Length follows semantic burden. Do not pad or delete meaning just to hit a sentence count.

### Step 7 — Run deterministic validation and clinical lint

```bash
python -m speaker_notes_builder.cli validate --project ./speaker-notes-project
python -m speaker_notes_builder.cli clinical-lint --project ./speaker-notes-project
```

Repair all blockers before building final artifacts.

### Step 8 — Build presenter companions

Rehearsal edition:

```bash
python -m speaker_notes_builder.cli build-docx \
  --project ./speaker-notes-project \
  --mode rehearsal
```

Live presenter edition:

```bash
python -m speaker_notes_builder.cli build-docx \
  --project ./speaker-notes-project \
  --mode live
```

Rehearsal pages may show:

- actual slide thumbnail
- slide number / section / timing
- delivery intent
- full main script
- key emphasis
- pause/point cue
- transition
- caution box
- compressed script

Live pages minimize cognitive load and prioritize:

- slide thumbnail
- main script
- emphasis cue
- compressed fallback
- next-slide bridge
- small timing marker

### Step 9 — Optional PPTX notes injection

Only if the user wants a PPTX with embedded notes and the source is PPTX:

```bash
python -m speaker_notes_builder.cli inject \
  --project ./speaker-notes-project \
  --output ./speaker-notes-project/final/deck_WITH_SPEAKER_NOTES.pptx
```

PowerPoint notes must contain **only `main_script` spoken prose**. Do not inject timing, confidence, audit labels, cautions, compressed/expansion scripts, or engineering metadata.

### Step 10 — Verify artifacts

DOCX:

```bash
python -m speaker_notes_builder.cli verify-docx \
  --project ./speaker-notes-project \
  --docx ./speaker-notes-project/final/rehearsal.docx \
  --output-dir ./speaker-notes-project/qa/rehearsal-render
```

Repeat for the live edition. Inspect every rendered page. Repair any clipping, overlap, missing glyph, broken image, or pagination defect; re-render after repairs.

PPTX:

```bash
python -m speaker_notes_builder.cli verify-pptx \
  --project ./speaker-notes-project \
  --pptx ./speaker-notes-project/final/deck_WITH_SPEAKER_NOTES.pptx
```

### Step 11 — Final QA report

```bash
python -m speaker_notes_builder.cli qa --project ./speaker-notes-project
```

Report exact state and unresolved items. Do not claim clinical correctness merely because engineering checks pass.

## Mandatory QA gates

1. Source copied; original hash preserved.
2. Slide/page count reconciled.
3. Duplicate pages detected and disposition explicit.
4. Every included slide maps to exactly one script record.
5. Every main script is non-empty.
6. Timing reconciles to the requested presentation window within configured tolerance.
7. Semantic coverage ledger has no unexplained omissions.
8. `clinical_cme`: no `BLOCKED`/unqualified jurisdiction-sensitive high-risk claim remains.
9. Rehearsal/live DOCX files reopen and render without visible defects.
10. Injected PPTX, when requested, reopens and preserves slide order/count; notes map exactly to source slides.
11. Source presentation is never overwritten.

## Deliverables

Default deliverables when the user asks for the complete workflow:

- `rehearsal.docx`
- `live-presenter.docx`
- optional `*_WITH_SPEAKER_NOTES.pptx`
- `speaker-script-main.md`
- `speaker-script-compressed.md`
- `speaker-script-optional-expansion.md`
- `quality_report.md`
- `quality_report.json`

Keep engineering intermediates in the project folder unless the user requests them.

## Failure handling

If a material failure occurs:

`DETECT -> CONTAIN -> IDENTIFY CAUSE -> CORRECT -> RE-RUN -> VERIFY -> PRESERVE EVIDENCE`

Do not silently discard failed artifacts or contradictory clinical evidence.
