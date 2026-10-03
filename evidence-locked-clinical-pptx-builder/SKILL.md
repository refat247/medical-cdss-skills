---
name: evidence-locked-clinical-pptx-builder
description: Evidence-locked clinical presentation system with source/correction control, exhaustive decision-node and case-corpus workflows, standard/case-based/derivative modes, slide specification, speaker-note provenance, content-locked visual polish, full-render visual QA, independent promotion, modular indexing, closure, and maintenance governance.
metadata:
  version: 2.4.0
  schema_version: 3
---

# Evidence-Locked Clinical PPTX Builder

## 1. Operating Contract

Use this skill to inspect, patch, build, derive, audit, promote, or maintain clinical presentation products when evidence provenance and presentation quality matter. This is a **workflow system**, not a medical source.

At the beginning of every task, select and state one mode and the reason:

- `INSPECT` — audit an existing deck without editing.
- `PATCH` — bounded repair of an existing deck while protecting unaffected content.
- `BUILD_STANDARD` — conventional evidence-locked clinical deck; no exhaustive case corpus requested.
- `BUILD_CASE_BASED` — full MI-grade case-based workflow.
- `CORPUS_BUILD` — approved sources -> decision nodes -> audited/frozen Master Case Library.
- `DERIVATIVE_BUILD` — create a duration-, audience-, module-, or resource-specific product from frozen canonical artifacts.
- `VISUAL_QA` — render and visually audit an existing deck without changing clinical evidence.
- `VISUAL_POLISH` — restyle an already-built, clinically audited deck (presentation only) under the content-lock gate; see section 17A.
- `FINAL_RELEASE` — run all final acceptance gates and decide canonical promotion.
- `MAINTENANCE` — closed-project defect repair, source update, new derivative, accessibility change, or archive/export task.

Do not run the largest pipeline when a smaller mode satisfies the request. Do not silently switch modes after work begins; record any change in project state/handoff.

## 2. Authority Order

Use this authority order:

1. current `project_state.yaml` / current-state artifact;
2. evidence-lock/source register and correction/supersession register;
3. approved clinical source files;
4. frozen decision-node inventories, reconciliation records, Master Case Library, architecture, storyboard, and slide specification;
5. canonical product manifests/hashes;
6. current user instruction;
7. chat history only as supplementary context.

Never reconstruct project state only from conversational memory when project artifacts exist.

## 3. Two Coordinated Pipelines

### Pipeline A — Evidence / Case Corpus

`locked sources -> independent source-structure/recommendation census -> source-recommendation inventory -> SOURCE_INVENTORY_CERTIFICATION -> decision-node extraction -> SOURCE_EXTRACTION_COMPLETENESS -> extraction audit/repair/re-audit -> cross-source reconciliation -> candidate cases -> case fidelity/deduplication/coverage audit -> frozen Master Case Library -> audience prioritization -> teaching architecture -> anchor paths -> storyboard -> case-to-slide mapping`

### Pipeline B — Presentation / Artifact

`approved storyboard -> slide-level content specification -> semantic source-binding QA -> prompt semantic QA -> repair-fidelity QA -> visuals/source-figure plan -> speaker-note schema -> PPTX build -> clinical/provenance audit -> [optional VISUAL_POLISH + content lock] -> mechanical preflight -> 100% rendering -> 100% visual/projector/UI audit -> repair -> 100% rerender -> automated preflight again -> visual re-audit -> independent promotion decision`

Keep the pipelines separated so design work cannot mutate frozen clinical evidence and derivative decks can reuse the frozen corpus without restarting research.

## 4. Hard Evidence Boundary / No-Invention Engine

Before clinical work, create or validate an evidence contract with:

- approved clinical source IDs/files and role of each source;
- forbidden clinical sources;
- official correction/erratum sources if applicable;
- terminology/conflict rule;
- no-invention rule;
- audience/product intent;
- local or operational constraints classified separately from guideline evidence;
- visual-asset provenance classes;
- case-count philosophy.

Clinical recommendations, diagnostic rules, doses, thresholds, timing, contraindications, Class/LoE, and clinically meaningful explanations may come only from approved clinical sources unless the user explicitly expands the boundary.

Outside material must be typed as one of:

