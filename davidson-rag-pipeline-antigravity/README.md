# davidson-rag-pipeline-antigravity

Canonical private repository for the Davidson 25th Edition & Clinical Practice Guidelines RAG pipeline,
currently released as `v2.25.1` (Universal Document Archetype & Scalable Performance Engine Release). This repository contains the active pipeline
code, maintenance utilities, regression tests, release reports, and preserved
archival evidence used to validate the current baseline.

The pipeline is optimized for Google Antigravity local Windows sessions and Google Gemini 3.7 Flash High model (direct
filesystem access, no cowork sandbox, no bash VM, `python` not `python3`).
Given one `markdown_inlined.md` source, it produces `REPAIRED_S2`, `chunks`,
and `RAG_Optimised` outputs with checkpoint/resume support, a blocking
source-coverage gate, a deterministic hybrid code parser, and a completeness checklist that catches and stubs
genuine content gaps instead of shipping silent omissions.

It runs via a slim Progressive Disclosure hub architecture (`SKILL.md`) backed by dedicated, tested Python stage modules in `pipeline/stages/` and a unified CLI dispatcher with automated pipeline chaining (`python -m pipeline.run_stage --stage auto`).

## Repository Layout

- `pipeline/` - active runtime modules, unified CLI dispatcher (`run_stage.py`), and stage implementations
- `references/` - modular reference documentation, CDSS integration guides, on-demand adjudication protocols, hard-won rules, and historical post-mortems
- `scripts/` - maintenance utilities and chapter-repair helpers
- `docs/` - architecture notes and release reports
- `archive/` - preserved backups, evidence, and snapshots retained intentionally
- `tests/` - regression, invariant, and CLI-guardrail test suite

## Private Repository Notes

- This repository is intended for private GitHub use, not public distribution.
- Historical `.bak`, evidence, and snapshot files under `archive/` are
  intentionally versioned for auditability.
- Cache, temp, editor, and local environment artifacts are excluded via
  `.gitignore` and are not part of the production release surface.
- The repository reorganization is structural only and does not change pipeline
  architecture or runtime behavior.

## Status

Installed (v2.25.1). **Architecture status: UNIVERSAL DOCUMENT ARCHETYPE, SCALABLE PERFORMANCE ENGINE & OFFLINE ADJUDICATION HARDENED**

`docs/reports/V2_6_10_POSTCONDITION_TRANSACTION_REPAIR_REPORT.md`,
`docs/reports/V2_6_9_ATOMIC_FINALIZER_REPORT.md`,
`docs/reports/V2_6_8_CH11_RELATED_CHUNKS_RESTORATION_REPORT.md`,
`docs/reports/V2_6_7_STAGE6_AND_CH05_COMPLETENESS_FIX_REPORT.md`,
`docs/reports/V2_6_6_FAIL_CLOSED_FINALIZATION_REPORT.md`,
`docs/reports/V2_6_5_EMERGENCY_INTEGRITY_FIX_REPORT.md`,
`docs/reports/V2_6_4_CORPUS_SCALE_GATE_CLOSURE_REPORT.md`, and `SKILL.md`'s
"ARCHITECTURE STATUS" section). This is a significant evolution beyond the
original 7-stage v1.x baseline described lower in this file's history:

- **CDSS Multi-Modal Figure Asset Mapping & Clinical Algorithm Detection** (v2.15.0):
  Enriches micro-chunks with decoupled figure asset pointers (`figure_assets`, `figure_captions`, `contains_figures`),
  clinical algorithm & decision tree classification (`is_clinical_algorithm: true`, `algorithm_type: "decision_tree" | "scoring_system" | "stepwise_escalation"`),
  enforces Stage 6 Invariant 6.5, and provides `references/cdss_rag_integration_guide.md` for downstream clinical decision support ingestion.
- **Pareto-Optimal Token Efficiency & Automated Chaining** (v2.14.0):
  Introduces native `--stage auto` in `pipeline.run_stage` for end-to-end deterministic
  stage execution ($0 \to 1 \to 2 \to 3 \to 4a \to 4b \to 4.5 \to 4.5c \to 4.5d \to 4.6 \to 4.7 \to 5.4 \to 5 \to 6 \to 7 \to 8$)
  with clean pause-points for interactive candidate triage. Formalizes the 5 Golden Rules of Token
  Efficiency (~90% token reduction, 100% textbook verbatim retention, zero hallucination).

