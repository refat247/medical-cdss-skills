# Migration Notes — v1.0.0 -> v2.1.0

## Proven predecessor

The proven predecessor is `evidence-locked-clinical-pptx-builder v1.0.0` from `evidence-locked-clinical-pptx-builder-v1.0.0.zip`.

## Retained

- evidence locking and no-invention principle;
- stateful/resumable work;
- decision-node -> case -> architecture -> spec -> build concept;
- canonical hash guard, manifest and closure packaging;
- speaker-note presence audit;
- slide/case indexing;
- derivative reuse rather than restarting research;
- canonical immutability and maintenance mode.

## Reworked / expanded

- lifecycle state and task mode are now separate;
- source registry supports correction/erratum and non-clinical context classes;
- extraction completeness and recommendation-table accounting are explicit;
- case deduplication/coverage are first-class gates;
- slide specification and provenance chain are validated;
- final visual QA is enforceable through render and per-slide review ledgers;
- projector/UI/UX and independent visual QA are explicit release domains;
- derivative integrity uses case fingerprints;
- failures can produce RENDER-UNCERTIFIED rather than false PASS.

## Breaking migration actions

1. Copy v1 state to a new file; do not overwrite canonical project records.
2. Set `schema_version: 2`.
3. Add `mode`, `pipelines`, `release_policy`, `correction_policy`, `visual_qa_policy` and `context_sources` sections.
4. Map old completed work items to v2 pipeline states; do not rerun frozen clinical work unless a specific defect requires it.
5. For already-canonical decks, record historical visual-certification evidence if available; otherwise mark that historical release as `legacy-canonical` rather than pretending a new 100% visual audit occurred.