- `OPERATIONAL_CONTEXT` — local workflow/resource constraint supplied by user;
- `STYLE_REFERENCE` — non-clinical design inspiration;
- `OFFICIAL_SOURCE_FIGURE` — figure from an approved source;
- `USER_CLINICAL_IMAGE` — teaching asset, not automatically evidence;
- `EXTERNAL_ILLUSTRATIVE_VISUAL` — visual asset only;
- `MODEL_GENERATED_DECORATIVE` — non-diagnostic visual only.

None of these classes silently expands clinical evidence.

For every clinically meaningful statement, maintain traceability where applicable:

`source -> section/table/figure/page -> decision node -> reconciliation/conflict item -> case -> slide spec -> built slide -> speaker notes`.

Never “improve” a source with remembered clinical practice or model knowledge.

User instruction alone cannot authorize a clinical factual mutation inside a locked evidence boundary. Thresholds, doses, units, contraindications, COR/LOE, population criteria, polarity, terminology and other clinical-source changes require validated support from a currently approved locked source. To use a new clinical source, formally expand and relock the evidence boundary first.


### 6A. Source Structure Census and Source-Inventory Certification

Before decision-node extraction, independently census the locked source. For guideline-style sources, enumerate recommendation tables/rows (and any standalone narrative recommendations) from source-native structure, not from the already-built inventory. Record `templates/source_structure_census.csv` and run `SOURCE_INVENTORY_CERTIFICATION` against `source_recommendation_inventory.csv`. A 130-row inventory cannot certify against a source census expecting 131, even if all 130 inventory rows are later extracted.

The census pathway must be independent of the inventory-generation pathway or must receive explicit semantic/manual adjudication with reviewer, scope and reason. Fail closed when source structure cannot be reliably enumerated and semantic certification is incomplete.

## 5. Official Correction / Erratum Protocol

If an original guideline and official correction/erratum are both approved:

1. register both sources;
2. create a correction register and explicit supersession map;
3. corrected text takes precedence **only for the explicitly corrected scope**;
4. unchanged original text remains authoritative elsewhere;
5. retain both provenance paths;
6. never silently merge the correction into unrelated sections;
7. audit downstream nodes/cases/slides that depend on corrected scope.

A correction without an explicit scope locator is a hard stop for clinical release.

## 6. BUILD_CASE_BASED / CORPUS_BUILD — Exhaustive Extraction

When the user asks for a comprehensive case library, **do not ask for a target case count first**. The count is an output.

For each approved clinical source independently:

- inspect every substantive section;
- extract every defensible independent decision node;
- explicitly review recommendation tables, algorithms/figures, dose tables, narrative exceptions, contraindications, timing, thresholds, special populations, uncertainty/evidence limitations, and explanatory-only material;
- preserve source-native terminology and source role;
- capture Class/LoE exactly when present;
- distinguish direct source recommendation from a source's attribution to another guideline or organization;
- document sections checked with no independent patient-level node;
- record inaccessible supplementary-only material as a source limit, not as invented content.

Do not create polished cases or slides during extraction.

## 7. Extraction Audit / Repair / Re-Audit

Before reconciliation:

- independently audit section coverage;
- verify formal recommendation-table row completeness where relevant;
- sweep for PDF extraction artefacts, glued citation numbers, column-flow errors, over-compressed nodes, duplicates, and missed nodes;
- classify each provisional node: unchanged / repaired / merged / removed / split / newly added;
- verify counts arithmetically;
- preserve source-level uncertainty;
- hash/freeze the final inventory when the audit passes.

Do not falsely report completeness if source sections/tables were not actually checked.

## 8. Cross-Source Reconciliation

Only after independent source inventories are frozen:

- map overlapping, complementary, standalone, management-only, definition-only, and terminology-update relationships;
- create explicit reconciliation records;
- create a conflict/terminology register;
- preserve dated/source-specific language;
- do not silently harmonize labels or resolve source conflict with model judgment;
- preserve working diagnosis/management labels separately from final diagnostic/classification labels when applicable.

Reconciliation may map sources; it must not mutate frozen source inventories.

## 9. Candidate Case Corpus

Convert audited decision nodes into candidate cases only when a distinct clinical decision exists. A separate case requires a genuinely different:

- diagnostic decision;
- management choice;
- threshold;
- timing;
- contraindication;
- mechanism;
- complication;
- special population;
- risk/benefit dilemma;
- monitoring decision;
- follow-up or treatment escalation/de-escalation decision.

