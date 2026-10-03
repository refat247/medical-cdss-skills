# Changelog

## 2.4.0 - 2026-10-02

- Added `VISUAL_POLISH` mode and `scripts/visual_polish/` (`polish.py`, `style.py`,
  `verify.py`): a content-locked, rule-based restyle of an already-built deck,
  run after `clinical_provenance_audit` and before `automated_preflight`.
- Added the `VISUAL_POLISH_CONTENT_LOCK` gate: slide identity/order/layout,
  verbatim text (multiset), no non-token additions, speaker notes, byte-identical
  layout/master/theme parts, font floors, independent fit re-measurement, and
  the repo's own `pptx_preflight`. It also writes the render manifest and a blank per-slide visual-review ledger.
- Fail-closed outcomes: `SKIPPED` (unrecognised structure) and `SPLIT_REQUIRED`
  (cannot fit at the floor). Both leave the slide byte-identical to the build.
- Profiles: `projector_default` (section 17 floors) and opt-in `dense_case_reveal`
  (DYS_2026 v1.5 density; owner approval required and validated in project state).
- Design semantics: amber DECIDE / green SOURCE REVEAL with icon cues; ACC/AHA
  COR colour pills; compound COR/LOE codes split into separate pills; uniform body size per slide.
- `semantic_promotion_gate.py` now requires `visual_polish_content_lock = PASS`
  whenever `visual_polish_applied` is true. It cannot be waived.
- `project_state.yaml`: new `visual_polish` state and `release_policy.visual_polish`
  block. `validate_project.py` enforces the profile approval.
- `mode_router.py` routes beautify/polish/restyle requests to `VISUAL_POLISH`.
- `case_reveal_layout_gate.py`: the hard-coded `C:/Windows/Fonts/arialbd.ttf` was replaced
  with a portable metric-font lookup (it previously crashed off Windows).
- Added a synthetic fixture deck and 21 regression tests (110 total).
- No clinical source, frozen artifact or design-reference deck changed. Backward compatible.

## 2.3.0 - 2026-10-02

- Added a source-derived scenario and neutral DECIDE question contract, with
  deterministic checks for metalanguage, recommendation leakage, fragments,
  short stems, and scenario/prompt drift.
- Added an advisory case/reveal layout screen for titles, badges, card bodies,
  and footer geometry; rendered slide-by-slide review remains mandatory.
- Included the exact user-preferred DYS_2026 v1.5 precanonical PPTX as a
  design-only reference, without promoting its clinical content or QA status.
- Kept legacy prompt ledgers readable; new projects use the expanded template.
- No clinical source, baseline deck, selected deck, or original skill ZIP changed.

## 2.2.1 — 2026-09-29

### Patch release: fail-closed semantic enforcement hardening
- Added independent `SOURCE_INVENTORY_CERTIFICATION` before decision-node extraction; source census and inventory generation must be independent or explicitly semantically adjudicated.
- Fixed semantic promotion so every non-independent required gate rejects `WAIVED`; only independent visual QA may use a policy-governed explicit waiver.
- Changed CRITICAL/HIGH promotion logic to fail closed for every defect family, including previously unseen families.
- Fixed extraction accounting so `EXTRACTED` with a blank decision node fails; explicit non-node dispositions require reason, reviewer and completed semantic review.
- Replaced dynamic footnote-marker columns with a one-row-per-recommendation-footnote binding model; legacy v2.2.0 ledgers remain readable.
- Fixed normalization fidelity so bibliographic citation-number removal can pass while thresholds, doses, units, percentages, ages/durations, COR/LOE, operators, markers and negation remain protected.
- Fixed repair authority: user instruction alone cannot validate a clinical factual mutation; clinical changes require verified support from a currently approved locked source.
- Excluded `.pytest_cache/`, `__pycache__/`, `*.pyc`, and `*.pyo` from manifests and release ZIPs.
- Reordered project state to: evidence lock → source census → source inventory → source inventory certification → decision-node extraction → source extraction completeness → extraction audit → reconciliation.
- Retained the 57 v2.2.0 tests and expanded the suite to 84 tests.
- Backward compatible; no frozen MI artifact or dyslipidemia deck modified.

## 2.2.0 — 2026-09-29

### Minor release: dyslipidemia semantic-integrity hardening
- Added `SOURCE_EXTRACTION_COMPLETENESS` independent of downstream node coverage; detects missing/duplicate source recommendation accounting including the 130/131 failure class.
- Added source-recommendation boundary validator with fail-closed semantic review for headers/DOIs/page strings, neighbouring headings, unrelated tables/figures and cross-recommendation spill.
- Added explicit marker/footnote binding ledger and validator.
- Added source-section/source-table attribution validator separating source-native hierarchy from editorial deck modules.
- Added CASE/DECIDE prompt leak/coherence validator plus mandatory semantic comparison status.
- Added text-handling policies `SOURCE_NATIVE_EXACT`, `SOURCE_NATIVE_NORMALIZED`, and `PEDAGOGIC_PARAPHRASE`, with protected-token validation.
- Added repair-fidelity ledger/validator so unsupported clinical/editorial repairs become auditable defects.
- Added severity-aware semantic promotion gate; unresolved CRITICAL/HIGH clinical/source-binding/completeness/prompt/repair defects block canonical promotion even if rendering or independent visual QA passes.
- Added 15 dyslipidemia regression fixtures and adversarial tests.
- Preserved MI-grade source locking, correction handling, case-corpus workflow, rendering/visual QA, independent QA, hashing/immutability, package closure, state and handoff behavior.
- Backward compatible; no frozen MI clinical project modified.