- **Postcondition Transaction Repair** (v2.6.10): a read-only audit
  (`docs/reports/V2_6_9_POSTCONDITION_ATOMICITY_AUDIT.md`) proved v2.6.9's finalizer
  transaction ended BEFORE its own postcondition checks ran, so all 8
  injected postcondition-failure scenarios left both the chapter marker and
  the corpus-wide ledger committed despite the command reporting failure.
  `pipeline/stages/mutation_guard.py`'s `atomic_write_then_dependent()` now accepts
  an optional `postcommit_verify` callback invoked only after both files
  are durably committed while pre-call snapshots are still in scope, so a
  postcondition failure rolls both files back (ledger first, marker second)
  using the same verified-rollback machinery a write-phase failure already
  used. Finalization transaction behavior only; no change to stage order,
  trust thresholds, or chapter-qualification logic. See
  `docs/reports/V2_6_10_POSTCONDITION_TRANSACTION_REPAIR_REPORT.md`.
- **Atomic Finalizer Repair** (v2.6.9): `pipeline/finalize_trusted_chapter.py`'s
  chapter-marker write and corpus-wide `CORPUS_TRUST_STATUS.md` ledger write
  used to share a single `args.in_place` flag computed from only the
  marker's pre-existence — a first-ever finalization into a corpus whose
  root ledger already existed wrote the marker, then refused the ledger
  write, requiring the operator to re-run the identical command (observed
  identically for Chapters 12, 09 and 07 during Batch 2). Both writes are
  now a single transaction (`pipeline/stages/mutation_guard.py`'s
  `atomic_write_then_dependent()`) that rolls back cleanly on failure —
  one invocation, both files, or neither. Finalization transaction behavior
  only; no change to stage order, trust thresholds, or chapter-qualification
  logic. See `docs/reports/V2_6_9_ATOMIC_FINALIZER_REPORT.md` and
  `CORPUS_PRODUCTION_BATCH2_GOVERNANCE_ADDENDUM.md`.
- **Stage 5.4 output-persistence invariant** (v2.6.8): `pipeline/verify_trusted_corpus_invariants.py`
  now independently re-derives `related_chunks` state from `chunks.md` and
  `RAG_Optimised.md` for any chapter whose checkpoint claims Stage 5.4
  COMPLETED, and flags `[STAGE-5.4-OUTPUT-PERSISTENCE-DEFECT]` if the claim
  doesn't match current file content — closing the gap that let Chapter 11's
  `related_chunks` field silently vanish (total loss, all 106 L2 chunks)
  across three prior release cycles undetected. Chapter 11's `chunks.md`/
  `RAG_Optimised.md` were restored (existing, unmodified Stage 5.4/5 logic
  re-run, no code change to the generation logic itself).
- **Fail-Closed Finalization** (v2.6.6): `pipeline/stages/corpus_trust.py::classify_trust()`
  now treats missing or malformed Stage 4.6/4.7/8 evidence as a mandatory-gate
  failure (`CORPUS_REVIEW_PENDING`), never as "not considered" — closing the
  Chapter 11 defect (a genuinely missing `stage_completions["4.7"]
  ["unresolved_completeness_clusters"]` checkpoint field silently passed) and
  the Chapter 03 defect (a prefixed protection-marker filename went
  undetected). Adds `pipeline/finalize_trusted_chapter.py` (the single canonical,
  dry-run-by-default finalization command) and
  `pipeline/verify_trusted_corpus_invariants.py` (a read-only post-finalization
  invariant checker). See `docs/reports/V2_6_6_FAIL_CLOSED_FINALIZATION_REPORT.md`.