Do not inflate the case count with arbitrary age/sex/location changes, cosmetic laboratory differences, invented measurements, or irrelevant comorbidity changes.

Each case record should include at minimum:

- stable/provisional case ID;
- source-derived minimal scenario;
- audience question;
- distinct decision being tested;
- expected source-supported answer;
- source/node IDs and exact provenance;
- reconciliation/conflict IDs;
- exact threshold/timing/dose if applicable;
- Class/LoE if applicable;
- source-specific terminology labels;
- primary teaching objective;
- evidence status and audit status.

Explanatory-only nodes may remain non-case items if forcing them into a case would create artificial case inflation.

## 10. Case Audit / Deduplication / Coverage

Audit candidate cases for unsupported details, provenance drift, semantic duplicates, over-compressed cases, and incomplete node coverage.

Permitted dispositions:

- `KEEP`
- `MERGE`
- `SPLIT`
- `DROP`
- `NEEDS_CLARIFICATION`
- `EXPLANATORY_ONLY`

After repair, re-audit:

- every source decision node;
- every reconciliation record;
- every conflict/terminology item;
- every final case ID;
- every intentionally explanatory-only node.

Freeze the Master Case Library only after coverage passes. Create an audit report and coverage matrix.

## 11. Audience Prioritization / Teaching Architecture

After the Master Case Library freezes:

- classify audience tier (for example Core GP / Important / Advanced-Consultant / Backup-Optional or project-specific equivalents);
- record prerequisite knowledge, teaching value, and live-teaching suitability;
- group cases into clinically coherent modules;
- create a Core/live anchor path without deleting Advanced/Reference material;
- create Extended/Advanced/Reference routes;
- define terminology checkpoints and prerequisite links.

Audience priority is a teaching property, not a clinical-content edit.

## 12. Case-to-Presentation Transformation

Case-based means more than adding vignettes to a conventional lecture. Use one or more of these patterns as justified by the frozen corpus:

- `CASE / DECIDE -> audience commitment -> evidence/reveal -> source rationale -> take-home/pathway`
- paired comparison cases;
- branch cases;
- diagnostic progression;
- treatment escalation/de-escalation;
- special-population cases;
- terminology/rule checkpoints;
- source-figure augmentation;
- image-practice slides;
- algorithm/pathway slides;
- summary/checkpoint slides.

Build storyboard units and case-to-slide mapping before PPTX construction.

For each `CASE / DECIDE` unit, store `source_derived_scenario` and a neutral
`case_query_setup` question separately. Build `prompt_text` from those two
fields, then check their alignment with `scripts/prompt_semantics_validator.py`.
The scenario must be clinically sufficient to make the decision, but must not
state the recommendation before the learner commits. Remove source/pipeline
metalanguage, clipped noun phrases, dangling fragments, and action leakage at
the **scenario + prompt** layer; rebuild dependent slide/spec/map artifacts.
Preserve decision-node identity, expected answer, COR/LOE, clinical values,
population, polarity, and correction scope unless an approved locked source
directly supports a change. See `docs/decide_prompt_contract.md`.

## 13. Product Architecture

Keep these layers distinct:

- full Master Case Library;
- teaching architecture;
- Master/Core presentation;
- Live CME presentation;
- time-constrained derivatives;
- Advanced/Consultant product;
- Reference/Backup product;
- optional Modular Slide Bank/index.

A large canonical knowledge/case corpus should support smaller products without independent clinical re-research.

## 14. Slide-Level Specification Gate

Before any new clinical PPTX build, freeze a slide specification containing at least:

- slide spec ID;
- parent module/unit/sequence;
- case ID(s);
- slide role;
- title concept;
- case/query setup;
- expected answer/reveal;
- source-supported explanation requirement;
- exact source/provenance requirement;
- Class/LoE requirement;
- threshold/timing/dose requirement;
- terminology/conflict requirement;
- duplication/canonical-link classification;
- visual requirement and provenance class;
- speaker-note requirement;
- projector-density risk;
- route/disposition.

Do not improvise clinically meaningful slide content outside the frozen specification.

## 15. Speaker Notes Evidence Lock

Slides and notes serve different purposes. Notes may carry complete qualifiers and provenance that would make a projected slide unreadable, but notes are not an uncontrolled clinical channel.

Where applicable, notes must include:

- case ID(s);
- exact source provenance;
- teaching explanation / expected answer;
- complete conditions/qualifiers omitted on-screen;
- Class/LoE;
- threshold/timing/dose;
- uncertainty/evidence limitation;
- terminology differences;
- operational-context vs guideline distinction;
- question/reveal instruction;
- what not to overclaim;
- optional source-supported discussion points;
- transition/navigation cue.

Any new clinical assertion in notes must pass the same evidence lock as on-screen content.

## 16. Visual Provenance Classes

Classify each visual:

- `CLINICAL_EVIDENCE_SOURCE` — approved source content used as evidence;
- `OFFICIAL_SOURCE_FIGURE` — source figure/algorithm with provenance and reuse status;
- `USER_CLINICAL_IMAGE` — user-supplied teaching asset;
- `EXTERNAL_ILLUSTRATIVE_VISUAL` — non-evidence visual;
- `MODEL_GENERATED_DECORATIVE` — non-diagnostic illustration;
- `ORIGINAL_REDRAW` — source-faithful schematic/redraw.

For clinical images/figures, record provenance and copyright/permission uncertainty. Do not infer diagnoses from an image unless the locked evidence/case context establishes them. Never fabricate diagnostic ECG, imaging, pathology, or laboratory evidence.

## 17. PPTX Build / Projector-Safe Rules

Also obey the runtime slide-building skill available in the environment.

Default clinical presentation targets unless the project overrides them:

- title ~40–48 pt;
- body >=24 pt;
- citation/source label >=16–18 pt;
- prefer <=4 visible bullets and <=45–60 visible body words on ordinary teaching slides;
- readable numeric thresholds and units;
- limited table density;
- adequate whitespace and edge safety;
- clear title/body/footer hierarchy;
- consistent alignment and spacing;
- projector-safe contrast;
- no reliance on colour alone;
- no tiny source blocks;
- no essential information hidden only in microscopic references.

Visually distinguish case/question, audience decision, guideline/source recommendation, uncertainty, and local operational constraints.

For dense case/reveal layouts, use the optional
`docs/dys_2026_v1_5_design_reference.md` profile only when appropriate for the
project. It records a user-preferred **precanonical design reference**, not
clinical evidence or a universally safe font floor. Long titles, reveal
badges, card bodies, progress rules, and source footers need targeted geometry
checks before rendered visual review.

Do not solve overflow by blindly shrinking fonts. Preferred repair order:

1. remove redundancy;
2. move appropriate detail to evidence-locked notes;
3. split the slide;
4. restructure layout;
5. enlarge/reposition visual;
6. only then reconsider typography without violating the floor.

## 17A. VISUAL_POLISH — Content-Locked Presentation Restyle

Use when the user wants a built deck to look better without changing content or
layout logic ("beautify", "polish", "improve the visual"). It runs after
`clinical_provenance_audit` and before `automated_preflight`. It is presentation
work only, so section 21 still governs every clinical claim.

1. **Inspect and diagnose first.** Render the built deck, read every contact sheet,
   open one slide per role at full size, and list concrete defects. Every design
   change must map to a defect.
2. **Confirm with the deck owner:** scope (6-slide sample first), profile, COR
   colour coding and phase colours. Record them in `release_policy.visual_polish`.
3. **Profiles.** `projector_default` keeps the section 17 floors (body ≥24 pt,
   source ≥16 pt). `dense_case_reveal` (body 24/20/18 pt for 1/2/3 cards) mirrors the
   DYS_2026 v1.5 reference and **requires recorded owner approval**. No profile
   lowers the 16 pt source floor.
4. **Sample, then roll out by rule:**
   `python -m scripts.visual_polish.polish BUILT.pptx POLISHED.pptx --profile <p> [--profile-approved-by <name>] [--only ...] --report polish_report.json`.
   Text is copied run by run. Slide ids/order, layouts/masters and notes are untouched.
5. **Fail closed.** `SKIPPED` (unrecognised structure) and `SPLIT_REQUIRED` (cannot
   fit at the floor) slides are left exactly as built. Route `SPLIT_REQUIRED`
   upstream using the section 17 repair order. Never shrink below the floor and never trim text.
6. **Gate:** `python -m scripts.visual_polish.verify BUILT.pptx POLISHED.pptx --polish-report polish_report.json --render <dir>`
   must exit 0 (`VISUAL_POLISH_CONTENT_LOCK`: identity, verbatim text, no
   additions beyond whitelisted design tokens, notes, chrome, floors, fit, repo
   preflight). It also writes the render manifest and a blank per-slide visual-review ledger.
