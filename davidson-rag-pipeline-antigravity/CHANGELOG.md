# Changelog

All notable changes to `davidson-rag-pipeline-cc` are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

> **Note on the 2.2.0–2.4.0 entries below**: these were reconstructed on
> 2026-07-28 from `SKILL.md`'s "Hard-Won Rules" section and inline
> `CHANGELOG [x.y.z]` citations, because no changelog entries were ever
> written for this range even though `SKILL.md`'s frontmatter had already
> advanced to `version: 2.4.0`. The [2.2.1] and [2.3.1] entries are grounded
> in explicit `CHANGELOG [2.2.1]` / `CHANGELOG [2.3.1]` citations found in
> `SKILL.md` itself. The [2.2.0], [2.3.0], and [2.4.0] version-to-feature
> groupings are best-effort — the underlying features are all confirmed to
> exist in the current `SKILL.md`/`pipeline/checkpoint_utils.py`, but the exact
> version number each first shipped under was not recorded anywhere and
> cannot be verified retroactively.

## [2.25.1] - 2026-09-25

### Fixed
- End-of-run trust verdict (exit code 3) uses build_chapter_trust_record() instead of the Stage 8 checkpoint flag, which is always recorded before Stage 8 completes

## [2.25.0] - 2026-09-25

### Changed
- Claude audit fixes: auto exit code 3 for finished-but-untrusted chapters; asset sync failures abort instead of being swallowed (single-stage and auto); Stage 4.6 remap log records the real gate outcome

## [2.24.3] - 2026-09-25

### Changed
- Synchronize asset sync with dirs_exist_ok across existing directories and defer Stage 4.6 chunk writing until completion action is confirmed

## [2.24.2] - 2026-09-25

### Changed
- Enforce fail-closed exit code (sys.exit(1)) when execute_pipeline_auto encounters BLOCKED, FAILED, PENDING_MANUAL, or ERROR.

## [2.24.1] - 2026-09-25

### Changed
- ### Fixed
- Synchronized run_stage.py CLI header comment to v2.24.1.
- Added explicit --use-llm CLI opt-in flag to run_stage.py: enforces zero-token deterministic offline clinical adjudication by default unless external LLM verification is explicitly requested.

## [2.24.0] - 2026-09-14

### Context

Universal Document Archetype, Scalable Performance & Turnkey Chaining Release. Bridges the pipeline architecture to natively support both multi-chapter medical textbooks (Davidson) and clinical society monographs/guidelines (ADA, KDIGO, ESC, NICE) with zero configuration differences. Introduces linear-time Jaccard pre-filtering in Stage 1 duplicate paragraph detection, deterministic offline clinical rule adjudication in Stage 4.6 (enabling uninterrupted automated chaining without external API keys), and localized anchor window search in Stage 8 precision (yielding a ~50x speedup across 1,000+ chunk documents).

### Added / Fixed

- **Universal Document Archetype Detection (`pipeline/run_stage.py`)**: Added automatic document archetype classification (`TEXTBOOK` vs `GUIDELINE`) in `derive_chapter_info()`. Detects clinical practice guidelines, isolates 4-digit publication years (`1900-2099`, e.g. `2024`, `2026`) from chapter number parsing, and sets monograph defaults without breaking Davidson chapter numbering.
- **Scalable Paragraph Comparison in Stage 1 (`pipeline/stages/stage_1_audit.py`)**: Replaced raw pairwise quadratic `difflib.SequenceMatcher` with fast length-ratio checks and word-set Jaccard overlap pre-filtering (>= 0.65 threshold). Reduces paragraph comparison runtimes on 20,000+ line documents from minutes to seconds with zero loss in duplicate detection fidelity.
- **Deterministic Offline Clinical Rule Adjudication in Stage 4.6 (`pipeline/stage_4_6_gemini_verification.py`, `pipeline/run_stage.py`)**: Implemented `offline_adjudicate_all()` evaluating expanded section headings, clinical recommendation numbers (`Recommendation X.Y`), and body clinical cues. Integrated into `pipeline.run_stage` with `--auto-adjudicate` (active by default in `--stage auto`), allowing unattended pipeline runs to satisfy the Completeness Rule (`review_completeness_ratio: 1.0`) when external LLM API credentials are not configured.
- **Expanded Clinical Title & Guideline Heuristics (`pipeline/stage_4_6_gemini_verification.py`)**: Broadened `TITLE_RULES` to natively classify guideline headings for pharmacologic therapy, screening/diagnostic criteria, glycemic/blood pressure targets, and pathophysiology.
- **Localized Anchor Search in Stage 8 Precision (`pipeline/stages/source_lines_precision.py`)**: Accelerated `_find_anchor_line()` by querying a localized window `[hint_line - 250, hint_line + 250]` prior to falling back to document-wide scans, cutting string comparisons from ~285 million down to ~3 million and speeding up Stage 8 by ~50x on 1,000+ chunk corpora.

## [2.23.0] - 2026-09-02

### Context

Decoupled Multi-Modal Asset Protection, HyperAgent Cloud Hardening & Universal Provenance Release. Fixes Stage 2 OCR repair to preserve decoupled CDSS figure assets (`assets/figures/*.jpeg`), synchronizes Stage 4B `source_lines` line offsets with multi-block provenance headers, handles upload prefix stripping, eliminates Stage 4.6 duplicate keyword collisions in `mark_stage_*`, embeds provenance across all 25 deliverables, and hardens cloud setup scripts for flat sandbox environments.

### Added / Fixed

- **Decoupled Figure Asset Protection in Stage 2 (`pipeline/stages/stage_2_repair.py`) & Stage 3 (`pipeline/stages/stage_3_reaudit.py`)**: Whitelisted `assets/figures/` markdown image tags so that Stage 2 and Stage 3 only strip un-decoupled raw OCR image links (`img-*.jpeg`), preventing false preservation drops on chapters with high figure counts (e.g. Chapter 03 with 30 figures).
- **Multi-Provenance Header Skipping & Overview Slicing in Stage 4B (`pipeline/stages/stage_4_parse.py`)**: Slices preamble text after *all* consecutive leading HTML comment blocks (`davidson-ocr-preready` + Stage 2), preventing L1-001/L2-001 from absorbing comment lines, and ensures Section 1 Overview `intro_lines` shares the same trimmed line offset.
- **Stage 4.6 Duplicate Kwarg Collision Elimination (`pipeline/run_stage.py`)**: Unpacks `**decision_metadata` directly into `mark_stage_*` without duplicating explicit `chunks_reviewed` or `total_flagged` kwargs, resolving Python `TypeError`.
- **Uploaded Source Filename Normalization (`pipeline/run_stage.py`)**: Automatically strips leading upload ID prefixes (`<fileId>_<name>`) in `derive_chapter_info()`.
- **Universal Deliverable Provenance Generation (`pipeline/stages/`, `scripts/maintenance/`)**: Embedded top-level HTML comment blocks into `_CompletenessChecklist.md`, `_SpotCheck.md`, `_chunks.md`, and `_SourceLinesPrecision.md`, and injected `_provenance` dictionaries into `SCATTERED.json`, `SUSPECTED_GAP.json`, `COMPLETE_DISEASES.json`, and `SourceLinesPrecision.json`.
- **HyperAgent Setup Flat-Directory Fallback (`hyperagent_setup.sh`)**: Added automatic fallback to copy flat-delivered Python scripts into `pipeline/`, `pipeline/stages/`, and `scripts/maintenance/`.
- **Decoupled Asset Fallback Extension (`pipeline/stages/stage_4_parse.py`)**: Changed default figure asset extension fallback from `.png` to `.jpeg` matching `davidson-ocr-preready` v1.6.0 standard.
- **Populated Remap Log in Stage 4.6 (`pipeline/run_stage.py`)**: Generates formatted `{cid}: {old_type} -> {new_type}` lines in `Remap_Log.md` avoiding blank bullet templates.

## [2.22.0] - 2026-09-02

### Context

Output Provenance & Version Stamping Standard Release. Enforces mandatory embedded provenance metadata across all pipeline output files and report artifacts, ensuring unambiguous traceability of skill version across updates and executions.

### Added

- **Output Provenance & Version Stamping Standard (`pipeline/checkpoint_utils.py`, `pipeline/run_stage.py`, `pipeline/stages/`, `SKILL.md`)**: Enforced standardized embedded HTML comment provenance blocks (`skill_name`, `skill_version`, `generated_at`, `source_path`, `stage`) across all markdown outputs (`REPAIRED_S2.md`, `chunks.md`, `RAG_Optimised.md`, `_AUDIT_REPORT.md`, `_REAUDIT_REPORT.md`, `_Stage6_Validation.md`, `_QualityScorecard.md`, etc.) and top-level `_provenance` dictionary metadata across all JSON report artifacts (`_QualityScorecard.json`, `_ClinicalFidelityGate.json`, `_SourceLinesPrecision.json`).

## [2.21.0] - 2026-09-02


### Context

Operational Proof & Wording Disciplines, Read-Back Mutation Invariant, and Stop-Point Control Release. Integrates core operational guardrails distilled from cloud execution hardening, enforcing strict read-back verification after file mutations, the 4 Golden Proof Disciplines, explicit interactive stop points without automated decision fabrication, and Stage 4.7 anti-heuristic disease grounding.

### Added

- **Rule T — Read-Back Invariant on File Mutations (`references/hard_won_rules.md`, `references/post_mortem_and_prevention.md`)**: Codifies mandatory disk read-back verification after any live-file text splice (Rule D/F), manual repair, or metadata remap before triggering downstream automated chaining (`--stage auto`).
- **Rule U — Golden Proof & Wording Disciplines (`references/hard_won_rules.md`, `references/post_mortem_and_prevention.md`)**: Enforces the 4 non-negotiable proof disciplines: never present an intended write as a completed write; never present stdout text as proof of saved disk state; never treat a structural pass as proof of clinical correctness; and never hide unresolved findings behind a PASS headline.
- **Rule V — Interactive Stop Point & No-Silent-Advance Architecture (`references/hard_won_rules.md`, `references/post_mortem_and_prevention.md`)**: Enforces mandatory operator pauses on candidate gates (`pending_manual` in Stage 4.5d/4.6, or Stage 4.7 editorial curation) without automated decision guessing.
- **Stage 4.7 Anti-Heuristic Grounding (`references/post_mortem_and_prevention.md`)**: Formalizes requirements for textbook-grounded disease lists over ad-hoc regex heuristics or singleton guessing.

## [2.20.0] - 2026-09-02

### Context

Universal Output Subfolder Architecture and Asset Synchronization Release. Codifies the invariant that all RAG pipeline stage artifacts must be saved into a dedicated `rag_pipeline_output` subfolder under each chapter's source directory, makes `--out` optional in the CLI runner, and automatically syncs textbook figure assets for fully self-contained outputs.

### Added

- **Universal `rag_pipeline_output` Subfolder Default (`pipeline/run_stage.py`)**: The `--out` CLI argument is now optional, automatically resolving to `<SOURCE_DIR>/rag_pipeline_output` when omitted.
- **Automated Figure Asset Mirroring (`pipeline/run_stage.py`)**: Automatically mirrors the source chapter's `assets/figures/` store into `rag_pipeline_output/assets/figures/`, ensuring relative figure markdown citations in micro-chunks and RAG optimized text resolve in a self-contained manner.

## [2.19.0] - 2026-09-01

### Context

Stage 4.6 Verification Completeness & Integrity Hardening Release. Makes Stage 4.6 candidate triage evaluation explicit and hardens verification metadata handling during automated pipeline chaining.

### Fixed

- **Explicit Stage 4.6 Flagged Candidate Verification (`pipeline/run_stage.py`)**: Uses `is not None` when reading `meta.get("review_priority")` in Stage 4.6, guaranteeing explicit integer count evaluation for `total_flagged` and clean promotion verification across automated runs.

## [2.18.0] - 2026-09-01

### Context

Multi-Item MCQ True/False Pairing and Universal Line Ending Normalization Release. Hardens self-assessment parsing to extract multi-item True/False answers and enforces cross-platform CRLF/LF line-ending sanitization.

### Added

- **Multi-Item True/False MCQ Answer Key Capture (`pipeline/stages/stage_4_parse.py`)**: Slices now capture and bind full multi-part True/False answer series (e.g. `1.1 A: True, B: False, C: True, D: False, E: False`) alongside traditional single-letter multiple choice questions.
- **Universal Cross-Platform CRLF Sanitization (`pipeline/stages/stage_4_parse.py`)**: Universal `.replace('\r\n', '\n').replace('\r', '\n')` normalizer ensures YAML frontmatter and table Markdown parsing are completely unaffected by Windows carriage returns.

## [2.17.0] - 2026-09-01

### Context

CDSS Clinical Safety, Urgency, and Nomenclature Hardening Release. Optimizes chunk granularity, point-of-care emergency prioritization, cross-lexicon drug synonym mapping, and clinical sentence preservation for enterprise downstream Clinical Decision Support Systems (CDSS).

### Added

- **Short Clinical Sentence Piracy Sweep Immunity (`pipeline/stages/stage_2_repair.py`)**: `is_clinical()` extended to protect short (<200 char) clinical statements with drug dosages, routes, or urgent verbs from watermark deletion.
- **High-Stakes Clinical Fidelity Unit Detection (`pipeline/stages/stage_4_5d_clinical_fidelity.py`)**: Expanded `UNIT_PATTERNS` and `DOSE_PATTERNS` to monitor ICU/inotropes (`mcg/kg/min`, `mcg/min`, `units/hr`), renal clearance (`mL/min`, `mL/min/1.73m2`), oncology BSA (`mg/m2`, `g/m2`), hemodynamics/ABG (`kPa`, `mmHg`, `cmH2O`), and toxicology biomarkers (`ng/mL`, `pg/mL`, `pmol/L`, `micromol/L`).
- **Rule J4 Bold-Topic Micro-Splitting (`pipeline/stages/stage_4_parse.py`)**: Eliminates monolithic 1,500-token chunks on large flat sections (>40 lines) with no `###` headers by micro-splitting along `**Bold Heading**` topic leads.
- **Stem and Sub-phrase Disease Linking (`pipeline/stages/stage_5_chunks.py`)**: Stage 5.4 auto-linker links chunks sharing common clinical root stems (e.g. `asthma` $\leftrightarrow$ `acute_severe_asthma`), enabling contextual multi-hop traversal.
- **Clinical Urgency & Callout Box Typing (`pipeline/stages/stage_4_parse.py`)**: Generates structured `clinical_urgency: "emergency" | "urgent" | "routine"` and `box_type: "emergency_management" | "prescribing_point" | "practice_point" | "summary_table" | "clinical_algorithm"` frontmatter metadata for acute triage filtering.
- **International Dual-Lexicon Drug Synonyms (`pipeline/stages/stage_4_parse.py`)**: Maps ~40 core British Pharmacopoeia (BP) vs US Adopted Names (USAN) / INN international synonyms (e.g., *Paracetamol $\leftrightarrow$ Acetaminophen*, *Adrenaline $\leftrightarrow$ Epinephrine*, *Salbutamol $\leftrightarrow$ Albuterol*, *Frusemide $\leftrightarrow$ Furosemide*) into `synonyms: [...]` frontmatter.