- **Corpus-Scale Gate Closure** (v2.6.4): closes the three `MUST FIX` items
  found after Chapter 05/Chapter 02 generalization testing. (1) Stage 2's
  `is_clinical()` piracy-removal guard — previously inline in `SKILL.md`,
  copy-pasted per session — is now `pipeline/stages/stage_2_repair.py`, a shared,
  tested module, fixing the confirmed Chapter 05 MCQ-stem/option
  content-loss bug (decimal-numbered stems, dash-prefixed options, and
  multi-line stem continuation paragraphs are now protected). (2)
  `pipeline/stages/source_lines_precision.py` now runs automatically as Stage 8 for
  every canonical chapter (advisory + human-adjudicated, never an automatic
  hard gate), with a conservative short-bullet-list heuristic
  (`bullet_gap_only`) and a lightweight `CHECKER_FALSE_POSITIVE` /
  `HUMAN_CONFIRMED_METADATA_DEFECT` adjudication mechanism
  (`apply_source_lines_adjudication()`). (3) `CORPUS_TRUST_STATUS.md` is now
  generated by `pipeline/stages/trust_ledger.py` /
  `pipeline/generate_corpus_trust_ledger.py` (dry-run by default, guarded write) from
  live repository evidence — a new `CORPUS_REVIEW_PENDING` classification
  means an untested or unresolved source-lines mapping can no longer receive
  `CORPUS_TESTING_READY`, and `tests/test_trust_ledger_staleness.py` makes
  ledger staleness a CI-visible test failure. `STAGE_ORDER` gained a new
  terminal stage `"8"`; existing terminal checkpoints (Chapter 05, Chapter
  02) were migrated forward via `scripts/maintenance/checkpoint_migrate_v2_6_4.py` (CP-08).
- **Safety guardrails** (v2.6.3): explicit read-only vs. pipeline-execution
  checkpoint access (`read_checkpoint()` never writes or migrates;
  `load_checkpoint_for_run()` migrates in-memory for stage execution;
  `migrate_checkpoint_schema()` is the only function that persists a schema
  migration to disk, dry-run by default) — see `pipeline/checkpoint_utils.py`'s
  module docstring and `CHANGELOG.md` [2.6.3]. Direct runner scripts
  (`scripts/maintenance/run_stage_4_5d.py` and every Chapter-05-specific repair script) are now
  non-mutating by default: overwriting an existing chapter output requires
  `--write --in-place`, and a chapter carrying a `CORPUS_OUTPUT_PROTECTED.json`
  marker additionally requires `--backup` — refused otherwise with a clear
  error naming the missing flag(s) (`pipeline/stages/mutation_guard.py`). Chapter 05's
  Stage 4.5d adjudication now replays an immutable, hash-locked, per-candidate
  manifest with a mandatory rationale for every decision
  (`pipeline/stages/adjudication_manifest.py`,
  `tests/fixtures/ch05_regression/clinical_fidelity_adjudication_manifest.json`)
  instead of a hardcoded blanket decision — replay against a different
  source/chunks/candidate-set is refused, not silently applied.
- **Checkpoint provenance** (v2.6.2): `chapter_info`'s single, ambiguous
  `pipeline_version` field is replaced with three explicit fields —
  `checkpoint_created_with_pipeline_version` (set once, at creation, NEVER
  overwritten — a chapter's historical creation version is preserved
  permanently, even after migration or years of later processing),
  `last_processed_with_pipeline_version` (advances only when a stage
  genuinely executes), and `checkpoint_schema_version` (`"2.0"`). A legacy
  checkpoint with no version info at all gets `"UNKNOWN"`, never an
  invented value. `check_version_compatibility()` produces a non-fatal
  warning distinguishing creation/last-processed/installed versions — a
  version difference is never itself treated as corruption. See
  `pipeline/checkpoint_utils.py`'s module docstring and `CHANGELOG.md` [2.6.2].
- **Deterministic corpus-trust classification** (v2.6.2):
  `pipeline/stages/corpus_trust.py`'s `classify_trust()` replaces independent,
  hand-edited trust classification per chapter/document — the prior
  hand-edited approach produced a real, confirmed misclassification (see
  `CORPUS_TRUST_STATUS.md`). Never infers trust from `RAG_Optimised.md`'s
  mere existence.
- **Checkpoint statuses** (v2.6.0): `stage_completions[key].status` is now
  one of `COMPLETED` / `BLOCKED` / `FAILED` / `IN_PROGRESS`, not just
  `COMPLETED`. A stage with a real pass/fail verdict (1, 3, 4.5, 4.5c, 4.5d,
  4.6, 6) is only ever checkpointed `COMPLETED` on an actual pass —
  `mark_stage_blocked()`/`mark_stage_failed()`/`mark_stage_in_progress()`
  cover every other outcome. `pipeline_state.pipeline_status` also
  distinguishes `CORPUS_PIPELINE_COMPLETED` from
  `ADVISORY_SCORECARD_COMPLETED`, backed by independent monotonic boolean
  flags. See `CHANGELOG.md` [2.6.0] and `docs/architecture/IMPLEMENTATION_MAP.md` for the
  full CP-01–07 rationale, and `scripts/maintenance/checkpoint_migrate_v2_6_0.py` if resuming a
  chapter checkpointed before this release.