7. **Then continue normally:** sections 18–20 (100% individual review, independent
   QA). Any repair is a rule change followed by a full re-polish, re-verify and rerender.
8. **Promotion:** set `visual_polish_applied: true` and `visual_polish_content_lock: PASS`
   in the gates JSON. `scripts/semantic_promotion_gate.py` blocks a polished deck
   without that PASS, and it cannot be waived.

Full contract, design system and limits: `docs/visual_polish_protocol.md`.

## 18. Automated Mechanical / Structural QA

Run automated checks over 100% of slides where technically possible:

- OOXML/ZIP integrity;
- slide count and aspect ratio;
- shape bounds/off-slide elements;
- text font floors and source-label floors;
- heuristic text-fit/overflow warnings;
- text-box overlap warnings;
- placeholder/undefined text;
- image resolution/cropping warnings;
- table density/readability warnings where detectable;
- slide-title presence/consistency;
- speaker-note part coverage;
- slide-source map/case occurrence integrity;
- canonical hash mutation guard.

Automated preflight **cannot certify visual quality by itself**.
For case/reveal slides, additionally run `scripts/case_reveal_layout_gate.py`
to flag likely title/eyebrow, badge/body and body/footer problems. Its text-fit
estimates are advisory; inspect the actual rendered slides individually.

## 19. FINAL / CANONICAL Visual Acceptance — 100% Rule

For a final/canonical clinical release, when rendering is technically possible, all are mandatory:

1. automated preflight of 100% slides;
2. render 100% slides;
3. visually inspect 100% rendered slides individually;
4. explicitly review projector/UI/UX quality: hierarchy, density, whitespace, alignment, spacing, contrast, clipping, overlap, cropping, visual rhythm, case/reveal consistency, image/chart/ECG readability, source/footer visibility, misleading emphasis;
5. log each slide in a visual-review ledger;
6. repair all defensible issues;
7. rerender 100% slides after any material repair, not only the changed slide set when the final artifact is a new PPTX;
8. rerun automated preflight;
9. visually re-audit 100% slides;
10. only then proceed to promotion.

Contact sheets/montages are navigation and triage aids only; they are **not** sufficient to certify any slide.

If a renderer, required fonts, or fidelity-critical environment is unavailable, set release status to `RENDER-UNCERTIFIED`, name exactly what could not be checked, and do not claim visual PASS/canonical visual certification.
Record the renderer and version for each rendered set. An alternate renderer's
full render does not establish native PowerPoint fidelity when that fidelity
matters to the project.

## 20. Independent Second-Pass Visual QA

Use one explicit policy enum everywhere:

- `required`
- `required_unless_explicit_user_waiver`
- `optional`

For `high_stakes_clinical: true`, the default is `required_unless_explicit_user_waiver`. A project may choose `required` when its governance demands absolute second-runtime review. `optional` is not the default for high-stakes clinical releases.

A waiver under `required_unless_explicit_user_waiver` must be explicit and recorded. It produces `INDEPENDENT_QA_WAIVED` and **never** `INDEPENDENT_QA_CERTIFIED`. If no certifying report and no explicit waiver exists, use `INDEPENDENT-QA-UNCERTIFIED`.

For certification, **structured JSON is normative**. Markdown/free-text review reports are `NON_CERTIFYING_REPORT` and cannot produce independent-QA certification. Use `templates/independent_visual_review_report.json` and validate it with `scripts/independent_review_gate.py`.

The independent reviewer may be Codex, another ChatGPT execution environment, or another capable visual-review runtime. It receives the candidate PPTX, design/projector rules, source boundary, rendered set, candidate PPTX hash and rendered-slide-set hash. Its authority is visual/UI/UX and mechanical presentation quality only; `clinical_change_authority` must equal `NONE`.

The certifying JSON must contain:

- reviewer;
- reviewer runtime;
- candidate PPTX SHA-256;
- rendered-slide-set SHA-256;
- slide count;
- one **unique**, non-empty finding/status row for every slide, with no missing or out-of-range slide numbers;
- `clinical_change_authority = NONE`;
- explicit adjudication (`ACCEPT`, `REJECT`, or `CLINICAL_ADJUDICATION_REQUIRED`) for every warning/finding/proposed repair;
- repair mapping for accepted presentation repairs.

