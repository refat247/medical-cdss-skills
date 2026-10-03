# Package Tree — v2.4.0

The complete file inventory, byte sizes, and SHA-256 values are authoritative
in `PACKAGE_MANIFEST.md`. This release adds:

- `scripts/visual_polish/__init__.py`, `polish.py`, `style.py`, `verify.py`
- `docs/visual_polish_protocol.md`
- `fixtures/visual_polish/make_fixture.py` and `case_reveal_mini.pptx` (synthetic)
- `tests/test_v2_4_visual_polish.py`
- `VERSIONING_DECISION_v2.4.0.md`, `MIGRATION_NOTES_v2.3.0_to_v2.4.0.md`
- updated `SKILL.md`, `scripts/semantic_promotion_gate.py`, `scripts/validate_project.py`,
  `scripts/mode_router.py`, `scripts/case_reveal_layout_gate.py`, `templates/project_state.yaml`

Previous release (v2.3.0) additions:


- `docs/decide_prompt_contract.md`
- `docs/dys_2026_v1_5_design_reference.md`
- `scripts/case_reveal_layout_gate.py`
- updated `scripts/prompt_semantics_validator.py`
- updated prompt ledger template/schema and v2.3 regression tests
- `assets/design_references/DYS_2026_Master_Core_v1.5_VISUAL_REPAIR_PRECANONICAL.pptx`

Runtime caches and temporary test directories are excluded from the release.