- **Stages 1–4B**: forensic audit, autonomous repair, reaudit, header map +
  heading-depth manifest, subagent chunking (with checkpointed 500-line
  batching for large chapters).
- **Stage 4.5**: exhaustive verbatim spot-check (every L2 chunk, no sampling).
- **Stage 4.5c**: L1/L2 source-span coverage gate — **blocking**. Catches
  whole sections/diseases silently dropped during chunking, a failure mode
  Stage 4.5 alone cannot see (it only verifies chunks that exist, not spans
  that were never chunked at all).
- **Stage 4.5d** (v2.6.0): clinical fidelity gate — **blocking**. Catches
  content that *did* reach an L2 chunk but changed in transit: numeric/unit/
  inequality/range/dose/duration/frequency drift, negation/polarity flips,
  sequence reorders, and drug/dose boundary loss across a chunk split.
  Automated detection (11 sub-checks) + mandatory human adjudication of
  every candidate — never auto-cleared or auto-failed on regex alone. See
  `pipeline/stages/stage_4_5d_clinical_fidelity.py` and SKILL.md's Stage 4.5d
  section for the full protocol.
- **Stage 4.5b**: clinical flag coverage (dosing/threshold density), pharma
  chapters only, auto-detected from the chapter title.
- **Stage 4.6**: semantic-type verification, now mandatory rather than
  optional, full-scope (all chunks, not just `pathophysiology`-tagged ones).