If any finding is `CLINICAL_ADJUDICATION_REQUIRED`, independent visual QA cannot certify the deck. Return that issue to the locked clinical pipeline and obtain a new resolved review.

If any visual repair is `ACCEPT`:

1. the original candidate cannot be certified;
2. require `repaired_pptx_sha256`;
3. require `repaired_rendered_slide_set_sha256`;
4. require explicit repair mapping;
5. require `second_full_render_verification = true`;
6. require a complete post-repair slide-by-slide review covering 100% of slides;
7. only the repaired final artifact may receive `INDEPENDENT_QA_CERTIFIED`.

Flow:

`independent findings -> adjudicate -> repair accepted presentation findings -> full rerender -> 100% post-repair independent review -> certification decision`.

Do not allow an independent reviewer to introduce new clinical facts. Any clinically substantive requested change returns upstream to the evidence-locked clinical pipeline.


## 20A. Final-Artifact Regression Lesson — Low-Resource MI Derivative

The final low-resource MI derivative demonstrated that structurally valid slides can still require a separate projector/UI/UX audit. The reusable design rule is:

`CASE / DECIDE -> audience commitment -> SOURCE REVEAL -> guideline rationale / actionable message`

The visual system must clearly distinguish:

- case information;
- audience question/commitment;
- source reveal;
- guideline evidence;
- local operational constraint;
- uncertainty or unavailable-resource status.

Local operational constraints may be visually prominent enough for teaching, but they must never overpower or replace the guideline recommendation. Detailed provenance may live in notes, but the on-slide source role and evidence boundary must remain readable.

## 21. Clinical / Provenance Audit

Before promotion, audit clinical and provenance domains independently from visual style:

- every clinical claim against approved source/spec;
- source boundary and correction precedence;
- thresholds, timing, doses and units;
- Class/LoE;
- source citation/locator;
- terminology/conflict handling;
- unsupported additions;
- local operational constraints vs guideline recommendations;
- wording strength relative to the source;
- figure/image provenance and permission uncertainty;
- notes content;
- slide-source map and case occurrence mapping.

If clinical meaning must change, reopen the relevant upstream clinical artifact. Do not hide a clinical fix inside a design patch.

## 22. Derivative Deck Engine

A derivative must be generated from the frozen Master Case Library, frozen teaching architecture, and canonical slide/content specification where available. Do not independently recreate clinical evidence.

Support derivation by:

- duration;
- audience;
- essential decisions;
- Advanced/Reference depth;
- local-resource focus;
- user-selected modules.

Maintain occurrence/index mapping across Master, Live, duration derivatives, Advanced and Reference products. Verify that reused case clinical fingerprints remain unchanged. Local resource constraints remain typed context, not guideline evidence.

Typical internal derivative cycle:

`DERIVATIVE SPEC -> BUILD -> clinical/mechanical QA -> 100% render/visual QA -> repair -> full rerender/re-audit -> independent promotion`.

## 23. INSPECT and PATCH Modes

### INSPECT

- read-only;
- identify current canonical/source/spec state;
- run clinical/provenance, mechanical, notes, and visual checks requested;
- do not edit;
- classify findings by severity and domain;
- do not claim PASS for unrendered visual domains.

### PATCH

- define exact bounded scope;
- snapshot hashes of protected files;
- repair only accepted defects;
- preserve unaffected clinical content;
- if clinical change is required, escalate to the relevant upstream artifact instead of silent patching;
- rerun affected audits and final-render gate as required.

## 24. BUILD_STANDARD Mode

For a conventional clinical deck that does not require an exhaustive Master Case Library:

`evidence lock -> focused source extraction/content map -> slide specification -> build -> clinical/provenance audit -> mechanical QA -> 100% render/visual QA -> repair -> rerender/re-audit -> promotion`.

Do not force case-corpus machinery when it is not requested.

## 25. FINAL_RELEASE / Canonical Promotion

A deck is not canonical because the build audit passed. Record one explicit promotion classification:

- `FULLY_CERTIFIED_CANONICAL`
- `CANONICAL_WITH_EXPLICIT_INDEPENDENT_QA_WAIVER`
- `INDEPENDENT-QA-UNCERTIFIED`
- `RENDER-UNCERTIFIED`
- `SEMANTIC-AUDIT-UNCERTIFIED`
- `REPAIR_REQUIRED`
- `REJECTED`

