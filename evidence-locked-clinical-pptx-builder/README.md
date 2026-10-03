# Evidence-Locked Clinical PPTX Builder v2.4.0

v2.4.0 adds an optional, content-locked `VISUAL_POLISH` stage
(`scripts/visual_polish/`): a rule-based restyle of a built deck with its own
blocking `VISUAL_POLISH_CONTENT_LOCK` gate. Slides that cannot be restyled
safely are left as built (`SKIPPED` / `SPLIT_REQUIRED`). See
`docs/visual_polish_protocol.md`.

v2.3.0 adds a source-derived scenario-to-DECIDE-prompt contract, stricter
prompt leakage and fragment checks, and an advisory case/reveal geometry
screen. The included DYS_2026 v1.5 PPTX is a design-only precanonical
reference. Clinical evidence and final visual/independent QA requirements
remain governed by `SKILL.md`.

A governed clinical-presentation workflow reconstructed from the completed MI Case-Based Presentation project rather than from a theoretical PowerPoint template.

## What changed in v2

v2.0.0 was the major rebuild from the MI workflow. v2.1.0 is a backward-compatible minor release that validates the skill against the later final low-resource MI artifact and turns the Codex-stage lesson into enforceable gates. It strengthens independent visual QA from a prose preference into an operational certification gate, adds a structured independent-review manifest, requires domain-complete visual-review ledgers, and adds final-artifact regression reports/fixtures.

v2.1.1 is a focused hardening patch: package manifests no longer self-reference, immediate lineage metadata is corrected, independent-QA policy is represented by one enum, and only validated structured JSON can produce `INDEPENDENT_QA_CERTIFIED`. No clinical workflow or frozen MI content is rebuilt.

**v2.2.0** introduced the dyslipidemia semantic-integrity architecture. **v2.2.1** is the focused implementation-hardening patch: it adds a true source→inventory certification gate, rejects waivers on every non-independent promotion gate, blocks every unresolved CRITICAL/HIGH defect by default, fixes blank-node accounting, replaces dynamic footnote columns with one-row-per-binding records, distinguishes bibliographic citations from clinical numbers, requires approved locked-source support for clinical repairs, and excludes runtime/test caches from release packages.

## Operating modes

`INSPECT`, `PATCH`, `BUILD_STANDARD`, `BUILD_CASE_BASED`, `CORPUS_BUILD`, `DERIVATIVE_BUILD`, `VISUAL_QA`, `VISUAL_POLISH`, `FINAL_RELEASE`, `MAINTENANCE`.

The assistant should state the selected mode and reason before execution.

## Two pipelines

**Pipeline A — Evidence / Case Corpus**  
locked sources -> independent source-structure/recommendation census -> source-recommendation inventory -> SOURCE_INVENTORY_CERTIFICATION -> exhaustive decision nodes -> SOURCE_EXTRACTION_COMPLETENESS -> extraction audit -> reconciliation -> candidate cases -> case audit/deduplication/coverage -> frozen Master Case Library -> audience architecture -> storyboard/case mapping.

**Pipeline B — Presentation / Artifact**  
approved storyboard -> slide spec -> source-binding/prompt/repair semantic QA -> visual/notes plan -> PPTX -> clinical audit -> [optional content-locked visual polish] -> mechanical preflight -> 100% render -> 100% visual/projector QA -> repair -> full rerender/re-audit -> independent promotion.

## Installation

Upload the ZIP as a custom skill/package using the product's skill installation flow. `SKILL.md` is at package root. After installation, run `ACTIVATION_SMOKE_TEST.md` in a fresh chat.

## Final clinical release rule

For final/canonical clinical decks, contact-sheet review is not enough. When rendering is technically possible, every slide must be rendered and individually reviewed; after material repair, the final PPTX must be fully rerendered and re-audited. If renderer/font fidelity is unavailable, return `RENDER-UNCERTIFIED` rather than claiming PASS.

For high-stakes/final clinical decks, `independent_visual_qa_policy` defaults to `required_unless_explicit_user_waiver`. Structured JSON is required for `INDEPENDENT_QA_CERTIFIED`. If unavailable and not explicitly waived, use `INDEPENDENT-QA-UNCERTIFIED`; an explicit waiver records `INDEPENDENT_QA_WAIVED` with certification `NOT_CERTIFIED`. Markdown/free-text reviews are non-certifying.

## Deterministic support tools

The scripts do not replace clinical judgment. They enforce state, provenance, independent source→inventory certification, inventory→extraction completeness, downstream coverage, recommendation-boundary checks, footnote binding, source-section attribution, prompt leak/coherence controls, normalization fidelity, repair fidelity, correction scope, case fingerprints, PPTX structure/bounds/font floors/notes, render coverage, semantic promotion blocking, canonical hashes and archive integrity.

Run tests:

```bash
python -m pytest -q
```

## Reference implementation

`docs/actual_mi_workflow_reconstruction.md` and `docs/mi_regression_mapping.md` show how the skill maps to the frozen MI project: two sources -> 508 frozen source nodes -> 493 provisional cases -> 481 final cases -> audience/16-module architecture -> 78 live anchors -> 39 storyboard units -> 137-slide Master -> live/derivative/advanced/reference/index products -> audit/repair/promotion -> closure.

Those MI counts are regression evidence, not hard-coded requirements for new projects.