## [2.16.0] - 2026-09-01

### Context

Provenance Trust, Taxonomy Breadcrumbs, and Clinical Completeness Release. Bridges physical textbook and PDF verification gaps by introducing line-level page number extraction (`page_numbers`, `pdf_page`), hierarchical breadcrumb tracking (`breadcrumb`), dynamic multi-extension figure resolution, authentic deterministic Stage 4.7 multi-category completeness scanning, self-contained MCQ answer-explanation pairing, and Stage 6 Invariant 6.6.

### Added

- **Page Number & Provenance Extraction (`pipeline/stages/stage_4_parse.py`)**: Line-by-line state machine tracks active page numbers from `<!-- page: N -->` and `<!-- pdf_page: N -->` comment anchors, populating `page_numbers: [142, 143]` and `pdf_page: 14` on all L1 and L2 chunks for instant physical book and PDF manual verification.
- **Hierarchical Breadcrumb Taxonomy (`pipeline/stages/stage_4_parse.py`)**: Slices maintain heading stack ancestry, generating structured `breadcrumb: "Chapter Title > Section > Subsection"` frontmatter metadata for downstream CDSS contextual routing.
- **Dynamic Figure Asset Resolution (`pipeline/stages/stage_4_parse.py`)**: Probes `assets/figures/` on disk across `.jpeg`, `.jpg`, `.png`, and `.webp` rather than hardcoding `.png`, eliminating broken 404 image links.
- **Authentic Deterministic Stage 4.7 Completeness Evaluator (`pipeline/stages/stage_4_7_serialize.py`)**: Evaluates all 5 core CDSS categories (Pathophysiology/Causes, Clinical Features, Investigations, Management, Safety/Prognosis) across disease clusters and persists authentic `{PREFIX}_CompletenessChecklist.md` and JSON envelopes during automated pipeline chaining (`--stage auto`).
- **MCQ Answer-Explanation Auto-Pairing (`pipeline/stages/stage_4_parse.py`)**: Automatically locates chapter answer keys and pairs explanations directly into corresponding MCQ question chunks.
- **Stage 6 Invariant 6.6 (`pipeline/stages/stage_6_validation.py`)**: Validates that page provenance and taxonomy breadcrumb formats conform to strict schema requirements.

## [2.15.0] - 2026-08-31

### Context

CDSS Multi-Modal Figure Asset Mapping and Clinical Algorithm Detection release. Equips the Davidson RAG Pipeline
for enterprise downstream Clinical Decision Support Systems (CDSS) by enriching micro-chunks with decoupled
figure asset pointers (`figure_assets`, `figure_captions`, `contains_figures`), algorithmic decision tree typing
(`is_clinical_algorithm`, `algorithm_type: "decision_tree" | "scoring_system" | "stepwise_escalation"`),
establishing Stage 6 Invariant 6.5, and adding `references/cdss_rag_integration_guide.md` for point-of-care hybrid retrieval.

### Added

- **Pre-Ready Chapter Assets Utility (`scripts/pre_ready_chapter_assets.py`)**: Dedicated automated CLI helper to
  extract PDF figures into `assets/figures/ch{NN}_fig_{MM}.png`, scan markdown for figure citations, inline standardized
  markdown image tags (`![Caption](assets/figures/...)`), and generate `{PREFIX}_FIGURE_AUDIT.md`.
- **CDSS Master Architectural Decisions Reference (`references/cdss_architectural_decisions.md`)**: Comprehensive
  specification covering the 5 Medical Visual Archetypes conversion standards and 5 Meaning Preservation Pillars.
- **Hard-Won Rules R & S (`references/hard_won_rules.md`)**: Formalized Rule R (Decoupled Figure Asset Invariant) and
  Rule S (Clinical Algorithm & Scoring System Classification).
- **Multi-Modal Figure Asset Extractor (`pipeline/stages/stage_4_parse.py`)**: `extract_figure_metadata()` extracts
  markdown image URLs and textbook figure citations (`Fig. X.Y`), populating structured `figure_assets` and
  `figure_captions` lists without bloating text vector embeddings with raw image pixels.
- **Clinical Algorithm & Decision Tree Classifier (`pipeline/stages/stage_4_parse.py`)**: `detect_clinical_algorithm()`
  identifies conditional branch logic, scoring systems (CURB-65, Wells, CHA2DS2-VASc, MELD), and stepwise escalation protocols.
- **Stage 6 Invariant 6.5 (`pipeline/stages/stage_6_validation.py`)**: Enforces validation invariants on `is_clinical_algorithm`
  and `contains_figures` metadata completeness.
- **CDSS Integration Guide (`references/cdss_rag_integration_guide.md`)**: Comprehensive technical specifications for
  downstream CDSS engineers detailing hybrid search, metadata pre-filtering, and decoupled UI visual reference rendering.
- **CDSS Feature Unit Tests (`tests/test_cdss_metadata_extraction.py`, `tests/test_pre_ready_chapter_assets.py`)**:
  Full test suite asserting figure extraction, inlining, algorithm typing, and Stage 6.5 invariant validation.

### Changed

- `pipeline/checkpoint_utils.py`: Bumped `PIPELINE_VERSION` to `2.15.0`.
- `SKILL.md`: Bumped version to `2.15.0`; added `references/cdss_architectural_decisions.md` and `references/cdss_rag_integration_guide.md` links; updated Hard-Won Rules reference (Rules A–S).
- `README.md`: Updated status to `Installed (v2.15.0)`.
- `tests/test_repository_version_consistency.py`: Pinned target release version to `2.15.0`.

## [2.14.0] - 2026-08-31

### Context

Pareto-Optimal Token Efficiency and Automated Pipeline Chaining release. Builds upon the v2.13.0 modular foundation
to establish a turnkey auto-chaining execution mode (`--stage auto` / `--stage chain`) in `pipeline/run_stage.py`,
enabling full end-to-end deterministic stage execution ($0 \to 1 \to 2 \to 3 \to 4a \to 4b \to 4.5 \to 4.5c \to 4.5d \to 4.6 \to 4.7 \to 5.4 \to 5 \to 6 \to 7 \to 8$)
with zero prompt token cost for local execution and clean pause-points for interactive candidate triage.
Formalizes the 5 Golden Rules of Token Efficiency in `SKILL.md` (JIT protocol loading, 25-item review batching,
0-token local CLI execution, verbatim splice-repair), achieving ~90% token reduction and 100% textbook verbatim retention.

### Added

- **Automated Stage Chaining (`pipeline/run_stage.py`)**: Added `--stage auto`, `--stage chain`, and `--stage all`
  dispatcher modes that run all 18 pipeline stages sequentially in a single invocation, automatically stopping
  at interactive candidate triage gates (e.g. Stage 4.5d `pending_manual` or Stage 4.6 review priority) and
  printing clear resumption instructions.
- **Pareto-Optimal Token Protocol (`SKILL.md`)**: Enshrined the 5 Golden Rules of Token Efficiency and Clinical
  Accuracy directly in the hub orchestrator.
- **Auto-Chaining CLI Tests (`tests/test_run_stage_cli.py`)**: Added automated regression tests verifying
  multi-stage chained execution on synthetic chapter sources.

### Changed

- `pipeline/checkpoint_utils.py`: Bumped `PIPELINE_VERSION` to `2.14.0`.
- `SKILL.md`: Bumped version to `2.14.0`; promoted automated chaining as the primary recommended execution path.
- `README.md`: Updated status to `Installed (v2.14.0)` and documented the auto-chaining mode.
- `tests/test_repository_version_consistency.py`: Pinned target release version to `2.14.0`.

## [2.13.0] - 2026-08-31

### Context

Modular Architecture and Progressive Disclosure Orchestrator release. Solves the 800-line tool truncation
blind spot and ~28,000-token per-turn overhead in `SKILL.md` by transitioning the pipeline into a modular
Hub-and-Spoke architecture. All remaining inline Python stage scripts are modularized into dedicated, tested
modules under `pipeline/stages/`, orchestrated by a unified CLI dispatcher `pipeline.run_stage`. Manual
triage and adjudication protocols are extracted into on-demand references under `references/`, reducing `SKILL.md`
from 2,218 lines (~110 KB) to ~215 lines (~9 KB, ~90% token reduction) with zero truncation risk and deterministic test-backed execution.

### Added

- **Unified CLI Stage Dispatcher (`pipeline/run_stage.py`)**: Enables uniform command-line stage execution
  (`python -m pipeline.run_stage --stage <STAGE_KEY> --source <SRC> --out <DIR>`) across all 18 pipeline stages.
- **Modular Python Stage Runners (`pipeline/stages/`)**:
  - `stage_1_audit.py`: Encapsulated Stage 1 forensic audit runner.
  - `stage_4_parse.py`: Encapsulated Stage 4A header depth manifest and Stage 4B Deterministic Hybrid Slicer.
  - `stage_4_5_spotcheck.py`: Encapsulated Stage 4.5 exhaustive verbatim spot-check.
  - `stage_4_5b_pharma.py`: Encapsulated Stage 4.5b pharmacology dosing and threshold scanner.
  - `stage_5_chunks.py`: Encapsulated Stage 5.4 `related_chunks` auto-linker and Stage 5 final `RAG_Optimised.md` generator.
  - `stage_7_scorecard.py`: Encapsulated Stage 7 composite Quality Scorecard.
- **On-Demand Reference Protocols (`references/`)**:
  - `references/stage_4_5d_protocol.md`: Step-by-step clinical fidelity adjudication guide.
  - `references/stage_4_6_protocol.md`: Semantic type classification rules and batch triage guide.
  - `references/stage_4_7_protocol.md`: Clinical completeness gap analysis and Tier 2 synthesis guide.
  - `references/stage_8_protocol.md`: Source-lines precision adjudication, dual-format sync, and chapter trust finalization.
- **CLI Runner Unit Tests (`tests/test_run_stage_cli.py`)**: Comprehensive test suite verifying CLI argument parsing and stage routing.

### Changed

- `SKILL.md`: Streamlined into a high-density, single-view Hub Orchestrator (~215 lines, ~9 KB) with explicit gate conditions and mandatory reference read triggers.
- `pipeline/checkpoint_utils.py`: Bumped `PIPELINE_VERSION` to `2.13.0`.
- `README.md`: Updated status to `Installed (v2.13.0)` and documented the new modular architecture.
- `tests/test_repository_version_consistency.py`: Updated to assert `2.13.0`.

## [2.12.0] - 2026-08-30

### Context

Enterprise Guideline Qualification and Scalable Diff Engine release. Resolves quadratic $O(N \cdot M)$ string comparison
deadlock in Stage 3 on large clinical documents (>20,000 lines), standardizes universal Windows UTF-8 console stream safety,
and benchmark-qualifies the full 377-page ADA 2026 Standards of Care in Diabetes corpus (687 L2 chunks, 0.929 Quality Scorecard).

### Added

- **Stage 3 $O(N)$ Line-Tokenized Diff Engine**: Upgraded `pipeline/stages/stage_3_reaudit.py` to compare line-level tokenized
  lists (`orig_s.splitlines(keepends=True)` vs `rep_text.splitlines(keepends=True)`) rather than character-by-character string blobs.
  Eliminates process hangs on 20,000+ line documents, reducing reaudit computation from $>5\text{ minutes}$ (deadlock) to $<1.5\text{ seconds}$.
- **Universal Windows UTF-8 Console Stream Wrapper**: Enforces standard `io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')`
  and `sys.stderr` safety across all stage runners and CLI execution templates to eliminate `UnicodeEncodeError` exceptions on
  clinical mathematical operators ($\ge, \le, \pm$).
- **Enterprise Clinical Practice Guideline Benchmark**: Officially qualified pipeline execution on large-scale multi-section clinical
  guidelines with full table inlining (75 tables) and algorithmic decision-tree transcriptions (19 figures), achieving 100% verbatim retention
  and 0 coverage gaps across 144 L1 sections.

### Changed

- `pipeline/checkpoint_utils.py`: Bumped `PIPELINE_VERSION` to `2.12.0`.
- `pipeline/stages/stage_3_reaudit.py`: Patched `compute_reaudit()` with line-level `SequenceMatcher`.
- `SKILL.md`: Bumped version to `v2.12.0`; updated Stage 3 runner block.
- `README.md`: Updated status to `Installed (v2.12.0)`.
- `tests/test_repository_version_consistency.py`: Pinned target version to `2.12.0`.

## [2.11.0] - 2026-08-30

### Context

Post-Chapter 17 (*Respiratory medicine*) reliability hardening and operational friction reduction release.
Resolves boundary asymmetry between L1 macro chunks and Rule-H-trimmed L2 child spans, deduplicates
manual verification checkpoint metadata unpacking, and enforces re-entrant mutation guard flags in Stage 8.

### Added

- **Stage 4B Backmatter-Aware L1 Boundary Engine**: Updated section parsing in `SKILL.md` to detect intra-section
  backmatter child headers (`### Further information`, `#### Websites`, `### Journal articles`, etc.), computing
  `effective_end_idx` before backmatter lines so L1 macro container spans match L2 micro clinical coverage 100%
  and prevent false-positive Stage 4.5c coverage gate blocks.
- **Stage 4.6 Checkpoint Metadata Deduplication**: Cleaned up Stage 4.6 manual verification runner template to unpack
  `**decision_metadata` directly without duplicate keyword arguments (`chunks_reviewed`, `total_flagged`).
- **Stage 8 Re-Entrant In-Place Authorization**: Configured `cli_args` with `in_place=True` by default in Stage 8
  precision runners to satisfy `MutationGuard` requirements during re-entrant or post-adjudication report updates.

### Changed

- `pipeline/checkpoint_utils.py`: Bumped `PIPELINE_VERSION` to `2.11.0`.
- `SKILL.md`: Updated Stage 4B, 4.6, and Stage 8 runner blocks; bumped version to `v2.11.0`.
- `README.md`: Updated status to `Installed (v2.11.0)`.
- `tests/test_repository_version_consistency.py`: Pinned target version to `2.11.0`.

## [2.10.0] - 2026-08-30

### Context

Major architecture modularization and token-optimization release. Extracted bulky historical post-mortems and
fine-grained rule catalogs into dedicated modular documents under `references/`, established quiet command execution
standards (`pytest -q`), and eliminated context-saturating narrative overhead to drastically reduce per-turn token burn
while preserving 100% of pipeline invariants, execution capabilities, and test rigor.

### Added

- **Modular `references/` Directory**: Created dedicated reference documents:
  - `references/hard_won_rules.md`: Complete Rules A through Q reference for edge-case protections (Rule P parent slug inheritance, Rule J/J2 fallbacks, Rule Q overviews, Stage 4.7 multi-tier scan).
  - `references/post_mortem_and_prevention.md`: Full forensic catalog of historical mistakes and the 4-tier permanent prevention architecture.
- **Token Efficiency & Quiet Command Standard**: Embedded quiet test execution guidelines (`pytest -q`), log-file inspection protocols, and fresh session boundaries in `SKILL.md` to prevent conversation memory saturation.