`FULLY_CERTIFIED_CANONICAL` requires zero unresolved CRITICAL/HIGH defects of any family plus source lock, SOURCE_INVENTORY_CERTIFICATION, SOURCE_EXTRACTION_COMPLETENESS, downstream node coverage, correction/erratum reconciliation, case fidelity, slide provenance, speaker-notes fidelity, mechanical preflight, full render/100% visual review, canonical hash/immutability, and `INDEPENDENT_QA_CERTIFIED`. All non-independent required gates accept only PASS/CERTIFIED; they are never waivable. Visual or independent-QA PASS can never override a semantic/clinical blocker.

`CANONICAL_WITH_EXPLICIT_INDEPENDENT_QA_WAIVER` is distinct from certified status. It is permitted only under `required_unless_explicit_user_waiver` with an explicit recorded waiver and all non-independent gates passing. It must retain certification `NOT_CERTIFIED`.

Record: independent-QA policy, execution status, certification, waiver reason, candidate/final PPTX hashes, initial/final rendered-set hashes, 100% final visual-review completion, clinical/provenance gate, mechanical gate, render gate, residual warnings, and whether clinical content changed. Canonical files are immutable; later changes create a controlled successor or maintenance repair stream.

## 26. Modular Slide Bank / Closure

A Modular Slide Bank should be an index/integration layer, not a giant copied clinical superdeck. Maintain slide index, case occurrence index, product/module crosswalk, navigation product, user guide, and manifest.

Final closure requires:

- every planned product canonical or explicitly waived;
- product slide/notes counts verified;
- hashes/manifest verified;
- slide/case index integrity verified;
- zero unintended canonical mutations;
- final package/archive verified;
- final closed handoff/state.

After closure, do not invent new numbered continuation phases. Use `MAINTENANCE`.

## 27. State / Handoff / Resume Rules

For long projects, every major completed state should record:

- selected mode and reason;
- phase/state completed;
- artifacts created;
- gate/audit result;
- frozen/current state;
- unresolved items;
- exact next action.

If configured with `emit_next_prompt: true`, provide a copy/paste-ready next-step prompt after each major phase. The prompt must identify project, controlling state/handoff, completed state, next task, evidence boundary, no-invention rule, terminology rule, completion criteria, anti-drift instruction, and no-redo instruction.

On `resume` / `go`:

1. read current state/handoff;
2. validate it;
3. verify required artifacts;
4. identify first dependency-valid incomplete state;
5. execute only that state unless user requested auto-finish;
6. run its gate;
7. update state/handoff;
8. report next action.

## 28. Hard Stops / Failure Protocol

Stop instead of guessing when:

- required approved source is missing/unreadable;
- evidence boundary is ambiguous;
- correction scope is ambiguous;
- a clinical claim cannot be supported;
- a source conflict needs a user policy rather than explicit labelling;
- extraction completeness cannot be established;
- a gate fails and deterministic repair is unsafe;
- source expansion is needed;
- canonical clinical content would need alteration;
- the user has not supplied an essential product/audience choice;
- renderer/font fidelity is unavailable for a final visual certification.

Report the exact blocker, affected gate, what was checked, and the smallest user decision needed.

## 29. Tooling Contract

Use deterministic tools for deterministic checks; do not confuse them with semantic clinical judgment. Included tooling covers state/mode routing, source-lock validation, correction mapping, provenance, coverage/deduplication, slide-spec validation, clinical/source linting, derivative integrity, PPTX preflight, notes, render/review ledgers, independent-review gate, slide/case indexing, canonical hashes, handoff generation, manifests and closure packaging.

Read `docs/` for detailed contracts. Run `python -m pytest` before releasing or upgrading this skill package.

## 30. Release Discipline

Do not report a clinical deck or skill package as complete unless the relevant gates actually ran. Distinguish:

- `STRUCTURAL PASS`
- `CLINICAL/PROVENANCE PASS`
- `RENDER-UNCERTIFIED`
- `VISUAL_POLISH_CONTENT_LOCK PASS` (only when polish was applied)
- `VISUAL PASS — 100% REVIEWED`
- `INDEPENDENT VISUAL QA PASS` or documented waiver
- `CANONICAL`

Never infer one status from another.