- **Stage 4.7**: completeness checklist — flags `SCATTERED` (multi-category
  gaps in a disease cluster) and `SUSPECTED_GAP` (heading implies content
  that's missing) diseases for follow-up.
- **Stage 5.2/5.3/5.4**: Tier 2 synthesized chunks (for confirmed `SCATTERED`
  diseases), Tier 3 gap stubs (for human-confirmed `SUSPECTED_GAP` diseases,
  never fed to editorial generators — their purpose is making a gap
  answerable via `gap_note` instead of silently absent), and `related_chunks`
  auto-linking by shared `disease_focus`.
- **Stage 5**: generates `RAG_Optimised.md` (L2 chunks only, with
  `coverage_status`/`gap_note` fields added).
- **Stage 6**: hard-fail validation gate — a chapter with unresolved coverage
  gaps or missing metadata does not ship.
- **Stage 7** (optional, advisory, zero extra cost): quality scorecard.
  Aggregates the log files every earlier stage already wrote (Stage 4.5
  verbatim pass rate, Stage 4.5c coverage-gap ratio, Stage 4.6 semantic-type
  skew, Stage 4.7 disease-completeness ratio, Stage 6 pass/fail) plus two
  fresh regex checks — dosing/threshold preservation from source all the way
  through to the *final* `RAG_Optimised.md` — into one `overall_score` per
  chapter, written to both `{PREFIX}_QualityScorecard.md` (human-readable)
  and `{PREFIX}_QualityScorecard.json` (for batch comparison across
  chapters). Purely regex-based, no LLM calls, no API cost — this is *not* a
  RAGAS/LLM-judge implementation; see the "Extending to LLM-judged metrics"
  note in `SKILL.md`'s Stage 7 section if that's ever wanted as a separate,
  explicitly opt-in addition.
- **Checkpoint/resume system** (`pipeline/checkpoint_utils.py`): every stage — and every
  500-line section within Stage 4B — is checkpointed to
  `{PREFIX}_CHECKPOINT.json`, so a crashed or interrupted session resumes at
  the exact next stage instead of restarting the chapter. If the source file
  changes, the checkpoint is discarded and the chapter restarts from Stage 1
  automatically (stage outputs downstream of a changed source aren't
  trustworthy otherwise). Checkpoint writes are atomic (temp file + rename),
  every checkpoint records the pipeline version it was created under (warns,
  non-fatally, on resume if that's changed), and manual splice-fixes (Rule
  D/F) are recorded to a non-blocking audit trail rather than treated as
  drift/corruption.

See `CHANGELOG.md` for the version history from the original v1.x baseline
through v2.4.0, including the accuracy findings that drove the Stage 4.6
redesign and the "Hard-Won Rules" section in `SKILL.md` for full incident
narratives behind each fix.

## Why the v2.1.0+ Stage 4.6 Design Exists

The base pipeline's Stage 4.6 originally assigned `semantic_type` to each
chunk via first-match-wins regex. On pharma chapters this misfires
constantly: a chunk about drug mechanism gets tagged `drug_info` just because
the word "drug" appears, even when the chunk is really `pathophysiology`.
Regex has no way to disambiguate — it needs to reason about what the chunk is
*primarily* about, not just which keywords it contains.

A full manual re-read of every chunk in a real chapter (370 chunks) found a
15–17% misclassification rate spread across **every** semantic type, not just
pharma-adjacent ones — `clinical_feature` (the default catch-all) was the
wrong tag in most corrections, not the type being corrected away from. As a
result, verification (via the Anthropic API if configured, or via the calling
Claude Code agent performing the same re-read reasoning manually if not) is
now **mandatory**, not opt-in, and scoped to every chunk at the requested
`chunk_level` (default L2, since that's all `RAG_Optimised.md` ships).

Testing also found that auto-applying body-text regex rules broadly — even
narrowly scoped — introduced far more regressions than it fixed (96
regressions for 23/58 correct catches in one test). Only title/topic-based
rules (`TITLE_RULES`) are auto-applied; body-text rules are advisory-only,
surfaced to help a verifier triage, never used to silently overwrite a tag.
See `CHANGELOG.md` [2.1.0] for the full findings and error-pattern breakdown.

## Files

| File | Purpose |
|---|---|
| `SKILL.md` | Skill definition — all 15 stages, params, Hard-Won Rules, Stage 4.6 verification design notes |
| `CHANGELOG.md` | Full version history, v1.x through v2.4.0, with the accuracy findings behind each change |
| `pipeline/checkpoint_utils.py` | Checkpoint/resume module — `should_run_stage()`/`mark_stage_complete()` used at the top/bottom of every stage in `SKILL.md`, plus per-section checkpointing inside Stage 4B |
| `pipeline/stage_4_6_sonnet_verification.py` | Stage 4.6 module: API verification path, regex baseline (title-rules-only auto-apply), manual verification protocol, metadata — called from the Stage 4.6 code block in `SKILL.md` |

## Usage

Follow `SKILL.md` Step 0 through Stage 6 in order (Claude Code executes each
stage's code block directly — there is no separate script to invoke). Stage
4.6's code block calls `stage_4_with_verification()` from
`pipeline/stage_4_6_sonnet_verification.py`:

```python
final, meta = stage_4_with_verification(
    chunks_data, repaired_s2_text,
    levels=(2,),              # RAG_Optimised.md only ships L2 — default scope
    min_budget_to_run=4000,
    max_output_tokens=12000,
)
```

If `meta['needs_manual_verification']` is `True` (the common case — no
`anthropic` package/API key configured in a typical Claude Code session),
run the manual verification protocol described in `SKILL.md` under Stage 4.6
instead of treating the regex-only baseline as final: export review batches
with `export_for_manual_review()`, read them, and apply corrections with
`apply_manual_corrections()`. This is not a degraded fallback — it's how the
accuracy findings that justified this stage's design were originally produced.

`stage_4_6_semantic_remap()` (the old v2.0.0 entry point,
`pathophysiology`-only scope, `verify_with_sonnet` flag) still exists for
backward compatibility but is **deprecated** — new work should use
`stage_4_with_verification()`.

## Batch / Parallel Chapter Processing

Each chapter's checkpoint is fully independent (`{PREFIX}_CHECKPOINT.json`,
keyed by that chapter's own prefix inside its own `OUTPUT_DIR`), so
processing multiple chapters is straightforward:

- **Sequential**: run Step 0 through Stage 6 for one chapter, then repeat for
  the next with a new `SOURCE_PATH`/`OUTPUT_DIR`. If a session ends mid-chapter,
  re-running Step 0.5 against the same `OUTPUT_DIR` resumes at
  `next_stage_to_run` automatically — no manual bookkeeping required.
- **Concurrent**: since there's no shared state between chapters, you can run
  several chapters at once by opening multiple Claude Code sessions, each
  pointed at a different chapter's `SOURCE_PATH`/`OUTPUT_DIR`. This is the
  real equivalent of "parallel workers" for this skill — parallelism is at
  the chapter level, not inside a single chapter's Stage 4B chunking (which is
  itself sequential/checkpointed by 500-line section, not parallel-worker
  based).

**Recommended layout** — keep chapter inputs/outputs in your own project
directory, not inside this skill's own folder:

```
<your-project-dir>/
  chapters/                          # markdown_inlined.md source files
    Davidson_25_16_Cardiology.pdf.md
    Davidson_25_17_Respiratory.pdf.md
    ...
  outputs/
    Davidson_25_Ch16_Cardiology/      # one OUTPUT_DIR per chapter
      Davidson_25_Ch16_Cardiology_CHECKPOINT.json
      Davidson_25_Ch16_Cardiology_AUDIT_REPORT.md
      ...
      Davidson_25_Ch16_Cardiology_RAG_Optimised.md
    Davidson_25_Ch17_Respiratory/
      ...
```

This skill's own directory (where `SKILL.md`/`pipeline/checkpoint_utils.py`/
`pipeline/stage_4_6_sonnet_verification.py` live) should only ever be read from (for
`SKILL_DIR` imports) — never written to as a scratch/output location.

## Known Gaps Not Yet Fixed

- ~~No automated re-run trigger when `chunks_unparsed` exceeds 10%~~ — fixed
  in v2.6.0, CP-05: Stage 4.6 now blocks explicitly (see CHANGELOG).
- Stage 4.5c (L1/L2 coverage gate) checks *sentence-level* coverage, not
  paraphrase-level — a section rewritten rather than dropped could still show
  as covered even if content drifted. Stage 4.5d (v2.6.0) narrows this for
  specific pattern classes (numeric/unit/negation/polarity/sequence/etc.)
  but does not close it generally — regex cannot prove semantic equivalence
  for prose outside those pattern classes, and Stage 4.5d's own
  `truth_status.semantic_completeness_claimed: false` is the explicit
  acknowledgment of that limit, not a fix for it.
- `TITLE_RULES` in `pipeline/stage_4_6_sonnet_verification.py` covers the strong-title
  patterns observed in the chapters used to build the rule set; other
  chapters may surface title patterns not yet encoded there. `BODY_RULES`
  remain advisory-only by design — do not promote them to auto-apply without
  re-running the same regression measurement documented in `CHANGELOG.md`
  [2.1.0].
- No automated regression test suite comparing the semantic-type rule
  engine's output against known-correct manual corrections from past
  chapters — v2.6.0 added `tests/` (pytest) covering the CP-01–07 governance
  fixes and Stage 4.5d's detectors/adjudication protocol, but a
  fixture-based regression suite for Stage 4.6's classification rules
  specifically is still Phase 4 (Stage 6.5) future work, not built.
- Stage 4.5d's 11 sub-checks are regex/pattern-based by design — every
  candidate they raise requires mandatory human adjudication before the
  gate can pass (see SKILL.md's Stage 4.5d section). This is deliberate,
  not a bug, but it means Stage 4.5d materially increases per-chapter human
  review time versus a chapter that only goes through Stage 4.6's manual
  path — not yet measured at scale across more than one chapter (see
  `docs/reports/PHASE0_PHASE1_REPORT.md`'s Chapter 05 regression numbers for the first
  real data point).
- Adding a stage to `STAGE_ORDER` does not retroactively invalidate a
  chapter's already-`COMPLETED` *later* stages whose own acceptance
  criteria changed as a result (e.g. Stage 6 gained Check 6.4b in v2.6.0,
  but a chapter whose Stage 6 was already `COMPLETED` under the pre-4.5d
  rules keeps that status until Stage 6 is explicitly re-run — CP-07's
  migration only rewinds `next_stage_to_run`, it does not clear downstream
  `COMPLETED` entries). Found while regression-testing Chapter 05 in
  v2.6.0; not fixed in this release — see `docs/reports/PHASE0_PHASE1_REPORT.md`.
- **`source_lines` frontmatter is frequently imprecise** (v2.6.1 finding):
  a whole-chapter scan of Chapter 05 with the new
  `pipeline/stages/source_lines_precision.py` checker found 29/228 chunks with a
  declared range that either excludes real content (a table) or includes
  unrelated interleaved content (a different box) — the root cause behind
  most of Stage 4.5d's false-positive candidates on that chapter. SKILL.md's
  Stage 4B subagent prompt gained an explicit rule about this for future
  chapters (v2.6.1, rule 8), but the checker itself is advisory-only and
  not wired into the checkpoint system, and Chapter 05's own `chunks.md`
  was not corrected — see `CHANGELOG.md` [2.6.1] for what was and wasn't
  done.
- **Chapter 05's integration regression test is NOT a fully-automated
  source-to-final run** (v2.6.2, `tests/test_ch05_integration_regression.py`):
  Level A validates the deterministic post-chunk pipeline (Stage 4.5c
  through Stage 6) against frozen, approved fixture artifacts in a
  temporary directory; Level B validates checkpoint-orchestration control
  flow across the full `STAGE_ORDER` sequence using synthetic stage
  results. Neither reproduces Stage 4B's real subagent (LLM) chunking call
  — that stage remains irreducibly non-deterministic and is not exercised
  inside pytest at all. Do not read this test suite as proof the whole
  pipeline, source-to-`RAG_Optimised.md`, has been automated end-to-end.
- **`INTENTIONAL_SECTION_SPLIT` is now reachable but pattern-based, not
  semantically verified** (v2.6.2): `detect_boundary_loss()` checks
  whether a real Markdown heading line sits in the source gap between two
  chunks — genuine structural evidence, not mere adjacency — but this is
  still a regex/line-scan heuristic, not proof the split was editorially
  *intentional* in a deeper sense. A heading that happens to sit between
  two chunks for an unrelated reason would still classify this way.
- **`source_lines` precision remains advisory-only, unchanged in v2.6.2**:
  the 23 `OVER_INCLUSIVE` findings remaining on Chapter 05 after v2.6.1's
  corrections were not further addressed in this stabilization release —
  the checker is still a standalone script, not a `STAGE_ORDER` stage. v2.6.3
  surfaces this same imprecision on Stage 4.5d's own gate output (see
  `source_mapping`, below) but still does not make it blocking — that
  remains a deliberately deferred future decision.
- **v2.6.3 safety-guardrail scope, stated plainly**: `scripts/maintenance/run_stage_4_5d.py`
  got the full non-mutating-by-default treatment (report-only redirect,
  authorization check, timestamped pre-mutation backup) as the flagship,
  most-used direct runner. The five Chapter-05-specific one-off scripts
  (`apply_ch05_adjudication.py`, `regenerate_rag_optimised_ch05.py`,
  `apply_source_lines_corrections_ch05.py`, `rerun_stage6_ch05.py`,
  `run_source_lines_precision.py`) and `migrate_ch05_schema_v2.py` received
  the same authorization gate and backup-before-write discipline via
  `pipeline/stages/mutation_guard.py`, but not the full atomic-temp-file +
  post-write hash-verification protocol `guarded_write_file()` implements
  for a single target file — several of these scripts write more than one
  file per invocation, backed up individually rather than as one atomic
  multi-file transaction. `scripts/maintenance/checkpoint_migrate_v2_6_0.py` already had an
  equivalent dry-run/`--apply`/backup/verify contract from CP-07 and was
  left as-is. See `docs/reports/V2_6_3_SAFETY_GUARDRAILS_REPORT.md` for the full
  classification table.
- **Chapter 05's adjudication manifest reflects a root-cause forensic
  review, not an independent credentialed clinical adjudication** (v2.6.3):
  `tests/fixtures/ch05_regression/clinical_fidelity_adjudication_manifest.json`'s
  `reviewer_role` is `pipeline_maintainer_root_cause_review`, not a
  physician sign-off — every decision's rationale documents source-line and
  formatting evidence examined, not a claim of independent medical review.
  The manifest provides traceability and locks the exact reviewed evidence;
  it does not itself prove the underlying candidates were clinically
  immaterial, only that the stated non-clinical root cause (source_lines
  metadata imprecision, one Unicode-normalization difference) is
  consistent with the evidence cited.