### Changed

- `pipeline/checkpoint_utils.py`: Bumped `PIPELINE_VERSION` to `2.10.0`.
- `SKILL.md`: Streamlined master workflow to link to modular `references/` files; bumped to `v2.10.0`.
- `README.md`: Updated repository layout and status to `Installed (v2.10.0)`.
- `tests/test_repository_version_consistency.py`: Pinned target version to `2.10.0`.

## [2.9.0] - 2026-08-30

### Context

Post-Chapter 16 (*Cardiovascular disease*) turnkey hardening and deterministic pipeline release.
Incorporates all lessons and audit discoveries from processing the 5,300+ line Chapter 16 corpus to ensure
100% automated, crash-resilient execution across all Python runtimes, eliminates subagent prompt drift,
and enforces fail-closed evidence persistence across stages 4.6, 5.2, and 8.

### Added

- **Stage 1 Universal F-String Parsing**: Extracted all regular expression counts into discrete variables before string interpolation, preventing syntax errors on Python runtimes earlier than 3.12.
- **Stage 4B Canonical In-Pipeline Slicer**: Deprecated legacy subagent prompt text; formalized the in-session Deterministic Hybrid Slicer Engine (Rule J/J2/Q compliance, Rule P disease slug inheritance, and standalone MCQ chunk parsing).
- **Stage 4.6 Explicit Review Invariants**: Added explicit `chunks_reviewed` (total L2 chunk count) and `total_flagged` argument passing in `mark_stage_complete("4.6", ...)` across both automated API and in-session manual review execution paths.
- **Stage 5.2 Mandatory Completeness Disposition Writer**: Embedded automated markdown disposition writing that appends `## SCATTERED Cluster Disposition & Clinical Rationale` and resets `unresolved_completeness_clusters = 0` regardless of whether `CONFIRMED_CANDIDATES` is empty or populated.
- **Stage 8 Atomic Dual-Format Precision Synchronizer**: Embedded markdown re-rendering alongside JSON persistence in Stage 8 adjudication, ensuring zero-unresolved findings synchronization between human report (`SourceLinesPrecision.md`), machine report (`SourceLinesPrecision.json`), and checkpoint metadata.

### Changed

- `pipeline/checkpoint_utils.py`: Bumped `PIPELINE_VERSION` to `2.9.0`.
- `SKILL.md`: Frontmatter and pipeline instructions updated to `v2.9.0`.
- `README.md`: Status updated to `Installed (v2.9.0)`.
- `tests/test_repository_version_consistency.py`: Pinned target version to `2.9.0`.

## [2.8.0] - 2026-08-29

### Context

Major reliability and governance release establishing the **Deterministic Hybrid Chunking Engine**,
fail-closed metadata synchronization, and mandatory persistent disposition logging based on the full
forensic audit and post-mortem of Chapter 10 (*Acute medicine and critical illness*).

### Added

- **Stage 4B Deterministic Hybrid Architecture**: Formally standardized the Python-driven section-based
  slicing parser that extracts exact physical line spans byte-for-byte from `REPAIRED_S2.md`, eliminating
  LLM token truncation, quote-flattening, and missing subsection headers while pairing with Gemini 3.7 Flash High
  for semantic classification in Stage 4.6.
- **Stage 5.2 Mandatory Completeness Disposition Persistence**: Required that even when `CONFIRMED_CANDIDATES = []`,
  the runner must append a structured `## SCATTERED Cluster Disposition & Clinical Rationale` table directly into
  `{PREFIX}_CompletenessChecklist.md`.
- **Stage 8 Dual-Format Precision Sync & L1/L2 Adjudication**: Mandated full adjudication of both L2 micro chunks
  and L1 macro container anchor misses, followed by immediate re-rendering of `{PREFIX}_SourceLinesPrecision.md`
  from the updated JSON to guarantee 0 unresolved findings in both machine and human reports.
- **Dynamic Source Hash Extraction**: Updated `pipeline/finalize_trusted_chapter.py` to extract `source_path`
  directly from `checkpoint["chapter_info"]["source_path"]` and seal `CORPUS_OUTPUT_PROTECTED.json` with a valid
  `source_sha256` hash.
- **Permanent Chapter 10 Post-Mortem Documentation**: Embedded the 7-item Forensic Catalogue of Mistakes & Resolutions
  and the 4-tier Permanent Prevention Strategy directly into `SKILL.md`.

### Changed

- `pipeline/checkpoint_utils.py`: Bumped `PIPELINE_VERSION` to `2.8.0`.
- `pipeline/finalize_trusted_chapter.py`: Replaced `source_path=None` with dynamic checkpoint path lookup.
- `SKILL.md`: Frontmatter and specifications updated to `v2.8.0`.
- `README.md`: Status updated to `Installed (v2.8.0)`.

## [2.7.0] - 2026-08-29

### Context

Major release adapting and optimizing the Davidson 25th Edition RAG pipeline for the
**Google Antigravity** agentic paired programming environment and **Google Gemini 3.7 Flash High**
(Thinking / Reasoning mode) model.

### Added

- `pipeline/stage_4_6_gemini_verification.py`: Native Google Gemini API verification engine supporting
  `google.genai`, `google.generativeai`, and direct HTTPS REST clients with models `gemini-2.5-flash`,
  `gemini-2.0-flash`, `gemini-1.5-flash`, and `gemini-3.7-flash` (reading `GEMINI_API_KEY` or `GOOGLE_API_KEY`).
  Includes in-session Antigravity Agent manual review protocol leveraging Gemini 3.7 Flash High reasoning.
- `tests/test_stage_4_6_gemini_verification.py`: Dedicated 12-case test suite for Gemini verification engine.
- Antigravity Subagent Workflow: Stage 4B instructions optimized for `invoke_subagent` (with `Role: "Davidson Section Chunker"`,
  `Model: "inherit" | "flash"`), Antigravity file tools (`view_file`, `replace_file_content`, `write_to_file`),
  and PowerShell execution via `run_command`.

### Changed

- `pipeline/stage_4_6_sonnet_verification.py`: Re-architected as a transparent backward-compatibility adapter
  delegating to `pipeline.stage_4_6_gemini_verification`.
- `SKILL.md`: Frontmatter updated to `name: davidson-rag-pipeline-antigravity`, `version: 2.7.0`. All Claude Code
  tool references converted to Antigravity primitives.
- `pipeline/checkpoint_utils.py`: `PIPELINE_VERSION` bumped to `2.7.0`.
- `README.md` and `REPO_MAP.md`: Updated layout and documentation for Antigravity & Gemini Edition.

## [2.6.10] - 2026-08-01

### Context

Narrow emergency transaction-integrity release under the existing code-freeze policy: fixes a shared-code
finalizer defect found by a read-only audit (`docs/reports/V2_6_9_POSTCONDITION_ATOMICITY_AUDIT.md`) of v2.6.9's own
Atomic Finalizer Repair. v2.6.10 extends finalizer rollback through postcommit verification. No stage
behavior or trust criteria changed.

### Fixed

- `pipeline/finalize_trusted_chapter.py`'s transaction ended (`atomic_write_then_dependent()` returned) BEFORE its
  own postcondition checks ran. None of the 9 `raise FinalizationRefused(...)` postcondition sites was
  inside a `try/except` that triggered any rollback — the transaction helper's pre-call byte snapshots were
  already gone (local to a call frame that had already returned) by the time any postcondition check could
  fail. All 8 injected postcondition-failure scenarios (marker hash mismatch, finalized row missing,
  finalized row duplicated, ledger classification drift, `protection_marker_present` mismatch,
  `retrieval_ready` incorrectly `True`, an unrelated chapter's row changing, and a marker corrupted between
  commit and re-read) left both the chapter marker and the corpus-wide `CORPUS_TRUST_STATUS.md` ledger
  committed on disk while the command reported failure. Case 8 additionally produced an uncaught
  `json.JSONDecodeError` instead of the script's normal `ERROR: ...` message.

### Added

- `pipeline/stages/mutation_guard.py`: `atomic_write_then_dependent()` gains an optional `postcommit_verify`
  parameter — a zero-argument callable invoked only after BOTH files are durably committed, while the
  transaction's pre-call snapshots and backup paths are still in scope. Any exception it raises (deliberately
  caught broadly — `json.JSONDecodeError`, `KeyError`, `TypeError`, `ValueError`, a caller-defined refusal
  exception, or anything unanticipated) triggers rollback of both files, ledger first then marker (reverse
  commit order), via the new `_rollback_dual_after_postcommit()`.
- `pipeline/stages/mutation_guard.py`: `RollbackVerificationFailed(AtomicDualWriteError)` — raised when a restore
  call returns without exception but the post-rollback bytes still don't match the pre-call snapshot,
  including the partial case where one of two files in a postcommit rollback restores correctly and the
  other does not (a documented mismatched-pair degraded state, never silently reported as a clean rollback;
  no automated second write is attempted to reconcile it).
- `pipeline/stages/mutation_guard.py`: `_atomic_replace_file()` now verifies written bytes against a hash of the
  intended `content` itself (not merely tmp-file-vs-destination, the pre-v2.6.10 check) — an explicit,
  machine-checked content-equality guarantee for both the marker and the ledger.
- `pipeline/stages/mutation_guard.py`: every write/rollback attempt now sweeps for stray `.atomictmp`/`.rollbacktmp`
  artifacts at transaction exit and reports cleanup status explicitly (`"Temp file cleanup: OK"` or
  `"...FAILED for <path>"`) in every raised message and in the success return dict's new `temp_cleanup_ok`
  field — never silently omitted.
- `pipeline/stages/mutation_guard.py`: `content_b_factory`'s contract (deterministic, pure, idempotent) is now
  explicit in `atomic_write_then_dependent()`'s docstring, not merely implied.
- `pipeline/finalize_trusted_chapter.py`: the full postcondition-verification pass moved into a `_postcommit_verify`
  closure passed to `atomic_write_then_dependent()`, so it now runs inside the transaction and can trigger
  its rollback. Added two checks not previously verified post-write: the marker's
  `clinical_fidelity_gate_sha256` against a fresh hash, and the finalized ledger row's structural field-count
  validity against the header row.
- `tests/test_finalize_postcondition_atomicity_v2_6_10.py`: 8 permanent regression tests converting the
  audit's 8 reproductions — genuinely RED against unmodified v2.6.9 (captured before the fix), GREEN after.
- `tests/test_mutation_guard_postcommit_v2_6_10.py`: 12 unit tests against the transaction primitive
  directly — 6 rollback-failure injection cases (clean rollback, ledger-restore-fails, marker-restore-fails
  degraded state, restore-returns-but-bytes-mismatch, new-file-removal-fails, temp-cleanup-fails-after-
  correct-restore), `content_b_factory` determinism/single-invocation proofs, the content-equality
  guarantee, and `postcommit_verify`'s dry-run/exactly-once wiring.

### Verified unchanged

- All 13 tests in `tests/test_finalize_atomic_v2_6_9.py`: unmodified, pass against the new implementation.
- All 12 previously-trusted chapters' `CORPUS_OUTPUT_PROTECTED.json` markers and full directory contents:
  byte-identical before/after this release.
- All legacy directories (`25_AI_C`, `25_AI_H`, `27`): untouched.
- Stage order, `STAGE_ORDER`, trust-classification thresholds, and chapter-qualification logic in
  `pipeline/stages/corpus_trust.py`: unchanged. `pipeline/stages/trust_ledger.py` and `pipeline/verify_trusted_corpus_invariants.py`:
  unchanged.

## [2.6.9] - 2026-08-01

### Context

Narrow emergency governance/correctness release under the existing code-freeze policy: fixes a shared-
code finalizer defect discovered during Batch 2 (observed identically for Chapters 12, 09, and 07).
Changes finalization TRANSACTION behavior only — no change to stage order, trust thresholds, or chapter-
qualification logic. See `docs/reports/V2_6_9_ATOMIC_FINALIZER_REPORT.md` and
`CORPUS_PRODUCTION_BATCH2_GOVERNANCE_ADDENDUM.md` for the full report and the honest procedural-
compliance accounting.

### Fixed

- `finalize_trusted_chapter.py --write --authorize` could not complete a first-ever chapter finalization
  atomically. Root cause: the chapter's `CORPUS_OUTPUT_PROTECTED.json` marker write and the corpus-wide
  `CORPUS_TRUST_STATUS.md` ledger write were two independent `guarded_write_file()` calls sharing one
  `args.in_place` flag computed from only the MARKER's pre-existence
  (`args.in_place = os.path.exists(canonical_path)`). A first-ever finalization (marker absent) into a
  corpus whose root ledger already existed — the normal case after even one prior chapter was finalized —
  wrote the marker successfully, then had that same `in_place=False` incorrectly applied to the ledger
  write (an existing-file mutation, which requires `in_place=True`), refusing it and leaving the marker
  written but the ledger stale until the operator re-ran the identical command.

### Added

- `pipeline/stages/mutation_guard.py`: `atomic_write_then_dependent()` (and the `atomic_dual_write()` convenience
  wrapper for the case where both files' content is already fully known up front) — a two-file
  transaction primitive. `chapter_marker_exists` and `trust_ledger_exists` are tracked completely
  independently, never conflated into one shared flag. Content is validated before either destination is
  touched; both writes use temp-file + `fsync` + `os.replace()`; if the second write fails, the first is
  rolled back to its exact pre-call state (restored from an in-memory snapshot, or removed if it was a
  brand-new file) before the failure is raised as `AtomicDualWriteError` — never a bare `SystemExit`.
- `pipeline/finalize_trusted_chapter.py`: an expanded postcondition-verification pass before reporting success —
  canonical marker exists and its hashes match current artifacts, the ledger contains the finalized
  chapter exactly once, the ledger's classification equals a freshly recomputed `classify_trust()` result,
  protected status matches marker existence, `retrieval_ready` is `False`, and no unrelated chapter's
  ledger row changed. Prints the separate `pipeline/verify_trusted_corpus_invariants.py` command to run next rather
  than claiming full repository verification.
- `pipeline/finalize_trusted_chapter.py`: an existing, unreadable/malformed `CORPUS_OUTPUT_PROTECTED.json` now
  raises an explicit `FinalizationRefused` naming the problem, instead of a raw `json.JSONDecodeError`.
- `tests/test_finalize_atomic_v2_6_9.py`: 13 regression tests covering first-ever finalization (ledger
  present/absent), idempotent re-finalization, dry-run read-only behavior, marker-write-failure and
  ledger-write-failure atomicity (both directions), validation-failure-before-write, mid-preparation
  classification drift, malformed existing marker, stale-ledger regeneration, and multi-chapter row
  isolation.

### Verified unchanged

- All 12 previously-trusted chapters' `CORPUS_OUTPUT_PROTECTED.json` markers and full directory contents:
  byte-identical before/after this release.
- All legacy directories (`25_AI_C`, `25_AI_H`, `27`): untouched.
- Stage order, `STAGE_ORDER`, trust-classification thresholds, and chapter-qualification logic in
  `pipeline/stages/corpus_trust.py`: unchanged.

## [2.6.8] - 2026-07-31

### Context

Narrow emergency correctness release under the existing code-freeze policy,
restoring Chapter 11's completely-lost `related_chunks` field (Stage 5.4
output) and adding a new invariant-checker check to catch this defect class
automatically going forward. Found and fully root-caused by
`CH11_RELATED_CHUNKS_CONTRACT_AUDIT.md` (a read-only pre-Batch-2 audit). See
`docs/reports/V2_6_8_CH11_RELATED_CHUNKS_RESTORATION_REPORT.md` for the full report.

