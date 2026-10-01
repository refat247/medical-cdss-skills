# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-10-01

### Changed
- Bare modality flags (--never-events, --sbar, --anki-deck, --causal-graph, --patient-leaflet) now show everything instead of substring-matching 'all' (the toxic-drug matrix showed a fraction); --workspace is forwarded to the navigator via CDSS_HABIJABI_ROOT and child exit codes propagate; pipeline tools run as subprocesses with a per-stage status table (missing/failed stages are reported, no false 'completed successfully'); POSIX default workspace no longer a literal 'D:' directory; --clinician-name/--series-name recorded.

## [1.1.0] - 2026-09-26

### Added
- Seven extended clinical and educational modalities:
  1. Clinical OSCE Visual Spotters (`--visual-spotter`): Interactive spot-diagnosis stations with decoupled clinical media, questions, and keys.
  2. Residency Progression Curriculum (`--curriculum`): Tier 1 (Intern), Tier 2 (MO/GP), and Tier 3 (FCPS/MRCP) competency framework.
  3. GraphRAG Causal Knowledge Graph (`--causal-graph`): Causal pathophysiological triplet network and query engine.
  4. Inpatient Ward SBAR Handovers (`--sbar`): Acute emergency on-call handover cards for night duties.
  5. Bengali Patient Health Literacy Leaflets (`--patient-leaflet`): Culturally grounded patient education sheets using folk allegories.
  6. High-Yield Anki Cloze Decks (`--anki-deck`): Turnkey spaced-repetition flashcards (.tsv) for exam preparation.
  7. Ward Pharmacovigilance & Never-Events Matrix (`--never-events`): Tabular reference of lethal drug combinations, toxicity mechanisms, and safe alternatives.
- Automated pipeline stage `extended-modalities` integrated into `--pipeline auto`.
- Standalone multi-folder manufacturing engine `scripts/generate_extended_modalities.py`.
- Unit test suite for zero-drift version verification (`tests/test_version_consistency.py`).

### Changed
- Expanded runtime engine from 6 to 13 clinical modalities.
- Upgraded orchestrator CLI dispatcher to handle all extended modalities natively.
- Standardized directory architecture extended with `OSCE/`, `CURRICULUM/`, `GRAPH/`, `SBAR_HANDOVERS/`, `PATIENT_LEAFLETS/`, `ANKI/`, and `PHARMACOVIGILANCE/`.

## [1.0.0] - 2026-09-26

### Added
- Initial production release of `clinical-preceptor-cdss-orchestrator`.
- Universal 12-directory workspace pre-scaffolding engine (`--init-workspace`).
- 7-stage autonomous manufacturing pipeline for physician SingleFile HTML archives.
- Six core runtime modalities:
  1. Socratic Ward Preceptor (`--preceptor`)
  2. Postgraduate Exam SBA Generator (`--exam-sba`)
  3. Bedside Prescribing Safety Interceptor (`--prescribing-safety`)
  4. Federated 4-Textbook Cross-Grounding (`--federated`)
  5. Tropical & Resource-Constrained Ward Calculator (`--tropical-calc`, `--ward-facilities`)
  6. Hybrid Bilingual Semantic Retrieval Engine (`--search`)
- Strict clinical governance rules: fail-closed safety, temporal awareness, and evidence class segregation.