## 2.1.1 — 2026-09-29

### Patch release: package integrity + independent-QA enforcement hardening
- Fixed self-referential `PACKAGE_MANIFEST.md` generation; the output manifest now automatically excludes itself and includes a verifier for every listed size/hash.
- Corrected lineage metadata: immediate predecessor is v2.1.0, lineage origin is v1.0.0, major predecessor is v2.0.0, and `breaking_change` is false.
- Unified `independent_visual_qa_policy` to `required`, `required_unless_explicit_user_waiver`, or `optional`; high-stakes default is `required_unless_explicit_user_waiver`.
- Made structured JSON the only certifying independent-review format; Markdown/free-text is `NON_CERTIFYING_REPORT`.
- Hardened per-slide independent review: unique/full/in-range slide coverage, non-empty findings/status, explicit adjudication, clinical-adjudication block, accepted-repair mapping, repaired artifact/render hashes, second full render, and complete post-repair review.
- Aligned canonical promotion statuses with independent-QA certification/waiver and render certification.
- Added regression tests for manifest integrity, lineage metadata, policy defaults, waiver/fail-closed behavior, slide-row integrity, non-certifying text reports, adjudication, repair evidence, and post-repair certification.
- No frozen MI clinical artifact or evidence content changed.

## 2.1.0 — 2026-09-28

### Minor release: final MI artifact regression + Codex lesson integration
- Validated the skill against the later final low-resource/district-hospital MI derivative deck that was absent from the original v2.0.0 regression.
- Added actual final-artifact regression evidence: 65/65 slides rendered and 65/65 individually reviewed in a domain-complete visual ledger.
- Strengthened independent second-runtime visual QA: required for independent-QA-certified canonical status in high-stakes/final clinical decks.
- Added fail-closed independent QA states: `INDEPENDENT-QA-UNCERTIFIED` and `INDEPENDENT_QA_WAIVED`.
- Repaired `independent_review_gate.py` so a simple free-text PASS marker is insufficient and required-policy waivers cannot certify a deck.
- Repaired `render_qa_gate.py` to support render-set hashing, manifest output and required per-slide visual ledgers.
- Expanded `visual_review_ledger.py` with domain columns for projector readability, hierarchy, footer visibility, clipping/overflow, image/ECG legibility, density, case/reveal rhythm and local-constraint separation.
- Added regression fixtures and tests for structured independent review, waiver handling and domain-complete visual-review ledgers.
- Added final-artifact/Codex lesson reports and updated the independent visual-QA prompt template.

### Compatibility
- Backward compatible with v2.0.0 project-state concepts.
- No clinical-content schema change.
- No new clinical evidence or MI content mutation.

## 2.0.0 — 2026-09-28

### Major rebuild
- Reconstructed the skill from the actual completed MI project workflow.
- Added explicit mode router: INSPECT, PATCH, BUILD_STANDARD, BUILD_CASE_BASED, CORPUS_BUILD, DERIVATIVE_BUILD, VISUAL_QA, FINAL_RELEASE, MAINTENANCE.
- Split architecture into Evidence/Case Corpus and Presentation/Artifact pipelines.
- Added official correction/erratum and explicit supersession handling.
- Added typed operational/local constraints and visual provenance classes.
- Expanded extraction requirements to recommendation tables, narrative nodes, figures/algorithms, thresholds, doses, contraindications, exceptions, special populations, explanatory-only nodes and completeness accounting.
- Added dedicated extraction audit/repair/re-audit contract and arithmetic reconciliation.
- Added case deduplication dispositions and coverage gates.
- Added audience/teaching architecture and storyboard/case-mapping schemas.
- Added speaker-note evidence-lock contract.
- Added derivative clinical-fingerprint integrity checks.
- Replaced weak visual certification with mandatory 100% final-render review when technically possible.
- Added `RENDER-UNCERTIFIED` state when renderer/font fidelity is unavailable.
- Added independent second-pass visual QA handoff/gate with clinical-evidence isolation.
- Expanded projector/UI/UX acceptance rules and repair order.
- Added visual review ledger, render coverage gate, correction validator, reconciliation validator, slide-spec validator, clinical lint, derivative integrity and richer PPTX preflight.
- Added five example project configurations and representative regression fixtures.
- Added MI read-only regression mapping, adversarial audit, repair report and final re-audit report.

### Breaking changes in v2.0.0
- `project_state.yaml` schema moved from v1 to v2.
- Modes became explicit and distinct from project lifecycle state.
- `FINAL_RELEASE` requires render-certification evidence; structural PASS alone is insufficient.
- Correction/erratum projects require explicit scope mapping.
- Canonical promotion records independent visual QA status or waiver.

## 1.0.0 — 2026-09-23
- Initial evidence-locked/stateful clinical presentation workflow distilled from the MI project.