### Fixed

- **Chapter 11 — `related_chunks` total loss** — Stage 5.4 genuinely ran on
  2026-07-30 and linked 105 chunks (`stage_completions["5.4"].linked_chunks
  == 105`), but a later ad hoc chunk-file regeneration (the same `.strip()`
  trailing-newline bug documented in `BATCH1_CHAPTER_11_COMPLETION_REPORT.md`
  Category-B finding #6) rebuilt `chunks.md`'s content without reproducing
  Stage 5.4's `related_chunks` frontmatter additions, and the checkpoint was
  never invalidated afterward. Confirmed: both `chunks.md` and
  `RAG_Optimised.md` had zero `related_chunks` lines across all 106 L2
  chunks. Fixed by re-running the existing, UNMODIFIED Stage 5.4/5 logic
  (verbatim from `SKILL.md`) against the current `chunks.md` — no code
  change to the generation logic itself. Result: 106/106 L2 chunks now carry
  `related_chunks` (45 empty `[]`, 61 non-empty), body text byte-identical
  once `related_chunks` lines are stripped, chunk ordering unchanged, zero
  invalid/self/cross-disease/asymmetric references. Stage 6 re-run
  afterward (PASS, 106 chunks, unchanged verdict — Stage 6 does not read
  `related_chunks`). Stage 7/8 evidence left untouched (no documented Stage
  7 rerun trigger applies; Stage 8's source_lines/body/ordering were
  independently verified unchanged).

### Added

- **`verify_trusted_corpus_invariants.py::_check_stage_5_4_persistence()`** —
  new invariant: for any chapter whose checkpoint records Stage 5.4 as
  COMPLETED, independently re-derives the real L2 chunk count, confirms
  every L2 chunk in `chunks.md` and `RAG_Optimised.md` has exactly one
  `related_chunks` field with matching values between the two files, that
  checkpoint `linked_chunks` equals the real count, and that every
  relationship is a valid, same-`disease_focus`, non-self, symmetric
  reference. A chapter where Stage 5.4 never ran (no `"5.4"` key) is
  explicitly NOT flagged — only a chapter claiming COMPLETED while its
  actual output contradicts that claim is a violation, labeled
  `[STAGE-5.4-OUTPUT-PERSISTENCE-DEFECT]`. This is an invariant-checker-level
  check, deliberately NOT wired into `pipeline/stages/corpus_trust.py::classify_trust()`
  — `related_chunks` remains a zero-consumer, non-trust-gating field per the
  audit's boundary analysis (section 5); `CORPUS_TESTING_READY` is unaffected
  by this check by design.
- **`tests/test_stage_5_4_persistence.py`** — 16 new tests: genuine RED
  evidence (imports the actual pre-v2.6.8 backup module and confirms it has
  no such check at all), plus GREEN coverage for every violation class
  (total loss, partial loss, chunks/RAG mismatch, stale `linked_chunks`,
  invalid/self/cross-disease/asymmetric references, malformed list syntax,
  duplicate fields, missing `RAG_Optimised.md`) and every legitimate
  non-violation state (clean complete, all-empty, Stage 5.4 not yet run).

## [2.6.7] - 2026-07-31

### Context

Narrow emergency correctness release under the existing code-freeze policy,
fixing exactly two confirmed, independently-reproduced defects found by
`REPOSITORY_PRODUCTION_READINESS_AUDIT.md` (a read-only pre-Batch-2 audit):
a Stage 6 block-parsing blind spot (Blocker 2) and an incomplete Chapter 05
Stage 4.7 evidence trail (Blocker 1). See
`docs/reports/V2_6_7_STAGE6_AND_CH05_COMPLETENESS_FIX_REPORT.md` for the full report.

### Fixed

- **`pipeline/stages/stage_6_validation.py::check_6_1_6_2()`** — the block-splitting
  regex required the literal sequence `\n---\n` (with a trailing newline) to
  close a chunk's frontmatter. A `RAG_Optimised.md` file with no trailing
  newline at end-of-file, whose LAST chunk is empty-body (frontmatter-only,
  e.g. a Tier-3 `coverage_gap` stub), silently dropped that final chunk from
  the count — not merged into a neighbor, not double-counted, just invisible.
  Reproduced live on Chapter 11 (105 vs real 106) and Chapter 15 (86 vs real
  87). Fixed by splitting on unambiguous `chunk_id`-line boundaries first,
  then validating each individual chunk's own frontmatter closes via either
  `\n---\n` (mid-file) or `\n---` at end-of-file (no trailing newline) — never
  dependent on whether the file as a whole ends with a newline. A chunk whose
  frontmatter never closes at all now fails visibly (an explicit failure
  message) instead of being silently dropped or merged into a neighbor.
- **Chapter 11 / Chapter 15** — re-ran Stage 6 with the fixed parser:
  `chunks_checked` corrected to 106 (Ch11) and 87 (Ch15), both still PASS with
  0 hard-fails (both stubs' own frontmatter independently verified
  well-formed — no content defect, only the validator's blind spot). Neither
  chapter's `RAG_Optimised.md`/`chunks.md` was modified.
- **Chapter 05 — Stage 4.7 evidence completion** — `CompletenessChecklist.md`
  declared "Disease clusters (>=2 chunks): 14" but only 8 were ever
  individually named (6 SCATTERED + 2 SUSPECTED_GAP); the other 6 were never
  enumerated anywhere (no `complete_count` field, no `COMPLETE_DISEASES.json`).
  Re-ran Stage 4.7's exact, unmodified clustering algorithm fresh against the
  current `chunks.md`: confirmed 14 multi-chunk clusters total, reproduced
  the same 6 SCATTERED entries unchanged, and individually body-verified the
  other 8 — 4 genuinely COMPLETE disease/condition entities and 4
  NON_DISEASE_CLUSTER exclusions (topic/technique/umbrella groupings, same
  Rule L pattern as the chapter's original 3 exclusions). Arithmetic now
  reconciles exactly (6+4+4=14); `unresolved_completeness_clusters = 0` is
  backed by complete evidence, not an unverified assumption.

### Added

- `pipeline/verify_trusted_corpus_invariants.py` now independently re-derives each
  trusted chapter's actual L2 chunk count from `RAG_Optimised.md` (via the
  fixed parser) and cross-checks it against `Stage6_Validation.md`'s declared
  count and the checkpoint's own `stage_completions["6"]["chunks_checked"]`
  field — flags a `[STAGE-6-CHUNK-COUNT-DEFECT]` violation on any
  disagreement, missing field, or malformed (non-int/negative) count. This
  closes the exact detection gap that let the Chapter 11/15 defect go
  unnoticed by every previous automated check.
- `tests/test_stage_6_final_chunk_parsing.py` — RED/GREEN regression
  coverage for the parser fix (final empty-body chunk with/without trailing
  newline, single-stub files, consecutive stubs, malformed/unclosed
  frontmatter, no-duplicate-blocks invariant).
- `tests/test_pipeline/verify_trusted_corpus_invariants.py` — new Stage 6
  chunk-count cross-check tests (clean pass, checkpoint-stale,
  report-stale, the exact Ch11/Ch15-style scenario, malformed/missing
  checkpoint field).

## [2.6.6] - 2026-07-30

### Context

Emergency correctness release under the existing code-freeze policy. During
Corpus Production Batch 1 (Chapters 03, 11, 10), independent verification
found two real trust-governance defects, then a broader systemic audit of
all 9 then-trusted chapters found the same class of gap in two more
(Chapters 02, 05):

1. **Chapter 11**: its checkpoint never recorded
   `stage_completions["4.7"]["unresolved_completeness_clusters"]` at all.
   Because `pipeline/stages/trust_ledger.py::build_chapter_trust_record()` only
   forwarded this value to `classify_trust()` when the key was present
   (otherwise passing `None`), and `classify_trust()` treated `None` as
   "not considered" (skip this gate) rather than "unknown/missing," Chapter
   11 reached `CORPUS_TESTING_READY` without the Stage 4.7 completeness gate
   ever actually running for it. The underlying review was genuinely done
   (verified against Chapter 11's own 17-flag disposition table) — only the
   machine-checkable evidence field was missing.
2. **Chapter 03**: its protection marker was created as
   `Davidson_25_Ch03_Clinical_genetics_CORPUS_OUTPUT_PROTECTED.json`
   (prefixed) instead of the canonical bare `CORPUS_OUTPUT_PROTECTED.json`
   that `pipeline/stages/mutation_guard.py::PROTECTION_MARKER_FILENAME` and the trust
   ledger's "Protected?" column actually check for — the chapter showed
   `CORPUS_TESTING_READY` with `Protected? No` simultaneously.

### Fixed

- `pipeline/stages/corpus_trust.py::classify_trust()`: once a checkpoint reaches the
  `corpus_pipeline_completed`+Stage-4.5d-gate-PASS milestone, Stage
  4.6 status, Stage 4.6 `chunks_reviewed`/`total_flagged` counts (new
  parameters), Stage 4.7 `unresolved_completeness_clusters`, and Stage 8
  `source_lines_precision_summary` are now MANDATORY evidence — missing
  (`None`) or malformed (wrong type, negative, or a `bool` where an `int`
  count is expected) means "evidence is missing," never "not considered,"
  and demotes to `CORPUS_REVIEW_PENDING` with a reason naming the exact
  field. This is an additive tightening of one branch only — all `LEGACY_*`
  early-return paths (no checkpoint, pre-4.5c, pre-4.5d) are unchanged.
- `pipeline/stages/trust_ledger.py::build_chapter_trust_record()`: now extracts
  `stage_4_6_chunks_reviewed`/`stage_4_6_total_flagged` explicitly, and
  falls back to alias-resolving Stage 8's checkpoint summary field (recorded
  under at least three different names across real chapters —
  `unresolved_count`, `unresolved_l2_after_adjudication`,
  `l2_findings_unresolved`) only when no `SourceLinesPrecision.json` results
  file exists on disk (the authoritative source, built via
  `build_precision_summary()`, is always preferred).
- Added `pipeline/finalize_trusted_chapter.py`: the single canonical,
  dry-run-by-default chapter-finalization command. Refuses (non-zero exit)
  unless `classify_trust()` returns `CORPUS_TESTING_READY`; refuses on a
  Chapter-03-style prefixed-marker conflict without auto-renaming; requires
  both `--write` and `--authorize` for a durable write; verifies marker
  hashes and re-reads the written state before reporting success.
- Added `pipeline/verify_trusted_corpus_invariants.py`: read-only, checks every
  chapter the committed `CORPUS_TRUST_STATUS.md` declares
  `CORPUS_TESTING_READY` against a fresh recomputation, explicitly naming
  Chapter-03-style (marker filename) and Chapter-11-style (missing evidence
  field) failures.
- Nine-chapter re-evaluation (02, 03, 05, 06, 10, 11, 13, 14, 15): Chapters
  02 and 05 demoted to `CORPUS_REVIEW_PENDING` (genuinely missing Stage
  4.6/4.7 evidence that could not be honestly reconstructed for every
  required field — see `docs/reports/V2_6_6_FAIL_CLOSED_FINALIZATION_REPORT.md` for the
  per-chapter evidence trail). Chapters 03, 06, 10, 11, 13, 14, 15 confirmed
  `CORPUS_TESTING_READY` under the new fail-closed classifier. Two
  chapter-local checkpoint evidence repairs applied (Chapter 02's Stage 4.6
  `total_flagged`, Chapter 05's Stage 4.7 `unresolved_completeness_clusters`)
  — both transcribed directly from already-existing, unambiguous detailed
  artifacts (`Remap_Log.md` / `CompletenessChecklist.md`), never fabricated.

See `docs/reports/V2_6_6_FAIL_CLOSED_FINALIZATION_REPORT.md` for full RED-before evidence,
design rationale, and per-chapter re-evaluation detail.

## [2.6.5] - 2026-07-29

### Context

Emergency correctness release under the existing code-freeze policy, triggered
by the Chapter 14 frozen-pipeline stress run. Two issues were found: (1) a
CATEGORY D defect — at least four independent `source_lines` parsing
implementations (`pipeline/stages/stage_4_5d_clinical_fidelity.py::resolve_source_span()`,
`pipeline/stages/source_lines_precision.py::_get_declared_segments()`,
`run_stage_4_5d.py::_l1_span()`, `stage_4_6_sonnet_verification.py::_get_source_lines()`)
each silently dropped comma-separated single-line `source_lines` segments; a
seeded test proved this can hide a real clinical-content corruption (a
paracetamol dose ceiling silently raised from 4g to 40g) from Stage 4.5d's
detectors entirely, since the segment carrying the correct value was never
included in the comparison span; and (2) Chapter 14 had been marked
`trusted_for_downstream_use: true` while 238/283 Stage 4.6 semantic-review
candidates and 18/35 Stage 4.7 completeness clusters remained unreviewed. See
`docs/reports/V2_6_5_EMERGENCY_INTEGRITY_FIX_REPORT.md` for full detail.

### Fixed

- **CATEGORY D**: added `pipeline/stages/source_lines_parser.py`, the single canonical
  `source_lines` parser/serializer for the whole pipeline. Migrated all four
  duplicate implementations to delegate to it. Added
  `tests/test_no_duplicate_source_lines_parser.py`, a repository guard that
  fails the suite if another independent parsing implementation is
  reintroduced.
- Added `stages.corpus_trust.classify_trust()` support for a `CORPUS_REVIEW_PENDING`
  classification that explicitly accounts for unresolved Stage 4.6/4.7 review,
  distinct from `CORPUS_TESTING_READY` — a broad `trusted_for_downstream_use`
  boolean must never conceal incomplete semantic-type or completeness review.
- Chapter 14 reclassified `CORPUS_REVIEW_PENDING` pending completion of its
  outstanding Stage 4.6/4.7 review (Option B, `docs/reports/V2_6_5_EMERGENCY_INTEGRITY_FIX_REPORT.md`
  Part 7); its `CORPUS_OUTPUT_PROTECTED.json` marker was updated transparently
  to reflect this, not deleted.

## [2.6.4] - 2026-07-29

### Context

Corpus-Scale Gate Closure — the one narrowly-scoped sprint recommended by
`CORPUS_SCALE_READINESS_REVIEW.md` (Part 5, Path B) before canonical corpus
processing resumes, closing exactly the three `MUST FIX` items identified in
that review and `GENERALIZATION_VALIDATION_REPORT.md`. Does **not** redesign
the architecture, and does not implement retrieval/embeddings/BM25/hybrid
search/reranking/generation evaluation/clinical or educational benchmarking —
see `docs/reports/V2_6_4_CORPUS_SCALE_GATE_CLOSURE_REPORT.md` for full evidence. Per that
review's Part 4/5, the architecture now enters **CODE FREEZE — emergency
correctness fixes only**.

### Added

- `pipeline/stages/stage_2_repair.py` — Stage 2's `is_clinical()` guard and full
  repair sequence (Fixes 1-9), extracted from an inline `SKILL.md` code
  block into a shared, tested module. Fixes the confirmed Chapter 05
  content-loss bug: decimal-numbered MCQ stems (`5.1.`, `5.1.2.`) and
  dash-prefixed options (`- A.`, `- A)`) are now protected, and protection
  extends to the whole paragraph containing a protected line (a wrapped
  multi-line stem's continuation text is otherwise indistinguishable from
  ordinary prose and was still swept even after the regex-only fix).
- `pipeline/stages/source_lines_precision.py`: `bullet_gap_only` classification
  (conservative short-bullet-list heuristic, found via the real Chapter 02
  Box 2.6 hypersensitivity-reactions list); `ADJUDICATION_DECISION_VALUES`
  (`CHECKER_FALSE_POSITIVE` / `HUMAN_CONFIRMED_METADATA_DEFECT`),
  `apply_source_lines_adjudication()`, `unresolved_findings()`,
  `build_precision_summary()` (L2-only by default — L1's imprecision is
  advisory/diagnostic only per Rule G, never trust-blocking); `chunk_level`
  now reported per result.
- `pipeline/stages/trust_ledger.py` + `pipeline/generate_corpus_trust_ledger.py` — deterministic
  `CORPUS_TRUST_STATUS.md` generator: `discover_chapter_dirs()`,
  `build_chapter_trust_record()`, `build_corpus_trust_ledger()`,
  `render_corpus_trust_status()`. Dry-run/read-only by default; a durable
  write requires `--write --in-place` through `pipeline/stages/mutation_guard.py`'s
  existing guarded-write contract. Never infers trust from a chapter
  directory's mere presence of `RAG_Optimised.md`.
- `pipeline/stages/corpus_trust.py`: new `CORPUS_REVIEW_PENDING` classification —
  a chapter that passed Stage 6 and the Stage 4.5d gate but whose
  source-lines precision review is untested or has unresolved findings can
  no longer receive `CORPUS_TESTING_READY`. New `source_lines_precision_summary`
  and `protection_marker` parameters on `classify_trust()` (both optional,
  backward-compatible via `None` — see the function's docstring for exact
  scoping); `protection_marker_present` is disclosed as a separate safety
  field, never an input to the classification decision itself.
- `pipeline/stages/checkpoint_migration_v2_6_4.py` (CP-08) + `scripts/maintenance/checkpoint_migrate_v2_6_4.py`
  — migrates a checkpoint whose `next_stage_to_run` predates the new `"8"`
  STAGE_ORDER entry (an ordinary terminal `None`, or Chapter 05's own
  stale-but-Stage-7-actually-complete `"7"` value) forward to `"8"`. Same
  dry-run/backup/verify contract as CP-07.
- `SKILL.md`: new "STAGE 8 — Corpus Gate Closure" section (source-lines
  precision + trust classification, runs automatically after Stage 7); new
  "ARCHITECTURE STATUS" section declaring the post-v2.6.4 code freeze.
- `tests/test_stage_2_mcq_preservation.py`,
  `tests/test_source_lines_bullet_gap_and_adjudication.py`,
  `tests/test_corpus_review_pending.py`, `tests/test_trust_ledger.py`,
  `tests/test_trust_ledger_staleness.py`, `tests/test_cp08_stage8_append.py`,
  `tests/test_ch02_integration_regression.py` +
  `tests/fixtures/ch02_regression/` — see
  `docs/reports/V2_6_4_CORPUS_SCALE_GATE_CLOSURE_REPORT.md` for RED/GREEN evidence.

### Changed

- `pipeline/checkpoint_utils.py`: `PIPELINE_VERSION` 2.6.3 → 2.6.4; `STAGE_ORDER`
  gained `"8"` (appended after `"7"`); new `corpus_gate_closure_completed`
  monotonic milestone flag and `CORPUS_GATE_CLOSURE_COMPLETED` pipeline
  status.
- `scripts/maintenance/run_source_lines_precision.py`: fixed a real bug where `is_new_file=True`
  was hardcoded regardless of whether the target file already existed,
  which crashed against a protected chapter with pre-existing precision
  reports (found while running this stage for real against Chapter 05,
  which already had pre-v2.6.4 `SourceLinesPrecision.md`/`.json` files from
  its own retrofit history); `out_dir`/`prefix` are now threaded through to
  `guarded_write_file()` so the protection-marker check can resolve at all.
- `CORPUS_TRUST_STATUS.md`: regenerated for real via the new guarded CLI.
  Chapter 02 is now listed (previously entirely absent — the exact staleness
  this release's MUST-FIX #3 exists to prevent from recurring). Chapter 05
  and Chapter 02 both reclassified `CORPUS_TESTING_READY` after real Stage 8
  runs + adjudication of every flagged finding (all confirmed
  `CHECKER_FALSE_POSITIVE` — short bullet/fragment-list under-anchoring, no
  confirmed metadata defects on either chapter). `25_AI_C`/`25_AI_H`/`27`
  remain correctly quarantined, unchanged.
- `02/CORPUS_OUTPUT_PROTECTED.json` — created for the first time (Chapter 02
  previously had no protection marker at all despite passing every gate
  Chapter 05 had).

### Fixed

- Stage 2's MCQ-stem/option content-loss bug (see Added, `pipeline/stages/stage_2_repair.py`).
- Chapter 02's 3 real `bullet_gap_only` source-lines findings (Box 2.6,
  the biologics/Fig 2.6 box, the Fig 2.8 prescription-chart box) and
  Chapter 05's 11 real L2 findings (4 heading-only-chunk `UNRESOLVED`, 7
  short-fragment-box `OVER_INCLUSIVE`) — all adjudicated `CHECKER_FALSE_POSITIVE`
  with a per-chunk rationale after direct verbatim confirmation against
  `REPAIRED_S2.md`; zero confirmed metadata defects found on either chapter.

## [2.6.3] - 2026-07-29

### Context
A narrowly-scoped safety and reproducibility release addressing three
process risks exposed during v2.6.2: (1) checkpoint reads could silently
migrate/mutate in-memory state even for audit/diagnostic use; (2) direct
verification/repair scripts could mutate trusted production outputs with
no authorization gate (a real, disclosed incident during v2.6.2 — see
`docs/reports/V2_6_2_STABILIZATION_REPORT.md` §14); (3) Chapter 05's Stage 4.5d
adjudication decisions were replayable but only as executable code with
prose comments, not as an immutable, independently auditable evidence
artifact. Does NOT implement Phase 2, any new evaluation metric, or raise
readiness beyond `CORPUS TESTING READY — Chapter 05 only`. Full evidence in
`docs/reports/V2_6_3_SAFETY_GUARDRAILS_REPORT.md`.

### Added
- `pipeline/checkpoint_utils.py`: `read_checkpoint()` (pure read, never writes,
  never migrates — the sanctioned API for audits/trust classification/
  diagnostics/tests/legacy-checkpoint inspection), `load_checkpoint_for_run()`
  (explicit pipeline-execution load, migrates in-memory only, same
  behavior the old `load_checkpoint()` always had), `migrate_checkpoint_schema()`
  (explicit, disk-persisting migration; dry-run by default; takes a
  timestamped backup before writing). `load_checkpoint()` retained as a
  documented, unambiguous alias for `load_checkpoint_for_run()`.
  `PIPELINE_VERSION` 2.6.2 → 2.6.3.
- `pipeline/stages/mutation_guard.py`: `CORPUS_OUTPUT_PROTECTED.json` production-
  output protection marker (build/read/write, sha256-hashed evidence
  fields, explicit non-clinical disclaimer embedded in every marker);
  `require_authorization_for_in_place_mutation()` (refuses a mutation
  missing `--write`/`--in-place`/`--backup`, naming exactly which flag(s)
  are missing); `guarded_write_file()` (dry-run-by-default single-file
  write helper implementing backup → temp-write → validate → atomic
  replace → hash-verify → automatic rollback on failure).
- `pipeline/stages/adjudication_manifest.py`: `build_candidate_set_hash()`,
  `validate_manifest()`, `apply_validated_manifest()` — schema/hash/
  candidate-count/duplicate-ID/decision-value/rationale/stale-legacy-ID/
  confirmed-corruption-re-verification validation, never partially
  applying an invalid manifest.
- `tests/fixtures/ch05_regression/clinical_fidelity_adjudication_manifest.json`
  (also copied to `05/Davidson_25_Ch05_Nutritional_factors_in_disease_clinical_fidelity_adjudication_manifest.json`) —
  the real Chapter 05 adjudication (7 current candidates, all
  `false_positive`, each with a per-candidate rationale, source/chunks/
  candidate-set sha256-locked), replacing the blanket
  `{c["candidate_id"]: "false_positive" for c in candidates}` comprehension
  previously used both in `scripts/chapter_repairs/apply_ch05_adjudication.py` and in
  `tests/test_ch05_integration_regression.py`.
- `05/CORPUS_OUTPUT_PROTECTED.json` — real protection marker for Chapter 05
  (the only corpus-certified chapter), generated from its actual source/
  chunks/RAG_Optimised/gate file hashes.
- `scripts/maintenance/run_stage_4_5d.py`: `source_mapping` block on the Stage 4.5d gate output
  (`chunks_using_source_lines`, `chunks_using_context_fallback`,
  `chunks_with_malformed_source_lines`, `source_lines_precision_gate_status`
  always `"ADVISORY_ONLY"`, `semantic_completeness_claimed` always `False`,
  plus `source_lines_precision_tested`/over-/under-inclusive/unresolved
  counts pulled from `{PREFIX}_SourceLinesPrecision.json` when present).
  Non-blocking, disclosure-only.
- New test files: `tests/test_checkpoint_access_modes.py` (20 tests,
  including byte-identity proof against the REAL `25_AI_H` checkpoint),
  `tests/test_mutation_guard.py` (19 tests), `tests/test_run_stage_4_5d_cli_guardrails.py`
  (6 tests, including default-CLI-non-mutation proof against a protected
  fixture), `tests/test_adjudication_manifest.py` (21 tests, including the
  real Chapter 05 manifest validated against a fresh Stage 4.5d run),
  `tests/test_source_mapping_disclosure.py` (7 tests),
  `tests/test_mutation_safety_declarations.py` (repo-wide scan for
  executable scripts capable of mutation but lacking an explicit safety
  declaration).

### Changed
- `scripts/maintenance/run_stage_4_5d.py`: CLI (`__main__`) is now non-mutating by default —
  overwriting existing Stage 4.5d outputs requires `--write --in-place`
  (`--backup` too once the chapter is protected); a first-time run on a
  chapter with no existing outputs requires only `--write`. Without
  authorization, results are computed identically but written to a
  `.dryrun_stage_4_5d/` report-only subdirectory instead. The underlying
  `run_stage_4_5d(out_dir, prefix, write_dir=None)` function is unchanged
  for library/test callers.
- `scripts/chapter_repairs/apply_ch05_adjudication.py`, `scripts/chapter_repairs/regenerate_rag_optimised_ch05.py`,
  `scripts/chapter_repairs/apply_source_lines_corrections_ch05.py`, `scripts/chapter_repairs/rerun_stage6_ch05.py`,
  `scripts/maintenance/run_source_lines_precision.py`, `scripts/chapter_repairs/migrate_ch05_schema_v2.py`: each now
  requires explicit authorization (`--write`, `--in-place` for existing-file
  mutation, `--backup` for a protected chapter, or `--apply` for the
  migration script) before mutating; default invocation computes and
  reports without writing to the real chapter output.
- `pipeline/stages/corpus_trust.py`: added `load_checkpoint_for_classification()`,
  a thin wrapper around `checkpoint_utils.read_checkpoint()` — the
  sanctioned way to load a checkpoint for trust classification going
  forward, never `load_checkpoint()`/`load_checkpoint_for_run()`.
- `tests/test_ch05_integration_regression.py`: the three call sites that
  built a blanket `{candidate_id: "false_positive"}` decisions dict now
  call `_apply_real_ch05_manifest()`, which validates and applies the real
  adjudication manifest instead.
- `SKILL.md`, `README.md`, `pipeline/checkpoint_utils.py`: version 2.6.2 → 2.6.3.
- `CORPUS_TRUST_STATUS.md`: version reference updated; added a note
  distinguishing `CORPUS_OUTPUT_PROTECTED.json` (a narrower "don't casually
  overwrite" claim) from this file's own trust classification.

### Fixed
- The exact incident disclosed in `docs/reports/V2_6_2_STABILIZATION_REPORT.md` §14 (a
  direct `scripts/maintenance/run_stage_4_5d.py` CLI invocation against Chapter 05's real
  output regenerated fresh, unadjudicated candidates and temporarily
  reverted a PASSING gate to BLOCKED) is now structurally prevented by
  default — proven by `tests/test_run_stage_4_5d_cli_guardrails.py` and by
  re-running the exact same CLI invocation against the real Chapter 05
  directory during this release (see `docs/reports/V2_6_3_SAFETY_GUARDRAILS_REPORT.md`).

## [2.6.2] - 2026-07-29

### Context
A narrowly-scoped stabilization release, addressing findings from
`COMPLETE_SKILL_BREAKDOWN.md` (a read-only, repository-grounded audit of
v2.6.1). Does NOT implement Stage 4.5e/4.6b/4.7b/6.5, retrieval evaluation,
generation evaluation, or clinical/educational benchmarks — those remain
future work, unchanged from prior releases. Full evidence (baseline/RED/
GREEN test results, migration output, Chapter 05 integration result) is
recorded in `docs/reports/V2_6_2_STABILIZATION_REPORT.md`.

### Fixed
- **Three-way version mismatch** (audit finding): `SKILL.md` (2.6.1),
  `checkpoint_utils.PIPELINE_VERSION` (2.6.0), and `README.md` (2.6.0) now
  all read `2.6.2`, and `CHANGELOG.md`'s latest heading matches. Enforced
  going forward by `tests/test_repository_version_consistency.py`, which
  defines the exact declaration location in each of the four files and
  fails naming which ones disagree.
- **Stage 4.5d candidate ID collisions** (audit finding): the prior
  `4.5d-{check}-{chunk_id}-{value}` format collided whenever two distinct
  candidates on the same chunk/check shared the same source/chunk value.
  New format `4.5d-{check}-{chunk_id}-{ordinal}-{stable_hash}`, assigned by
  a new `assign_candidate_ids()` post-processing pass (called from
  `run_all_detectors_for_chunk()` and `detect_boundary_loss()`) —
  guarantees uniqueness even when every other field matches. Existing
  adjudication files are unaffected without action (decisions live on each
  record itself, not in an externally-keyed index); `migrate_legacy_candidate_ids()`
  is available as an explicit, opt-in re-ID pass for an old-format file,
  preserving every other field (`decision`, `status_label`, `severity`,
  `re_verified`) untouched.
- **`INTENTIONAL_SECTION_SPLIT` unreachability** (audit finding):
  `detect_boundary_loss()` previously always passed
  `split_at_declared_heading=False`, so this classification — implemented
  and unit-tested in `classify_boundary()` — could never actually be
  produced by the real detector. Fixed via the **preferred (reachability)
  approach**, not the removal fallback: when both halves of a drug/dose
  boundary carry `source_lines` and `repaired_s2_text` is supplied, a real
  Markdown heading line found in the source gap between them is now
  checked (`_heading_exists_between()`) — genuine structural evidence, not
  an inference from mere chunk adjacency. `scripts/maintenance/run_stage_4_5d.py` updated to
  pass this evidence through. Chosen over the removal fallback because the
  reachability implementation turned out to be tractable within this
  release's scope (a single new helper function plus wiring) and preserves
  more diagnostic value than deleting the classification. Known limitation:
  still a line-scan heuristic (a heading present for an unrelated reason
  would still classify this way) — not semantic verification of editorial
  intent.

### Added
- **Checkpoint provenance model** (`pipeline/checkpoint_utils.py`): replaces the
  single, ambiguous `chapter_info.pipeline_version` field (audit finding —
  documentation and warning logic disagreed about whether it meant
  "creation version" or "currently governing version") with three explicit
  fields: `checkpoint_created_with_pipeline_version` (set once at creation,
  never overwritten by any function in this module),
  `last_processed_with_pipeline_version` (advanced only by
  `mark_stage_complete`/`mark_stage_blocked`/`mark_stage_failed`/
  `mark_stage_in_progress` — i.e. only when a stage genuinely executes),
  and `checkpoint_schema_version` (`"2.0"`). `migrate_checkpoint_schema_to_v2()`
  losslessly migrates an old-schema checkpoint on every load (via
  `load_or_create_checkpoint`) — preserves a legacy checkpoint's historical
  creation version exactly (Chapter 05's `"2.5.1"` is NOT overwritten with
  `"2.6.2"`), uses the literal string `"UNKNOWN"` for a checkpoint with no
  historical version at all (never invented), and is idempotent. Every
  `stage_completions[key]` entry written by a `mark_stage_*()` call now
  also records `executed_with_pipeline_version` — never retroactively
  added to historical entries that predate this field.
  `check_version_compatibility()` produces a non-fatal warning
  distinguishing creation/last-processed/installed versions
  ("Checkpoint was created under vX and last processed under vY. Installed
  pipeline is vZ.") — a version difference alone is never treated as
  corruption or used to block resume; a missing blocking stage still
  requires the normal stage-order migration/rerun policy independent of
  this check. `pipeline/stages/checkpoint_migration.py`'s CP-07
  `_backfill_missing_fields()` now delegates to
  `migrate_checkpoint_schema_to_v2()` (single source of truth) rather than
  duplicating the old ambiguous-field backfill logic.
- **`pipeline/stages/corpus_trust.py`**: deterministic trust classifier,
  `classify_trust(checkpoint, clinical_fidelity_gate, has_stage6_validation_file,
  has_coverage_gaps_file)`. Replaces independent, hand-edited trust
  classification per chapter/document — that process produced the
  confirmed `25_AI_H` misclassification below. Deliberately has no
  "does `RAG_Optimised.md` exist" input; never will. Returns
  `{classification, trusted_for_downstream_use, reasons, required_action}`.
  Verified against all four real chapters during this release: Chapter 05
  -> `CORPUS_TESTING_READY`; `25_AI_C` -> `LEGACY_UNCHECKPOINTED`; `25_AI_H`
  -> `LEGACY_STALE_CHECKPOINT`; `27` -> `LEGACY_UNGATED`.
- **`tests/test_ch05_integration_regression.py`**: repeatable pytest
  coverage for Chapter 05 (audit finding — previously only one-off scripts
  existed). Level A: deterministic post-chunk pipeline (Stage 4.5c through
  Stage 6) against frozen fixture artifacts in
  `tests/fixtures/ch05_regression/` (manifest + copied approved files,
  `sha256`-verified), run in a temporary directory — confirmed to never
  touch the real `05/` output directory. Level B: checkpoint-orchestration
  test exercising the full `STAGE_ORDER` sequence (1 through 7) with
  synthetic stage results, verifying valid transitions, that blocked/failed
  stages never advance, milestone-flag timing (`corpus_pipeline_completed`
  at Stage 6, `advisory_scorecard_completed` only after Stage 7 actually
  runs — never implied early), and `executed_with_pipeline_version`
  stamping. Neither level reproduces Stage 4B's real LLM subagent call —
  that remains untested inside pytest, by design (irreducibly
  non-deterministic).
- **Stage 4.6 deterministic unit tests** (`tests/test_pipeline/stage_4_6_sonnet_verification.py`,
  audit finding — this module had zero dedicated tests): covers
  `TITLE_RULES`/`BODY_RULES` classification, `_regex_remap_all`'s
  title-only auto-apply behavior, unparsed-chunk/degraded-ratio metadata
  construction, `export_for_manual_review()`/`apply_manual_corrections()`,
  and the `anthropic`-package-missing fallback path
  (`needs_manual_verification: True`). The Anthropic API itself is mocked
  (`unittest.mock`) for the success-path and malformed-response-handling
  tests — no live API call is made. These tests prove deterministic
  control flow and error handling, not semantic classification accuracy.
- Boundary-loss integration tests (`tests/test_stage_4_5d_detectors.py`):
  confirm the real `detect_boundary_loss()` — not just the pure
  `classify_boundary()` function — can produce all four classifications,
  including the newly-reachable `INTENTIONAL_SECTION_SPLIT`.
- `tests/test_checkpoint_provenance.py`, `tests/test_candidate_id_collision.py`,
  `tests/test_corpus_trust.py`, `tests/test_repository_version_consistency.py`.

### Corrected
- **`25_AI_H` trust classification** (audit finding, high severity): was
  incorrectly documented (in `CORPUS_TRUST_STATUS.md` and an earlier
  session report) as having no checkpoint, identical to `25_AI_C`. It
  actually has a real, ancient checkpoint (dated 2026-07-22) predating
  Stage 4.5c and `PIPELINE_VERSION` tracking entirely, with a pre-v2.6.0
  literal `pipeline_status: "COMPLETED"` string. Corrected classification:
  `LEGACY_STALE_CHECKPOINT` / `INVALID_FOR_TRUSTED_DOWNSTREAM_USE` /
  `FULL_CANONICAL_RERUN_REQUIRED`. New policy, stated explicitly:
  checkpoints predating Stage 4.5c cannot be upgraded to corpus-certified
  status by metadata migration alone — they require a full canonical
  rerun, since the evidence needed to reconstruct modern stage completion
  does not exist and synthesizing it would create false provenance. The
  historical checkpoint file itself was NOT altered or deleted — preserved
  as historical evidence, with a new
  `25_AI_H/LEGACY_STALE_CHECKPOINT_DO_NOT_TRUST.md` marker explaining why
  it must not be trusted.

### Known limitations carried forward, unchanged in this release
- Stage 4.5d's regex detectors cannot prove semantic completeness (see
  [2.6.0]/[2.6.1] entries) — unchanged.
- Stage 4B (chunking) remains an LLM subagent call, non-deterministic, and
  is not reproduced inside pytest by the new Chapter 05 integration tests
  or anywhere else.
- `source_lines` precision (`pipeline/stages/source_lines_precision.py`) remains
  advisory-only — not wired into `STAGE_ORDER`, unchanged from [2.6.1].
  The 23 `OVER_INCLUSIVE` findings remaining on Chapter 05 were not
  further addressed in this release.
- Stage 4.5e, 4.6b, 4.7b, and 6.5 remain unimplemented.
- Retrieval, generation, clinical, and educational evaluation remain
  unimplemented.
- No chapter except Chapter 05 is corpus-certified under the current
  pipeline. Readiness classification is unchanged from [2.6.1]:
  `CORPUS TESTING READY — Chapter 05 only`. This release does not raise
  that classification to `CORPUS PRODUCTION READY`.

## [2.6.1] - 2026-07-29

### Context
Adjudicating Chapter 05's Stage 4.5d candidates (v2.6.0) found that 55/55
candidates were false positives with a common root cause on 5 of 228
chunks: imprecise `source_lines` frontmatter (either excluding real
content — a table — or including unrelated interleaved content — a
different box). A follow-up whole-chapter scan (not gated by whether a
mismapped chunk happened to also trigger a Stage 4.5d content-pattern
candidate) found the problem is much broader than those 5 chunks: 29/228
chunks (4 under-inclusive, 25 over-inclusive) on this one chapter alone.

### Added
- **`pipeline/stages/source_lines_precision.py`** — measurement-only checker
  (never auto-applies) that locates each chunk's own body content directly
  in `REPAIRED_S2.md` via anchor matching (sentence-level for prose,
  row-level for tables — Stage 4.5c's equivalent explicitly skips table
  rows, wrong for this purpose since a missed table is exactly the
  UNDER_INCLUSIVE failure pattern), then classifies the chunk's declared
  `source_lines` as `PRECISE` / `UNDER_INCLUSIVE` / `OVER_INCLUSIVE` /
  `UNRESOLVED` (too little body text to anchor confidently — mostly
  heading-only stub chunks, not a red flag) with a `suggested_segments`
  correction. Disambiguates a repeated-boilerplate anchor (a running
  header appeared 12 times on Chapter 05) by preferring the occurrence
  nearest the chunk's own declared range, not just the first occurrence in
  the document — an earlier draft without this produced dozens of false
  `UNDER_INCLUSIVE` results from matching the wrong occurrence.
  Over-inclusion requires a genuine INTERNAL gap between two matched
  content clusters that both fall within the declared range (the real
  "unrelated box interleaved mid-chunk" signature) — comparing raw
  declared-vs-matched span size alone was tried first and falsely flagged
  roughly a third of the chapter purely from edge-trimming (this tool never
  anchors a chunk's own heading line, so a precise chunk still looks a
  line or two "short" at its start).
  `apply_corrections()` exists but is never called automatically — same
  human-in-the-loop posture as Stage 4.5d's adjudication requirement,
  scaled to a metadata-precision check rather than a clinical-content one.
- `scripts/maintenance/run_source_lines_precision.py` — whole-chapter runner, writes
  `{PREFIX}_SourceLinesPrecision.md`/`.json`. Advisory only; does not touch
  the checkpoint or gate anything.
- SKILL.md Stage 4B subagent prompt, new rule 8: documents both failure
  patterns directly in the chunking instructions (prevention for future
  chapters), citing the confirmed Chapter 05 cases.

### Not done in this release
- Not wired into the checkpoint system as a blocking or tracked pipeline
  stage — it's a standalone advisory tool, matching Stage 7's zero-cost/
  advisory posture, not Stage 4.5d's blocking one. Formalizing it into
  `STAGE_ORDER` would need the same rigor (tests, checkpoint states,
  migration) Phase 0/1 gave Stage 4.5d — not done here.
- Chapter 05's chunks.md `source_lines` fields were NOT corrected by this
  release — the checker's findings are reported, not applied. Whether to
  apply `apply_corrections()` for the high-confidence findings (the 4
  `UNDER_INCLUSIVE` chunks, the large-gap `OVER_INCLUSIVE` ones like
  L2-118/L2-126) against an already-certified chapter is a decision left
  to the user.

## [2.6.0] - 2026-07-29

### Context
Implements Phase 0 (governance/checkpoint fixes) and Phase 1 (Stage 4.5d
clinical fidelity gate) of `docs/architecture/IMPLEMENTATION_MAP.md`, itself scoped from
`DAVIDSON_RAG_COMPLETE_EVALUATION_GUIDE_v2.0.md` — CP-01 through CP-07
(CP-07 identified while writing the implementation map, not in the original
guide) plus a new blocking Stage 4.5d. Full evidence (RED/GREEN test runs,
migration dry-run/apply output, Chapter 05 regression result) is recorded in
`docs/reports/PHASE0_PHASE1_REPORT.md`. Phases 2–7 remain future work, not implemented.

### Added
- **`pipeline/stages/` package** — testable modules extracted from SKILL.md's inline
  blocks, limited to the stages with verdict/decision logic that needed
  regression coverage: `stage_3_reaudit.py`, `stage_4_5c_coverage.py`,
  `stage_4_6_decision.py`, `stage_4_7_serialize.py`,
  `stage_4_5d_clinical_fidelity.py`, `stage_6_validation.py`,
  `checkpoint_migration.py`. SKILL.md's inline blocks are now thin callers
  over these. Every other stage's inline logic is unchanged (per the
  "limited extraction scope" decision — no refactor of stable stages beyond
  what CP-01–07/Stage 4.5d required).
- **CP-01**: `mark_stage_complete()` now raises `ValueError` on an unknown
  `stage_key` instead of silently setting `pipeline_status` to `COMPLETED`.
- **CP-02**: new `mark_stage_blocked()` / `mark_stage_failed()` /
  `mark_stage_in_progress()` functions. Every stage with a real pass/fail
  verdict (Stage 3, 4.5, 4.5c, 4.5d, 4.6, 6) now branches on that verdict
  instead of calling `mark_stage_complete()` unconditionally — Stage 4.5's
  FAIL-verdict case was found during the final call-site audit (constraint
  11), not in the original CP list, and fixed the same way.
- **CP-03**: Stage 1's skip-Stage-2 path now writes an exact
  `shutil.copyfile()` of `SOURCE_PATH` to `{PREFIX}_REPAIRED_S2.md` with
  `repair_mode: pass_through` — previously it advanced the checkpoint
  without ever writing that file, which Stage 3 unconditionally reads.
- **CP-04**: Stage 4.7 now writes `{PREFIX}_SCATTERED.json`,
  `{PREFIX}_SUSPECTED_GAP.json`, `{PREFIX}_COMPLETE_DISEASES.json` (new —
  previously untracked) with a `{schema_version, pipeline_version, chapter,
  generated_at, data}` envelope (correction G), written atomically. Closes a
  self-consistency gap: Stage 5.2 already assumed `SCATTERED.json` existed;
  Stage 4.7 never actually produced it.
- **CP-05 + correction H**: Stage 4.6 now blocks when
  `chunks_unparsed/chunks_reviewed > 10%` (previously computed but never
  read by the checkpoint call), and explicitly `FAILED`s — never silently
  treated as a clean 0%-unparsed pass — when `chunks_reviewed == 0`.
- **CP-06 + correction I**: `pipeline_state.pipeline_status` now
  distinguishes `CORPUS_PIPELINE_COMPLETED` (Stage 6 passed) from
  `ADVISORY_SCORECARD_COMPLETED` (Stage 7 also ran) instead of a single
  `COMPLETED` value. Independent monotonic boolean flags
  (`corpus_pipeline_completed`, `advisory_scorecard_completed`,
  `rag_system_evaluation_completed` — the last a Phase 5+ placeholder, never
  set True by any code in this release) back the same distinction so no
  caller has to rely on string-matching one mutable field.
- **CP-07**: `scripts/maintenance/checkpoint_migrate_v2_6_0.py` / `pipeline/stages/checkpoint_migration.py`
  — one-shot migration for checkpoints written before `"4.5d"` was inserted
  into `STAGE_ORDER`. Idempotent via an explicit `migrations_applied`
  marker (not stage-key presence, which would re-trigger forever before
  Stage 4.5d has ever run for a chapter — correction A). Dry-run by
  default; `--apply` backs up, writes, and reloads-to-verify before
  returning, raising if verification fails.
- **Stage 4.5d — Clinical Fidelity Gate** (new, blocking, inserted between
  Stage 4.5c and Stage 4.5b in `STAGE_ORDER`). Two-phase: automated
  detection across 11 sub-checks (numeric, unit, inequality, range, dose,
  duration, frequency, negation, polarity, sequence, boundary-loss) +
  mandatory human adjudication of every candidate — never auto-cleared or
  auto-failed on regex alone. Boundary-loss findings are classified
  `CRITICAL_SEPARATION` / `SAFE_LINKED_SPLIT` / `INTENTIONAL_SECTION_SPLIT`
  / `AMBIGUOUS` (correction F); only a verified `CRITICAL_SEPARATION` is a
  hard failure. Source-span resolution prefers each chunk's own
  `source_lines` mapping, falling back to a 5-word local context window
  only when that's missing/malformed (correction E). Every result carries
  an explicit `truth_status` (`MEASURED` / `DEFINED_PATTERN_SET_ONLY` /
  `semantic_completeness_claimed: false`) so a 0-candidate result is never
  described as full semantic verification (correction D).
  `{PREFIX}_ClinicalFidelityGate.json` is the single source of truth Stage
  6's new Check 6.4b reads (correction C) — not just
  `ClinicalFidelityFailures.json`, since an unadjudicated candidate isn't
  yet classified as a confirmed failure and must not be treated as
  equivalent to "clean." `scripts/maintenance/run_stage_4_5d.py` is the direct/regression
  entry point; SKILL.md's Stage 4.5d block wraps it with checkpoint calls.
- **Stage 6 Check 6.4b**: hard-fails a chapter if Stage 4.5d's gate is
  missing, not `PASS`, has any unresolved candidate, has any unresolved
  confirmed corruption, or has any required detector not tested.

### Changed
- `STAGE_ORDER` gains `"4.5d"` between `"4.5c"` and `"4.5b"`.
  `PIPELINE_VERSION` bumped `2.5.1` -> `2.6.0`.
- `pipeline/stage_4_6_sonnet_verification.py`: unchanged — its existing
  `_build_metadata()` already computed the degraded-run ratio correctly;
  the bug was SKILL.md never reading it (CP-05).

### Migration
Chapter 05's real checkpoint (the only chapter run through the actual
checkpoint system prior to this release — see `docs/reports/PHASE0_PHASE1_REPORT.md` for
the other three chapters' status) was stranded at `next_stage_to_run: null`
/ `pipeline_status: COMPLETED` and would never have picked up Stage 4.5d
through normal resume logic. `checkpoint_migrate_v2_6_0.py --apply` rewound
it to `next_stage_to_run: "4.5d"`, `pipeline_status: "IN_PROGRESS"`,
verified on reload, backup preserved alongside the checkpoint file.

## [2.5.1] - 2026-07-28

### Context
A user-submitted "checkpoint and resume governance" document proposed
per-artifact output-hash verification on resume (treating any hash mismatch
as corruption requiring a rerun). Evaluated against this pipeline's own
documented rules: Rule D (Stage 4.5 splice-fix a failed chunk directly into
`chunks.md`, no subagent re-run) and Rule F (Stage 2 — restore piracy-swept
clinical content directly into `REPAIRED_S2.md`) both require hand-editing a
file *after* its producing stage is already marked `COMPLETED`. A
hash-as-validity-gate would treat every one of those sanctioned edits as
corruption. Adopted the parts of that document's intent that don't conflict
with this instead: atomic writes (a real gap) and a non-blocking audit trail
for manual edits (hashing for visibility, never for gating). The document's
other proposals (a six-parallel-worker Stage 4.3, per-stage directory trees,
`STAGE_COMPLETE.json` marker files) describe a different, non-matching
pipeline architecture and were not adopted — see the [2.5.0] entry above for
the same pattern with a different prior document.

### Added
- **Atomic checkpoint writes.** `save_checkpoint()` now writes to a sibling
  `.tmp` file and `os.replace()`s it onto the real checkpoint path, instead
  of writing directly. `os.replace()` is atomic on both Windows and POSIX, so
  a crash mid-write can no longer leave a half-written, unparseable
  `{PREFIX}_CHECKPOINT.json` behind.
- **`PIPELINE_VERSION` compatibility flag.** Every checkpoint now records the
  `pipeline/checkpoint_utils.py`/`SKILL.md` version it was created under
  (`chapter_info.pipeline_version`). On resume, if the installed skill's
  version differs from the checkpoint's recorded version, a warning is
  printed and `pipeline_state.version_mismatch_warning` is set — non-fatal,
  resume still proceeds, but it's now visible that a chapter's earlier
  stages may have run under different stage logic than its later ones will.
- **`record_manual_edit()`** — a non-blocking audit-trail helper. Call it
  immediately after a Rule D or Rule F manual edit; it re-hashes the edited
  file and appends `{timestamp, file, file_md5_after_edit, note}` to that
  stage's checkpoint entry under `manual_edits`. Nothing in
  `should_run_stage()`/resume logic reads this list or gates on it — its only
  purpose is a readable history of hand intervention for anyone inspecting
  the checkpoint later, never a corruption signal. Wired into `SKILL.md` at
  both existing manual-edit points (Stage 2's piracy-restoration step, Stage
  4.5's splice-fix step).

## [2.5.0] - 2026-07-28

### Added
- **Stage 7 — Quality Scorecard**, optional and advisory (does not gate
  anything downstream, unlike Stage 6). Aggregates the log files every
  earlier stage already writes (Stage 4.5 verbatim pass rate, Stage 4.5c
  coverage-gap ratio, Stage 4.6 semantic-type skew count, Stage 4.7
  disease-completeness ratio, Stage 6 pass/fail) into per-dimension scores,
  plus two fresh regex-based preservation checks computed directly against
  the *final* `RAG_Optimised.md` (dosing, threshold) that no earlier stage
  checks end-to-end against the shipped output — Stage 4.5b, when it runs at
  all, only checks an earlier `chunks.md` snapshot before Stages 4.6/4.7/5.2
  add or modify content, and only on chapters auto-flagged pharma-adjacent.
  Writes both a human-readable `.md` and a machine-readable `.json` per
  chapter, so a batch of chapters can be compared/sorted by `overall_score`
  without re-reading every stage's individual log.
- Dimensions with no applicable source content (e.g. a neurology chapter
  with zero dosing hits in source) are reported `N/A` and excluded from the
  `overall_score` average, rather than scoring 0 — a chapter shouldn't be
  penalized for a category that genuinely doesn't apply to it.

### Context
Prompted by a user-submitted "full implementation guide" proposing a
from-scratch parallel pipeline with RAGAS integration, custom LLM-judged
medical metrics, and 6x-per-chapter API cost via "parallel workers." That
design would have discarded all of the coverage-gap/completeness-checklist/
disease-clustering engineering already in this pipeline (Stages 4.5c, 4.7,
5.2, 5.3) while reintroducing failure modes this pipeline's own Hard-Won
Rules already document and fix, referenced a non-existent model string
(`claude-opus-4-8`), and assumed sandbox-only paths (`/mnt/user-data/uploads/`)
that don't exist in a local Windows Claude Code session. Stage 7 is the
scoped-down version of the useful part of that idea — a comparable per-chapter
quality number — built as a zero-cost addition on top of the existing 15
stages instead of a replacement for them. True RAGAS-style LLM-judged
metrics (`faithfulness`/`context_recall` against generated Q&A pairs) remain
unimplemented by design — see the "Extending to LLM-judged metrics" note in
`SKILL.md`'s Stage 7 section for how that would be scoped as a separate,
explicitly opt-in addition if ever wanted, following the same
budget-gated/manual-fallback pattern Stage 4.6 already established.

### Changed
- `pipeline/checkpoint_utils.py` `STAGE_ORDER` extended with `"7"` at the end.
- Completion Report Format template (`SKILL.md`) gained a `Stage 7:` line.

## [2.4.0] - date not recorded

### Added
- **Checkpoint/resume system** (`pipeline/checkpoint_utils.py`), wired into every
  stage in `SKILL.md`: `load_or_create_checkpoint()`,
  `should_run_stage()`/`mark_stage_complete()` at the top/bottom of every
  stage, plus `mark_section_complete()`/`get_remaining_sections()` for
  checkpointing Stage 4B's 500-line batches on large chapters. A crashed or
  interrupted session now resumes at the exact `next_stage_to_run` instead of
  restarting the chapter from scratch.
- Source-file change detection: if `SOURCE_PATH`'s MD5 no longer matches the
  saved checkpoint, the checkpoint is discarded and the chapter restarts from
  Stage 1 automatically — downstream stage outputs are not trustworthy
  against a changed source.

## [2.3.1] - date not recorded

### Fixed
- **Stage 4.7 `infer_categories()` still over-flagged after [2.2.1]'s fix** —
  Rule O in `SKILL.md`. Hand-verifying every remaining `SCATTERED`/
  `SUSPECTED_GAP` flag on a real chapter against the actual chunk **body**
  text (not just topic/semantic_type) found every one was still a false
  positive: a flowing single-paragraph disease overview (the flat-`##`
  fallback's typical output for a section with no `###` children) routinely
  covers 3–4 required categories in one chunk with no literal box headers to
  key off of (e.g. "The cause is unknown... Treatment is with aspirin..." in
  one `clinical_feature`-tagged chunk).
- Added a third, lowest-confidence `infer_categories()` tier: a
  `BODY_PATTERNS` regex scan (`treatment is`, `cause is`, `adverse effect`,
  etc.) that only **adds** categories the higher-confidence topic/
  semantic_type tiers missed — never overrides them.

## [2.3.0] - date not recorded

### Added
- **Stage 4.5c — L1/L2 Source-Span Coverage Gate**, blocking. Compares every
  L1 macro chunk's sentences (line-scoped, not joined-then-split — an earlier
  draft of this check false-positived 48/72 "gaps" by merging multiple `###`
  children's lines into one run-on unit before splitting on sentence
  punctuation) against the full pool of L2 chunk bodies; flags any L1 section
  under 90% sentence coverage. Closes the blind spot Stage 4.5 cannot see on
  its own: Stage 4.5 only verifies that chunks which *exist* are accurate, it
  has no way to detect a source span that was never chunked at all.
- **Stage 6 Check 6.4**: hard-fails a chapter if Stage 4.5c either wasn't run
  (missing `L1L2_CoverageGaps.md`) or reported a blocking failure. Absence of
  the file is treated as a failure, not a pass-by-default, since that would
  reproduce exactly the silent-omission risk the gate exists to close.

### Context
Built in direct response to Rule Q's original framing ("rare edge case,
splice-fix by hand when found") being wrong: a full audit driven by 15
specifically-named pieces of content found **9 of 15 confirmed as total
losses** — present in `REPAIRED_S2.md` and the L1 macro chunk, absent from
every L2 chunk and therefore absent from `RAG_Optimised.md`. Finding these by
hand doesn't scale (it requires already knowing what to look for); Stage
4.5c is the general-purpose, automatic version — see `SKILL.md` Rule Q2.

## [2.2.1] - date not recorded

### Fixed
- **Stage 4.7 `infer_categories()` had no `semantic_type` fallback for 2 of
  5 required categories** (`causes`, `complication_or_safety`) — Rule M in
  `SKILL.md`. They could only be satisfied by a literal topic keyword
  ("cause"/"aetiology"/"risk factor" or "adverse"/"side effect"/
  "contraindication"), so almost any disease without a box literally titled
  "Causes of X" or "Adverse effects of X" was flagged `SCATTERED` even when a
  `pathophysiology` chunk explained cause or a `drug_info` chunk bundled
  dosing with safety-monitoring in the same box. Measured impact on a real
  chapter: 30 of 38 disease clusters were flagged `SCATTERED` before this fix.
- Added `pathophysiology` → `causes`, `diagnostic_criteria` → `causes` (in
  addition to `clinical_presentation` — both flavors of box were tagged
  `diagnostic_criteria` in manual review), and `drug_info` →
  `complication_or_safety` (in addition to `treatment`) fallback mappings.
  `infer_categories()` now returns a *set* rather than a single value, since
  one chunk legitimately satisfies more than one category.
- Result: `SCATTERED` count on the same test chapter dropped from 30/38 to
  15 clusters (see [2.3.1] above — this number still turned out to be
  entirely false positives on manual body-text verification, which is what
  motivated that follow-up fix).

## [2.2.0] - date not recorded

### Added
- **Stage 4.7 — Completeness Checklist.** Clusters L2 chunks by
  `disease_focus` (Rule N in `SKILL.md` — clustering on topic-string matching
  against a curated alias list badly undercounts; on a real chapter it found
  only 2 chunks for `rheumatoid_arthritis` via topic text vs. 18 via
  `disease_focus`, since most sub-chunks are titled generically and never
  repeat the disease name). Flags `SCATTERED` (≥2 of 5 required categories
  missing across a ≥2-chunk disease cluster) and `SUSPECTED_GAP` (exactly 1
  category missing, matched against a curated per-chapter ruleset) for
  follow-up. Requires two per-chapter curated inputs with no chapter-agnostic
  automatic derivation: `DISEASES_<CH>` (alias groupings) and
  `SUSPECTED_GAP_RULESET_<CH>` (heading-implies-content rules) — Rule K.
- **Stage 5.2 — Tier 2 Synthesized Chunks.** For confirmed `SCATTERED`
  diseases (after filtering out non-disease clusters — anatomy/exam/
  investigation-topic groupings and regional-pain clusters are not
  synthesis candidates, Rule L), writes a 150–300 word clinical summary
  in-session from that disease's own fragments only (no outside knowledge —
  a hard constraint to avoid fabrication risk in clinical content), tagged
  `synthesized: true` with a `gap_note`.
- **Stage 5.3 — Tier 3 Gap Stubs.** For `SUSPECTED_GAP` diseases confirmed
  genuinely absent by a human (never skipped — Rule L), appends an
  empty-body stub chunk (`semantic_type: coverage_gap`,
  `coverage_status: gap`) so a query for missing content surfaces "not
  covered here, see X" instead of silently nothing. Stub chunks are never
  fed to editorial generators as source material.
- **Stage 5.4 — `related_chunks` Auto-Link.** Zero-token same-`disease_focus`
  bidirectional linking pass over all L2 chunks, idempotent (safe to re-run
  after a splice-fix without duplicating the field).
- **Rule P** (`SKILL.md`): documents two confirmed `disease_focus`
  consistency bugs that silently corrupt Stage 4.7 clustering — an
  over-broad umbrella term sweeping unrelated diseases into one label, and
  one disease group split across multiple different `disease_focus` slugs.
  Both are silent (no error, just wrong clustering) and were only caught by
  manually reading the `SCATTERED` chunk list.
- **Rule Q** (`SKILL.md`, later superseded by Rule Q2 / Stage 4.5c in
  [2.3.0]): first documented instance of the "some but not all content in a
  `##` section reached L2" failure mode, found while investigating a
  `SCATTERED` false-positive.

## [2.1.0] - 2026-07-21

### Context
A full manual re-read of every chunk in a real chapter (Rheumatology and bone
disease: 196 L1 macro chunks + 174 L2 micro chunks, 370 total) was performed
after the [2.0.1] parsing-bug fix made verification actually able to run for
the first time. Findings:

- **L2 (174 chunks): 29 corrections, 16.7% error rate.**
- **L1 (196 chunks): 29 corrections, 14.8% error rate.**
- Combined: **58/370 corrections, 15.7% overall error rate** on a
  pharma-adjacent chapter — worse than this skill's previously documented
  "~65% accuracy on pharma chapters" claim would predict as a FLOOR, because
  that claim assumed the pathophysiology-only verification scope was at least
  catching the errors within its scope. It wasn't: `clinical_feature` (the
  default catch-all) was the WRONG tag in the large majority of corrections,
  not the type being corrected away from. A pathophysiology-only scope
  structurally cannot fix "should have been X but defaulted to
  clinical_feature" for any X other than pathophysiology.

### Added
- `stage_4_with_verification()` — new default Stage 4.6 entry point. Combines
  the (now full-scope) regex baseline with Sonnet verification as a single
  mandatory step, not an opt-in flag. Auto-detects whether the `anthropic`
  package/API key are available and picks the API path or flags
  `needs_manual_verification: True` for the manual path — never silently
  ships regex-only output as if it were verified.
- `export_for_manual_review()` / `apply_manual_corrections()` — formalise the
  manual verification protocol used to produce the [2.1.0] findings. When no
  Sonnet API is configured (the common case for Claude Code sessions with no
  API credentials — observed directly, not hypothetical), the calling agent
  IS Sonnet and performs the same re-read reasoning directly instead of a
  network call. This isn't a degraded fallback; it's how the findings this
  release is based on were actually produced.
- `TITLE_RULES` — title/topic-based classification signals, checked before
  body-text `BODY_RULES`. Existing body-only regex was the root mechanism
  behind the single largest error pattern found (sibling type-bleed, below):
  a chunk's own title is a far stronger signal than keyword hits in nearby
  chunks' vocabulary bleeding into a body-text match.
- Pure-epidemiology detector (`_is_pure_epidemiology`) and pure-anatomy/
  physiology `BODY_RULES` patterns — see Error Patterns below.
- Back-matter filter (`_is_backmatter` / `BACKMATTER_TOPIC_RE`) — skips
  Journal articles / Websites / Patient organisations / Further information
  sections during verification, matching the equivalent exclusion added to
  Stage 4B's subagent prompt in `SKILL.md`.

### Changed
- **`verify_with_sonnet` default flipped from `False` to mandatory.**
  `stage_4_6_semantic_remap()` (the v2.0.0 entry point) is now deprecated but
  kept for backward compatibility — it still only scopes to
  pathophysiology-tagged chunks. New callers should use
  `stage_4_with_verification()`.
- **Verification scope expanded from "pathophysiology-tagged chunks" to
  "every chunk in the requested `levels`"** (default `levels=(2,)`, matching
  what `RAG_Optimised.md` actually ships — see Rule G in `SKILL.md`).
- `SKILL.md` Stage 4B subagent prompt: added rules for per-chunk-independent
  classification (no sibling bleed), MCQ classification by dominant subject
  instead of a blanket `diagnostic_criteria` default, and back-matter
  exclusion from chunk emission.
- `SKILL.md` Hard-Won Rules: added Rule G (L1 is advisory / L2-only
  verification by default), Rule H (back-matter isn't clinical content),
  Rule I (sibling type-bleed is the #1 failure mode).
- Documented accuracy claim corrected: the [1.x] baseline's "~65% accuracy on
  pharma chapters" was itself optimistic given the pathophysiology-only
  verification scope could never have closed most of the gap found here.
  Recommend re-measuring accuracy on the next 2-3 chapters processed under
  v2.1.0 before restating a new number with confidence.

### Error Patterns Found (basis for the rule changes above)
1. **Sibling type-bleed** (largest single pattern): consecutive chunks under
   one box/section inherit a neighbor's semantic_type regardless of their own
   content. Example: 4 vasculitis-subtype disease-description chunks all
   tagged `laboratory_investigation` purely for sitting next to a genuine
   "Investigation of AAV" chunk.
2. **Drug adverse-effects misrouted**: "Adverse effects of X" boxes tagged
   `management_step` instead of `drug_info` because they sat under a parent
   "management" section rather than being judged on their own drug-safety
   content (bisphosphonates box: 4/4 chunks wrong).
3. **Pure anatomy/physiology defaulted to `clinical_feature`**: structural/
   embryological description (Bone, Joints, Synovial fluid, Skeletal muscle)
   should be `pathophysiology` — 8 of 12 L1-batch-1 corrections were this
   single pattern, all in one "Functional anatomy and physiology" section.
4. **Imaging-modality / lab-test sections defaulted to `clinical_feature`**:
   Radionuclide scintigraphy, Ultrasonography, CT, Rheumatoid factor test
   should be `laboratory_investigation`.
5. **Pure epidemiology-statistic intros defaulted to `clinical_feature`**:
   disease-overview paragraphs that are ONLY prevalence/incidence/mortality
   numbers (no presentation description) should be `epidemiology_concept`.
   Distinguished from hybrid chunks that blend demographics WITH actual
   presentation description (e.g. polyarteritis nodosa, Kawasaki disease),
   which correctly stay `clinical_feature`.
6. **MCQs over-tagged `diagnostic_criteria`** as a generic catch-all
   regardless of the question's actual subject (2/7 MCQs in the sample
   chapter were pure drug-pharmacology questions mistagged this way).
7. **Non-clinical back-matter chunked as clinical content**: Journal
   articles / Websites / Patient organisations reference lists were emitted
   as L1/L2 chunks and forced into the 7-type taxonomy despite fitting none
   of them.

### Design Correction Made Mid-Implementation (important — read before touching `BODY_RULES`)
The first implementation of this release auto-applied `BODY_RULES` broadly
across all chunks in scope, on the theory that the hardened patterns (drug
adverse-effects, epidemiology-stat detection, anatomy/physiology detection)
would improve accuracy. Measured directly against the 58 known corrections
from the Ch25 audit plus the 312 already-correct chunks:
- `BODY_RULES` applied to all chunks: 23/58 agreement, but **96 regressions**
  on previously-correct chunks.
- `BODY_RULES` scoped only to chunks currently tagged `clinical_feature`
  (the catch-all bucket errors flow into): improved to 29/58 agreement after
  also fixing a weak `Box \d+\.` pattern that was stealing matches, but still
  **76 regressions**.
- The pure-epidemiology detector alone, scoped the same way: 0 new correct
  catches in this test, but **4 regressions** on legitimately-hybrid chunks
  (disease-overview paragraphs that blend demographics with an actual
  presentation description — exactly the distinction a human reviewer has to
  make case-by-case, which a stats-count threshold cannot safely replicate).
- `TITLE_RULES` alone (exact title/topic string matches only): **0
  regressions, 0 disagreements**, 5/58 direct catches.

**Conclusion applied to the final design**: body-text regex is not reliable
enough to auto-apply, full stop — not even scoped narrowly. `_regex_remap_all`
(Stage 4a in `stage_4_with_verification`) now auto-relabels using ONLY
`TITLE_RULES`. `BODY_RULES` and the epidemiology/anatomy detectors are
advisory-only, surfaced via `_flag_review_priority()` into the
`review_priority` metadata field to help a verifier triage what to check
first — never used to silently overwrite a tag. This is *why* verification
(Sonnet API or the manual protocol) is mandatory rather than "just run
better regex": no amount of regex hardening closes the gap safely on its
own, confirmed empirically rather than assumed.

### Known Limitations
- `TITLE_RULES` hardening covers the patterns actually observed in one
  chapter; other chapters may surface different strong-title-signal patterns
  not yet encoded. `BODY_RULES`/detectors remain advisory-only by design (see
  above) — do not promote them to auto-apply without re-running the same
  regression measurement this release did.
- L1 verification (`levels=(1, 2)`) still costs roughly 2x a L2-only run and
  is not the default — see Rule G. Chapters where L1 chunks ARE used
  downstream (outside this skill's own `RAG_Optimised.md` output) should
  explicitly pass `levels=(1, 2)`.
- No automated regression test suite comparing rule-engine output against
  the 58 known-correct Ch25 corrections. The measurement above was done
  ad hoc in this session; would be worth codifying as a fixture so any
  future rule change is checked against the same regression bar before
  merging.

## [2.0.1] - 2026-07-21

### Fixed
- **Critical: Stage 4.6 was a silent no-op against this skill's actual chunks.md
  format.** `_split_chunks()` only recognized chunks preceded by a
  `### Chunk L2-NNN` header line — a format from the original draft spec that
  this skill's Stage 4 (subagent verbatim line-slicing) never produces. Real
  `chunks.md` files use bare `---\nchunk_id: ...\n---\n` frontmatter blocks
  with no header line, so `_split_chunks()` found 0 chunks, `_regex_remap()`
  and `_stage_4_6_sonnet_verification()` both iterated over an empty list, and
  every prior run — regardless of `verify_with_sonnet` — returned
  `chunks_corrected: 0` unconditionally. This was indistinguishable in the
  logs from a legitimate "nothing needed fixing" result. Discovered when a
  manual re-read of a chapter's `pathophysiology`-tagged chunks found a real
  misclassification that Stage 4.6 had never touched.
  `_split_chunks()` now tries the legacy `### Chunk` format first, then falls
  back to the bare-frontmatter format actually produced by this skill.
- **Body-extraction logic assumed two `\n---\n` delimiters per chunk**
  (opening + closing), correct only for the legacy header format. The bare
  format has exactly one, so the old `part.find('\n---\n', part.find(...) + 1)`
  double-find returned -1 and silently fell back to treating the *entire*
  frontmatter+body block as body text — meaning regex keyword rules in
  `_regex_remap()` and the Sonnet prompt body in
  `_stage_4_6_sonnet_verification()` would have matched against YAML field
  names too (e.g. `topic:`, `contains_boxes:`) had the split ever succeeded.
  Replaced with a single regex (`_get_body()` / `_CHUNK_BODY_RE`) that handles
  both formats without hand-counting delimiters.

- **Same bug was also baked into `SKILL.md` itself**, independent of
  `pipeline/stage_4_6_sonnet_verification.py`: Stage 4.5's spot-check regex
  (`r'(### Chunk L2-\S+.*?)(?=### Chunk |\Z)'`) and Stage 5's chunk-extraction
  regex (`r'(?=^### Chunk )'`) both assumed the same never-produced header
  line. Stage 4.5 would have logged `L2 checked: 0 | ... | VERDICT: CLEARED`
  on every run — a false-positive pass, not a real check — and Stage 5 would
  have written an empty `RAG_Optimised.md` body (header only, 0 chunks).
  Both inline scripts in `SKILL.md` rewritten to parse the bare
  `---\nchunk_id:...` format directly.

### Verification
- Patched module tested against a real chapter's `chunks.md` (370 total
  chunks: 196 L1 + 174 L2): `_split_chunks()` now finds all 370 blocks
  (previously 0), correctly isolates pathophysiology-tagged L2 chunks, and
  `_get_body()` returns clean frontmatter-free text.
- Corrected Stage 4.5/Stage 5 regexes verified against the same chapter's
  real `chunks.md`: Stage 4.5 now reports `L2 checked: 174` (was 0), Stage 5
  now emits all 174 L2 chunks into `RAG_Optimised.md` (was 0).

## [2.0.0] - 2026-07-21

### Added
- Optional Stage 4.6 Sonnet verification path (`verify_with_sonnet` param), re-reads
  each `pathophysiology`-tagged chunk + its local source context and reasons about
  semantic type instead of relying solely on keyword regex. Implemented in
  `pipeline/stage_4_6_sonnet_verification.py`.
- `min_budget_to_run` param — gates whether Sonnet verification is even attempted,
  separate from the output token cap.
- `max_output_tokens` param — bounds the Sonnet API call's `max_tokens`, replacing
  the overloaded single-budget param from the original draft spec that conflated
  gate and cap.
- Per-chunk source context windowing (`_get_context_window()`), built from the
  `source_lines` frontmatter Stage 4 already writes per chunk — no new tracking
  required (the original draft spec assumed a `source_offset` field that doesn't
  exist in this skill's chunk format).
- `chunks_unparsed` and `unparsed_chunk_ids` fields in the returned metadata —
  chunks where Sonnet's response couldn't be parsed are tracked explicitly instead
  of silently keeping stale `semantic_type` values with no record.
- Partial-failure signal: if `chunks_unparsed` exceeds ~10% of chunks reviewed,
  `status` is reported as `"partial_success"` rather than `"success"`.

### Changed
- **Architecture adapted to this skill's text-based model.** The original draft
  spec assumed a `chunks_data` list-of-dicts pipeline with a persistent Python
  module and existing caller — this skill has neither: every stage is a
  standalone inline script operating on `chunks.md`/`REPAIRED_S2.md` as raw
  text. `stage_4_6_semantic_remap(chunks_data, repaired_s2_text, ...)` keeps the
  requested signature, but `chunks_data` is the full text of `chunks.md` and the
  function returns `(new_chunks_text, metadata)`.
- **Semantic type taxonomy kept as `laboratory_investigation` /
  `epidemiology_concept`** (not `lab_investigation` / `epidemiology` from the
  original draft) — matches what Stage 4.5b and Stage 5 already expect, and
  the `SKEW_THRESHOLD` distribution logic in the base Stage 4.6.
- **Only remaps chunks currently tagged `pathophysiology`**, matching the base
  skill's existing Stage 4.6 guard — not an unconditional retag of every chunk.
- **Model string corrected**: `claude-sonnet-4-6` → `claude-sonnet-5`. The
  original draft spec referenced a non-existent model string that would have
  hard-failed every Sonnet verification call.
- Regex fallback (`_regex_remap()`) is the base skill's original Stage 4.6 logic,
  unchanged, moved into the new module as the default and Sonnet-failure path.

### Known Limitations
- Stage 4 (chunking) and Stage 4.5 (spot-check) are unchanged; any accuracy
  issues originating there are out of scope for this update.
- Non-pharma chapter accuracy (90%+) is unaffected by this release since regex
  remains the default path unless `verify_with_sonnet=True` is explicitly set.
- No automated re-run trigger when `chunks_unparsed` exceeds the 10%
  degraded-run threshold — currently logged/flagged in metadata only.

---

## [1.x] - prior

- Baseline `davidson-rag-pipeline-cc` skill. 7-stage pipeline (audit, repair,
  reaudit, Sonnet chunking, spot-check, regex semantic remap, regeneration).
  ~90-95% accuracy on non-pharma chapters, ~65% on pharma chapters due to
  regex-only Stage 4.6.
