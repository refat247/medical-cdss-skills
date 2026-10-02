# v2.2.0 Hardening Report

## Architecture changes

1. Source-native recommendation inventory precedes decision-node extraction certification.
2. `SOURCE_EXTRACTION_COMPLETENESS` is independent from downstream node coverage.
3. Source-boundary, footnote-binding and source-hierarchy ledgers are explicit artifacts.
4. CASE/DECIDE prompts receive deterministic leak/coherence checks plus mandatory semantic comparison.
5. Source text uses explicit exact/normalized/paraphrase policy.
6. Every repair receives an authority/fidelity record.
7. CRITICAL/HIGH semantic defects are machine-counted and canonical-promotion blocking.

## Code changes

Added:
- `scripts/source_inventory_completeness.py`
- `scripts/recommendation_boundary_validator.py`
- `scripts/footnote_binding_validator.py`
- `scripts/source_section_validator.py`
- `scripts/prompt_semantics_validator.py`
- `scripts/normalization_fidelity_validator.py`
- `scripts/repair_fidelity_validator.py`
- `scripts/semantic_promotion_gate.py`

Added schemas/templates for source recommendation inventory, extraction accounting, marker/footnote binding, prompt semantic review, text normalization, repair fidelity and semantic defects.

Updated `SKILL.md`, `README.md`, `CHANGELOG.md`, `templates/project_state.yaml`, release metadata and regression tests.

## Regression fixtures

`fixtures/dyslipidemia_regression/fixture_map.csv` maps all 15 requested dyslipidemia failure classes to validator, expected failure, severity and required repair/adjudication. The full dyslipidemia deck is not packaged as a routine fixture.
