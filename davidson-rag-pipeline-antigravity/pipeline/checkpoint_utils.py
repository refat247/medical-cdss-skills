"""Checkpoint/resume for davidson-rag-pipeline-cc.

Each stage of the pipeline already runs as its own Bash/python invocation and
reads its inputs back off disk (REPAIRED_S2.md, chunks.md, ...) rather than
holding state in memory across stages — so resuming a chapter is mostly
"which stage do I skip to," not "how do I reload state." This module answers
that question and persists it to {PREFIX}_CHECKPOINT.json after every stage,
plus after every 500-line section inside Stage 4B (the one stage expensive
enough, and long-running enough on big chapters, that losing partial
progress on a crash is a real cost — see SKILL.md Stage 4B rule 7).

Every write is immediate (no buffering) so a crash right after the last line
of a stage still leaves a correct checkpoint on disk. Writes are also atomic
(temp file + os.replace) so a crash *during* the write itself can't leave a
half-written, unparseable JSON file behind (see v2.5.1 CHANGELOG entry).

PIPELINE_VERSION is the currently-installed pipeline's version. It is
distinct from a checkpoint's own provenance fields (v2.6.2 — see
"Checkpoint provenance" below): the ambiguous single `pipeline_version`
field used through v2.6.1 was overloaded to mean both "version this
checkpoint was created under" and "version currently governing it,"
which a v2.6.1 audit flagged as a real risk (a migration that overwrote it
with the installed version would falsely imply every already-completed
stage was re-verified under new logic — it wasn't). Keep this constant in
sync with SKILL.md's frontmatter `version:` field when bumping either one
(the two disagreed after v2.6.0/2.6.1 — see CHANGELOG [2.6.2]).

## Checkpoint provenance (v2.6.2)

Every checkpoint's `chapter_info` now carries three explicit fields instead
of one ambiguous one:

- `checkpoint_created_with_pipeline_version` — the version installed when
  this checkpoint FIRST came into existence. Never overwritten, by any
  function in this module, for the lifetime of the checkpoint. `"UNKNOWN"`
  for a checkpoint migrated from a schema old enough to have never recorded
  a version at all (pre-v2.4.0) — never invented/guessed.
- `last_processed_with_pipeline_version` — the version that most recently
  actually ran a stage against this checkpoint. Updated by
  `mark_stage_complete`/`mark_stage_blocked`/`mark_stage_failed`/
  `mark_stage_in_progress` every time — i.e. only when a stage genuinely
  executes, never just from loading/resuming a checkpoint unchanged.
- `checkpoint_schema_version` — `"2.0"` as of this release, tracks the
  SHAPE of the checkpoint dict itself (distinct from either pipeline
  version above). A checkpoint predating this field is migrated to it via
  `migrate_checkpoint_schema_to_v2()`, applied automatically and losslessly
  on every load (renames/restructures metadata only, never touches
  `stage_completions` or triggers a stage re-run or rewind — that remains
  CP-07's separate, explicit `checkpoint_migrate_v2_6_0.py --apply` job).

`check_version_compatibility()` produces a human-readable, non-fatal
warning when `last_processed_with_pipeline_version` differs from the
currently-installed `PIPELINE_VERSION` — a version difference alone is
never treated as corruption or grounds to block; it is purely informational
context for a human deciding whether completed stages are worth reviewing.
"""
import json
import hashlib
import os
from datetime import datetime, timezone

STAGE_ORDER = [
    "1", "2", "3", "4a", "4b", "4.5", "4.5c", "4.5d", "4.5b", "4.6", "4.7",
    "5.2", "5.3", "5.4", "5", "6", "7", "8",
]

# v2.6.0: inserted "4.5d" (Stage 4.5d — clinical fidelity gate) between "4.5c"
# and "4.5b". Any checkpoint written under an older PIPELINE_VERSION that
# reached "4.5c" or later before this change needs its next_stage_to_run
# migrated — see checkpoint_migrate_v2_6_0.py. Do not reorder or remove
# existing keys when adding future stages; only ever insert.
#
# v2.6.4: appended "8" (Stage 8 — Corpus Gate Closure: automatic source_lines
# precision assessment + deterministic trust classification, see SKILL.md's
# Stage 8 section and pipeline/stages/trust_ledger.py). A chapter whose checkpoint
# already sat at a terminal next_stage_to_run == None before this release
# (Chapter 05, Chapter 02) needs that null rewound to "8" so it actually
# resumes into the new stage — see checkpoint_migrate_v2_6_4.py /
# pipeline/stages/checkpoint_migration_v2_6_4.py, same rewind pattern CP-07 already
# established for the "4.5d" insertion above. A chapter that starts fresh
# under v2.6.4+ needs no migration at all: mark_stage_complete("7", ...)
# already computes next_stage_to_run="8" directly from the updated
# STAGE_ORDER, with no special-casing required.
#
# v2.6.7: narrow emergency correctness release, CODE FREEZE (no new stages,
# no STAGE_ORDER change). Fixed a real block-parsing blind spot in
# pipeline/stages/stage_6_validation.py::check_6_1_6_2() (silently dropped a
# RAG_Optimised.md file's final chunk when it was empty-body and the file
# lacked a trailing newline -- see REPOSITORY_PRODUCTION_READINESS_AUDIT.md
# Blocker 2) and completed Chapter 05's Stage 4.7 evidence (Blocker 1). See
# CHANGELOG.md [2.6.7] and V2_6_7_STAGE6_AND_CH05_COMPLETENESS_FIX_REPORT.md.
#
# v2.6.9: Atomic Finalizer Repair, narrow emergency governance/correctness
# release, CODE FREEZE (no new stages, no STAGE_ORDER change, no change to
# trust thresholds or chapter-qualification logic). Fixed a real defect in
# finalize_trusted_chapter.py: the chapter marker write and the corpus-wide
# CORPUS_TRUST_STATUS.md ledger write shared a single `args.in_place` flag
# computed from only the MARKER's pre-existence, so a first-ever
# finalization into a corpus whose root ledger already existed wrote the
# marker, then refused the ledger write, requiring the operator to re-run
# the identical command -- observed identically for Chapters 12, 09 and 07
# during Batch 2. Both writes are now a single transaction
# (pipeline/stages/mutation_guard.py's atomic_write_then_dependent()) with rollback
# on failure. See CHANGELOG.md [2.6.9] and
# V2_6_9_ATOMIC_FINALIZER_REPORT.md. This changes finalization TRANSACTION
# behavior only -- no chapter output, checkpoint shape, or trust
# classification rule changed.
#
# v2.6.10: Postcondition Transaction Repair, narrow emergency
# transaction-integrity release, CODE FREEZE (no new stages, no
# STAGE_ORDER change, no change to trust thresholds or chapter-qualification
# logic). V2_6_9_POSTCONDITION_ATOMICITY_AUDIT.md (read-only) proved that
# v2.6.9's finalizer transaction ended (atomic_write_then_dependent()
# returned) BEFORE finalize_trusted_chapter.py's own postcondition checks
# ran -- so all 8 injected postcondition-failure scenarios left both the
# chapter marker and the corpus-wide CORPUS_TRUST_STATUS.md ledger committed
# on disk while the command reported failure. pipeline/stages/mutation_guard.py's
# atomic_write_then_dependent() now accepts an optional `postcommit_verify`
# callback, invoked only after both files are durably committed while the
# transaction's pre-call snapshots are still in scope, so a verification
# failure reuses the exact same verified-rollback machinery a write-phase
# failure already used (ledger rolled back first, marker second -- reverse
# commit order). finalize_trusted_chapter.py's postcondition checks moved
# into this callback. See CHANGELOG.md [2.6.10] and
# V2_6_10_POSTCONDITION_TRANSACTION_REPAIR_REPORT.md. This extends
# finalizer rollback through postcommit verification only -- no stage
# behavior or trust criteria changed.
# v2.7.0: Antigravity & Gemini 3.7 Flash High Optimization Release.
# Adds native Google Gemini API verification (pipeline/stage_4_6_gemini_verification.py),
# in-session Antigravity Agent manual verification protocol, and Antigravity tooling.
#
# v2.8.0: Deterministic Hybrid Engine & Audit-Hardened Metadata Synchronization.
# Adds standardized deterministic code-slicing parser for Stage 4B, Stage 5.2 mandatory
# disposition persistence in CompletenessChecklist.md, Stage 8 dual-format precision sync
# (adjudicating L1 macro containers + L2 micro chunks and re-rendering markdown reports),
# and dynamic source_path hash extraction in finalize_trusted_chapter.py.
#
# v2.9.0: Post-Chapter 16 Turnkey Hardening & Deterministic Execution Release.
# Standardizes Stage 1 regex f-string extraction for universal Python runtime support,
# Stage 4B canonical in-session Deterministic Hybrid Slicer Engine (Rule J/J2/Q, Rule P parent
# inheritance, MCQ parsing), Stage 4.6 explicit chunks_reviewed/total_flagged checkpoint persistence,
# Stage 5.2 mandatory CompletenessChecklist.md disposition table persistence across all candidate counts,
# and Stage 8 atomic Dual-Format Precision Synchronizer (JSON + Markdown).
#
# v2.10.0: Modular Reference Architecture & Token-Optimized Execution Release.
# Modularizes Hard-Won Rules and Post-Mortem history into dedicated references/ documents,
# establishes quiet command execution standard (pytest -q), and optimizes in-session context footprint.
#
# v2.11.0: Post-Chapter 17 Deterministic Hardening & Friction Reduction Release.
# Implements Stage 4B backmatter-aware intra-section trimming for L1 spans, deduplicates
# Stage 4.6 manual verification parameter unpacking, and enforces in_place=True in Stage 8
# precision checks to eliminate mutation guard friction on re-entrant runs.
#
# v2.12.0: Enterprise Guideline Qualification & Scalable Diff Engine Release.
# Upgrades Stage 3 Reaudit to O(N) line-tokenized matching, eliminating quadratic difflib
# string deadlock on 20,000+ line documents. Enforces universal cross-platform Windows UTF-8
# console stream safety, and benchmark-qualifies the 377-page ADA 2026 Standards of Care corpus.
#
# v2.13.0: Modular Architecture & Progressive Disclosure Orchestrator Release.
# Modularizes monolithic markdown into a slim Hub-and-Spoke orchestrator, extracts
# Python stage logic into dedicated tested modules under pipeline/stages/, introduces
# the unified CLI dispatcher pipeline.run_stage, and isolates manual adjudication
# protocols in references/, reducing initial token overhead by ~90% and eliminating tool truncation.
#
# v2.14.0: Pareto-Optimal Token Efficiency & Automated Pipeline Chaining Release.
# Adds native automated pipeline chaining mode (--stage auto / --stage chain) in pipeline.run_stage,
# establishes the Pareto-optimal token efficiency protocol (JIT reference loading, 25-item batch triage,
# 0-token local CLI execution, verbatim splice-repair), and provides complete end-to-end stage orchestration.
#
# v2.15.0: CDSS Multi-Modal Figure Asset Mapping & Clinical Algorithm Detection Release.
# Adds native decoupled figure asset extraction (figure_assets, figure_captions, contains_figures),
# clinical algorithm & decision tree typing (is_clinical_algorithm, algorithm_type), and Stage 6 Invariant 6.5.
#
# v2.16.0: Provenance Trust, Breadcrumb Hierarchy & Clinical Completeness Release.
# Adds non-destructive page number preservation (page_numbers, pdf_page), taxonomy breadcrumbs
# (breadcrumb), dynamic multi-extension figure resolution (.jpeg/.jpg/.png/.webp), authentic deterministic
# Stage 4.7 multi-category completeness evaluation, MCQ answer-explanation pairing, and Stage 6 Check 6.6.
#
# v2.17.0: CDSS Clinical Safety, Urgency & Nomenclature Hardening Release.
# Adds short clinical sentence piracy sweep immunity, expanded ICU/renal/oncology/ABG fidelity unit detection,
# Rule J4 bold-topic micro-splitting for flat sections, stem/substring disease linking, clinical urgency
# and box typing (clinical_urgency, box_type), and international drug synonym indexing (synonyms).
#
# v2.18.0: Multi-Item MCQ True/False Pairing & Universal Line Ending Normalization Release.
# Adds multi-item True/False MCQ answer pairing and cross-platform CRLF/LF line-ending sanitization.
#
# v2.19.0: Stage 4.6 Verification Completeness and Integrity Hardening Release.
# Makes Stage 4.6 total_flagged check explicit and hardens verification metadata handling.
#
# v2.20.0: Universal Output Subfolder Architecture & Asset Synchronization Release.
# Codifies universal chapter output routing to <SOURCE_DIR>/rag_pipeline_output, makes --out
# optional in the CLI runner, and automatically synchronizes figure assets to self-contained outputs.
#
# v2.21.0: Operational Proof & Wording Disciplines, Read-Back Mutation Invariant & Stop-Point Control Release.
# Codifies Rule T (Read-Back Invariant on File Mutations), Rule U (Golden Proof & Wording Disciplines),
# Rule V (Interactive Stop Point & No-Silent-Advance Architecture), and Stage 4.7 Anti-Heuristic Grounding.
#
# v2.22.0: Output Provenance & Version Stamping Standard Release.
# Codifies mandatory embedded provenance metadata headers across all output markdown files and JSON artifacts,
# v2.23.0: Decoupled Multi-Modal Asset Protection & Provenance-Synchronized Slicer Release.
# Fixes Stage 2 decoupled figure stripping, synchronizes Stage 4B source_lines offsets with provenance headers,
# sets default figure fallback extension to .jpeg, formats Stage 4.6 Remap_Log cleanly, and attaches provenance to all JSON outputs.
#
# v2.24.0: Universal Document Archetype & Scalable Performance Engine Release.
# Adds universal document archetype detection (TEXTBOOK vs GUIDELINE) in derive_chapter_info(),
# publication year protection from chapter number regex, O(1) set-filtered paragraph duplicate comparison in Stage 1,
# deterministic offline clinical rule adjudication in Stage 4.6, and localized anchor window search in Stage 8 precision.
PIPELINE_VERSION = "2.26.0"
SKILL_NAME = "davidson-rag-pipeline-antigravity"

# Checkpoint dict SHAPE version — distinct from PIPELINE_VERSION (which
# tracks the pipeline's own release). Bumped only when chapter_info's or
# pipeline_state's own field set changes, e.g. this release's provenance
# fields. See migrate_checkpoint_schema_to_v2() below.
CHECKPOINT_SCHEMA_VERSION = "2.0"

# Terminal milestone flags, monotonic: once True, never reset to False by any
# function in this module. Distinct from pipeline_state["pipeline_status"]
# (a single human-readable string) so that "did the corpus hard-gate pass"
# is never inferred by string-matching one mutable field — see CP-06/
# correction I. rag_system_evaluation_completed exists here for forward
# compatibility with a future retrieval/generation evaluator (Phase 5+) but
# no code in this module ever sets it True.
#
# v2.6.4: added corpus_gate_closure_completed — set True only when Stage 8
# (source_lines precision + trust classification, see SKILL.md) actually
# runs to completion. Distinct from corpus_pipeline_completed (Stage 6):
# a chapter can pass Stage 6 without ever having its source-lines
# provenance checked, which is exactly the CORPUS_REVIEW_PENDING gap this
# flag exists to make machine-checkable rather than inferred.
MILESTONE_FLAGS = (
    "corpus_pipeline_completed",
    "advisory_scorecard_completed",
    "rag_system_evaluation_completed",
    "corpus_gate_closure_completed",
)


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def format_markdown_provenance_header(source_path: str, stage_name: str = None) -> str:
    """Standardized top-level HTML comment provenance block for all markdown artifacts."""
    now_iso = _now()
    stage_line = f"\n  stage: \"{stage_name}\"" if stage_name else ""
    return (
        f"<!--\n"
        f"PROVENANCE METADATA:\n"
        f"  skill_name: \"{SKILL_NAME}\"\n"
        f"  skill_version: \"{PIPELINE_VERSION}\"\n"
        f"  generated_at: \"{now_iso}\"\n"
        f"  source_path: \"{source_path}\"{stage_line}\n"
        f"-->\n\n"
    )


def attach_json_provenance(data_dict: dict, source_path: str, stage_name: str = None) -> dict:
    """Attaches top-level _provenance metadata dict to JSON reports and scorecards."""
    prov = {
        "skill_name": SKILL_NAME,
        "skill_version": PIPELINE_VERSION,
        "generated_at": _now(),
        "source_path": str(source_path),
    }
    if stage_name:
        prov["stage"] = stage_name
    data_dict["_provenance"] = prov
    return data_dict


def _md5(path):

    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def checkpoint_path_for(output_dir, prefix):
    return os.path.join(output_dir, f"{prefix}_CHECKPOINT.json")


def save_checkpoint(checkpoint, checkpoint_path):
    """Atomic write: json.dump to a sibling .tmp file, then os.replace() onto
    the real path. os.replace() is atomic on both Windows and POSIX — readers
    (load_checkpoint) always see either the fully-old or fully-new file, never
    a partially-written one, even if the process is killed mid-write."""
    checkpoint["pipeline_state"]["last_checkpoint_written"] = _now()
    # A UNIQUE temp name per write (a shared "<path>.tmp" let two concurrent runs interleave into one temp file),
    # flushed and fsynced before the atomic replace so a crash cannot leave a truncated checkpoint.
    import tempfile
    d = os.path.dirname(os.path.abspath(checkpoint_path))
    fd, tmp_path = tempfile.mkstemp(prefix=os.path.basename(checkpoint_path) + ".", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(checkpoint, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, checkpoint_path)
    except BaseException:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise


def migrate_checkpoint_schema_to_v2(checkpoint):
    """Losslessly migrates chapter_info's old ambiguous single
    `pipeline_version` field to the three explicit v2.6.2 provenance fields
    (see module docstring). Idempotent — a no-op if
    `checkpoint_schema_version` is already present. Never invents a version:
    a checkpoint with no `pipeline_version` key at all (predates v2.4.0's
    version tracking entirely — a real case, see CHANGELOG [2.6.2] /
    25_AI_H) gets the literal string "UNKNOWN" for
    `checkpoint_created_with_pipeline_version`, never a guess.

    Deliberately does NOT touch `stage_completions`, `next_stage_to_run`,
    or `pipeline_status` — this is a metadata rename/restructure only, not
    a stage-order rewind (that remains CP-07's separate, explicit
    `checkpoint_migrate_v2_6_0.py --apply` job). Safe to call
    unconditionally on every load.

    Mutates `checkpoint` in place and also returns it. Returns the same
    object whether or not a migration was actually needed."""
    ci = checkpoint.setdefault("chapter_info", {})
    if ci.get("checkpoint_schema_version") == CHECKPOINT_SCHEMA_VERSION:
        return checkpoint  # already migrated — idempotent no-op

    old_version = ci.pop("pipeline_version", None)
    created_version = old_version if old_version else "UNKNOWN"
    ci.setdefault("checkpoint_created_with_pipeline_version", created_version)
    # last_processed reflects the last version that actually ran a stage —
    # at migration time, that's whatever the checkpoint already claims (its
    # old single field), NOT the installed version; only a genuine future
    # mark_stage_*() call may advance it to the currently-installed version.
    ci.setdefault("last_processed_with_pipeline_version", created_version)
    ci["checkpoint_schema_version"] = CHECKPOINT_SCHEMA_VERSION
    ci.setdefault("migrations_applied", [])

    checkpoint.setdefault("pipeline_state", {}).setdefault("migration_log", []).append({
        "migration_id": "checkpoint-schema-v2.0",
        "action": "migrated ambiguous pipeline_version field to explicit "
                  "checkpoint_created_with_pipeline_version / "
                  "last_processed_with_pipeline_version / checkpoint_schema_version",
        "old_pipeline_version_value": old_version,
        "timestamp": _now(),
    })
    return checkpoint


def check_version_compatibility(checkpoint):
    """Returns a human-readable, non-fatal warning string when this
    checkpoint's last_processed_with_pipeline_version differs from the
    currently-installed PIPELINE_VERSION, or None when they match. A
    version difference is informational only — never raised as an error,
    never treated as corruption, never blocks resume on its own (a missing
    blocking stage still requires the normal stage-order migration/rerun
    policy, independent of this check)."""
    ci = checkpoint.get("chapter_info", {})
    created = ci.get("checkpoint_created_with_pipeline_version", "UNKNOWN")
    last_processed = ci.get("last_processed_with_pipeline_version", "UNKNOWN")
    if last_processed == PIPELINE_VERSION:
        return None
    return (
        f"Checkpoint was created under v{created} and last processed under "
        f"v{last_processed}. Installed pipeline is v{PIPELINE_VERSION}. "
        f"This is a non-fatal notice, not a block — but if a rule/stage "
        f"relevant to this chapter's remaining stages changed between those "
        f"versions (check CHANGELOG.md), consider whether completed stages "
        f"should be reviewed before trusting the final output."
    )


def load_or_create_checkpoint(source_path, output_dir, prefix, ch_num, ch_slug):
    """Call once, at Step 0, before any stage runs.

    Returns (checkpoint, checkpoint_path). If a checkpoint exists but
    source_path's MD5 no longer matches it, the source changed since the
    last run — the stale checkpoint is discarded and a fresh one created
    (pipeline restarts from Stage 1; this is intentional, not a bug: stage
    outputs downstream of a changed source are no longer trustworthy).
    """
    cp_path = checkpoint_path_for(output_dir, prefix)
    current_md5 = _md5(source_path)

    if os.path.exists(cp_path):
        with open(cp_path, encoding="utf-8") as f:
            checkpoint = json.load(f)
        saved_md5 = checkpoint["chapter_info"]["source_md5"]
        if saved_md5 == current_md5:
            migrate_checkpoint_schema_to_v2(checkpoint)
            warning = check_version_compatibility(checkpoint)
            if warning:
                print(f"WARNING: {warning}")
            next_stage = checkpoint["pipeline_state"]["next_stage_to_run"]
            print(f"Checkpoint found -> resuming from Stage {next_stage}")
            return checkpoint, cp_path
        print(f"Source MD5 mismatch ({saved_md5[:8]} -> {current_md5[:8]}) "
              f"— source changed since last checkpoint. Restarting from Stage 1.")
        os.remove(cp_path)

    checkpoint = {
        "chapter_info": {
            "chapter_num": ch_num,
            "chapter_slug": ch_slug,
            "prefix": prefix,
            "source_path": source_path,
            "source_md5": current_md5,
            "output_dir": output_dir,
            "checkpoint_created_with_pipeline_version": PIPELINE_VERSION,
            "last_processed_with_pipeline_version": PIPELINE_VERSION,
            "checkpoint_schema_version": CHECKPOINT_SCHEMA_VERSION,
            "migrations_applied": [],
        },
        "pipeline_state": {
            "last_completed_stage": None,
            "next_stage_to_run": "1",
            "full_run_started": _now(),
            "last_checkpoint_written": None,
            "pipeline_status": "STARTING",
            "corpus_pipeline_completed": False,
            "advisory_scorecard_completed": False,
            "rag_system_evaluation_completed": False,
            "corpus_gate_closure_completed": False,
        },
        "stage_completions": {},
    }
    save_checkpoint(checkpoint, cp_path)
    print(f"New checkpoint created -> {cp_path}")
    return checkpoint, cp_path


def read_checkpoint(output_dir, prefix):
    """v2.6.3 — READ-ONLY checkpoint access. Use this for audits, trust
    classification, diagnostics, tests, inspection of legacy checkpoints,
    and any historical-evidence-preservation use case.

    Guarantees, enforced by construction (this function does nothing else):
    - Never writes to disk (no save_checkpoint call, no os.replace, not
      even a temp file).
    - Never adds fields, never updates timestamps, never records a
      migration_log entry.
    - Never calls migrate_checkpoint_schema_to_v2() or any other mutating
      function — the returned dict is the historical file exactly as
      represented on disk, byte-for-byte round-trippable (json.load's
      normal float/int/key-order behavior aside).
    - A single `open()` + `json.load()` — no intermediate copy step that
      could silently pick up a mutation added later; if this function ever
      needs to touch a helper, that helper must itself be read-only.

    Raises the same exceptions raw `json.load()` would (FileNotFoundError,
    json.JSONDecodeError) — callers that need read-only access to a
    malformed/legacy checkpoint should catch those explicitly rather than
    relying on this function to normalize or repair anything.

    Returns (checkpoint, checkpoint_path), same shape as load_checkpoint(),
    so a caller can freely inspect chapter_info/pipeline_state/
    stage_completions exactly as historically written — including old-shape
    checkpoints that predate the v2.6.2 provenance fields or the v2.0
    schema entirely.
    """
    cp_path = checkpoint_path_for(output_dir, prefix)
    with open(cp_path, encoding="utf-8") as f:
        checkpoint = json.load(f)
    return checkpoint, cp_path


def load_checkpoint_for_run(output_dir, prefix):
    """v2.6.3 — Load a checkpoint for PIPELINE EXECUTION, explicitly
    applying required migrations. Call this at the top of each stage script
    (SKILL.md's per-stage boilerplate) — anywhere the checkpoint is about to
    be mutated and saved via mark_stage_*()/save_checkpoint().

    Applies migrate_checkpoint_schema_to_v2() to the in-memory dict only
    (idempotent, no-op if already current) — found necessary after a real
    mixed-schema bug: a caller that read via the old load_checkpoint() and
    then called mark_stage_complete() ended up with the OLD ambiguous
    `pipeline_version` field still present alongside the NEW
    `last_processed_with_pipeline_version` field mark_stage_complete()
    writes — neither fully old-schema nor fully new-schema. Confirmed on
    Chapter 05's real checkpoint via rerun_stage6_ch05.py (v2.6.2).

    Like the old load_checkpoint(), this does NOT itself write the migrated
    shape back to disk — migration only reaches disk when the caller
    subsequently calls a mark_stage_*()/save_checkpoint() function, same as
    before. For an explicit, disk-persisting migration with backup and a
    dry-run default, use migrate_checkpoint_schema() instead.
    """
    checkpoint, cp_path = read_checkpoint(output_dir, prefix)
    migrate_checkpoint_schema_to_v2(checkpoint)
    return checkpoint, cp_path


def load_checkpoint(output_dir, prefix):
    """Backward-compatible alias for load_checkpoint_for_run() — kept so
    existing call sites (SKILL.md's per-stage boilerplate, one-off
    chapter-specific scripts) do not all need renaming in the same release
    that introduces the explicit API. Unambiguous: this alias ALWAYS
    behaves exactly like load_checkpoint_for_run() (migrates the in-memory
    dict, never writes to disk on its own) — never like read_checkpoint().

    Do not use this for audits, trust classification, diagnostics, tests
    against legacy/malformed checkpoints, or any other read-only use case —
    use read_checkpoint() for those. New pipeline-execution call sites
    should prefer load_checkpoint_for_run() directly; this alias exists for
    compatibility, not as the preferred spelling going forward.
    """
    return load_checkpoint_for_run(output_dir, prefix)


def migrate_checkpoint_schema(checkpoint, checkpoint_path, *, dry_run=True, backup=True):
    """v2.6.3 — Explicit schema migration operation (distinct from the
    implicit, in-memory-only migration load_checkpoint_for_run() performs
    on every call). This is the function to reach for when you actually
    want the v2.0 schema shape PERSISTED to disk, with an audit trail and a
    safety net — e.g. a one-off chapter-specific migration script, or a
    deliberate "upgrade every checkpoint under this directory" pass.

    dry_run=True (default): computes whether a migration is needed and
    returns a report; writes NOTHING to disk, not even a backup. Safe to
    call repeatedly to inspect what would happen.

    dry_run=False: if (and only if) a migration is actually needed
    (checkpoint_schema_version isn't already current), takes a timestamped
    backup of the pre-migration file first (unless backup=False — not
    recommended), then persists the migrated checkpoint via
    save_checkpoint() and logs the action the same way
    migrate_checkpoint_schema_to_v2() always has (migration_log entry).

    `checkpoint` should already be loaded (e.g. via read_checkpoint()) —
    this function mutates it in place, same contract as
    migrate_checkpoint_schema_to_v2(). Returns a result dict:
    {"migrated": bool, "dry_run": bool, "backup_path": str|None,
     "checkpoint_path": str}.
    """
    already_current = (
        checkpoint.get("chapter_info", {}).get("checkpoint_schema_version")
        == CHECKPOINT_SCHEMA_VERSION
    )
    result = {
        "migrated": False,
        "dry_run": dry_run,
        "backup_path": None,
        "checkpoint_path": checkpoint_path,
    }

    if already_current:
        print(f"migrate_checkpoint_schema: {checkpoint_path} already at schema "
              f"v{CHECKPOINT_SCHEMA_VERSION} — no migration needed.")
        return result

    if dry_run:
        print(f"[DRY RUN] migrate_checkpoint_schema: {checkpoint_path} would be migrated "
              f"to schema v{CHECKPOINT_SCHEMA_VERSION}. Re-run with dry_run=False to apply.")
        result["migrated"] = True  # would-be outcome, nothing written
        return result

    if backup:
        import shutil
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_path = f"{checkpoint_path}.pre-schema-migration-{ts}.bak"
        shutil.copyfile(checkpoint_path, backup_path)
        result["backup_path"] = backup_path

    migrate_checkpoint_schema_to_v2(checkpoint)
    save_checkpoint(checkpoint, checkpoint_path)
    result["migrated"] = True
    print(f"migrate_checkpoint_schema: migrated {checkpoint_path} to schema "
          f"v{CHECKPOINT_SCHEMA_VERSION}"
          + (f" (backup: {result['backup_path']})" if result["backup_path"] else ""))
    return result


def should_run_stage(checkpoint, stage_key):
    """Return False (and print why) if stage_key is already COMPLETED."""
    info = checkpoint["stage_completions"].get(stage_key)
    if info and info.get("status") == "COMPLETED":
        print(f"Stage {stage_key} already completed at {info.get('timestamp')} — skipping.")
        return False
    return True


def _require_known_stage(stage_key):
    """CP-01: an unknown stage key must never silently look like pipeline
    completion (the old bug: STAGE_ORDER.index() raised ValueError, was
    caught, and next_stage_to_run was set to None — indistinguishable from a
    chapter that legitimately finished Stage 7). Raise before any checkpoint
    dict mutation or file write happens, so a bad call is a true no-op."""
    if stage_key not in STAGE_ORDER:
        raise ValueError(f"Unknown stage key: {stage_key!r} (not in STAGE_ORDER)")


def _pipeline_status_for(checkpoint, next_stage):
    """CP-06: distinguishes 'corpus hard gates passed' from 'advisory
    scorecard also ran' instead of collapsing both to a bare 'COMPLETED'.
    This sets the human-readable pipeline_status string; the monotonic
    boolean milestone flags (set in mark_stage_complete below) are the
    machine-checkable source of truth per correction I — callers should
    prefer the flags over string-matching this field.

    Deliberately keyed off last_completed_stage, NOT "next_stage is None":
    Stage 7 (advisory) sits after Stage 6 in STAGE_ORDER, so completing
    Stage 6 always has a non-None next_stage ("7") — gating on next_stage
    being None would mean the corpus-safe milestone was never reachable
    until the advisory scorecard also happened to run, which defeats the
    entire point of CP-06 (Stage 6 passing must be visible on its own)."""
    last = checkpoint["pipeline_state"]["last_completed_stage"]
    if last == "8":
        return "CORPUS_GATE_CLOSURE_COMPLETED"
    if last == "7":
        return "ADVISORY_SCORECARD_COMPLETED"
    if last == "6":
        return "CORPUS_PIPELINE_COMPLETED"
    return "IN_PROGRESS"


def _next_stage_after(stage_key):
    idx = STAGE_ORDER.index(stage_key)  # stage_key already validated by caller
    return STAGE_ORDER[idx + 1] if idx + 1 < len(STAGE_ORDER) else None


def _record_execution_provenance(checkpoint, stage_entry):
    """v2.6.2: stamps `executed_with_pipeline_version` on the stage entry
    being written AND advances chapter_info's
    `last_processed_with_pipeline_version` — both only ever set to the
    CURRENTLY-installed PIPELINE_VERSION, at the exact moment a stage
    genuinely executes (never retroactively, never guessed for a historical
    entry that predates this field — see migrate_checkpoint_schema_to_v2,
    which deliberately does NOT add this field to old stage_completions
    entries). Mutates `stage_entry` in place; caller passes the dict it's
    about to store."""
    stage_entry["executed_with_pipeline_version"] = PIPELINE_VERSION
    checkpoint.setdefault("chapter_info", {})["last_processed_with_pipeline_version"] = PIPELINE_VERSION


def _mark_downstream_stale(checkpoint, stage_key):
    """Completing stage k again (a --force re-run, a repair) makes every LATER stage's COMPLETED entry stale: its
    outputs were produced from the previous version of this stage. They become STALE (so should_run_stage re-runs
    them and classify_trust withdraws trust) and the milestone flags are cleared. Normal forward progress never
    triggers this, because later stages are not COMPLETED yet."""
    sc = checkpoint.get("stage_completions", {})
    idx = STAGE_ORDER.index(stage_key)
    staled = []
    for later in STAGE_ORDER[idx + 1:]:
        entry = sc.get(later)
        if isinstance(entry, dict) and entry.get("status") == "COMPLETED":
            entry["status"] = "STALE"
            entry["stale_because"] = f"stage {stage_key} was completed again at {_now()}"
            staled.append(later)
    if staled:
        ps = checkpoint.setdefault("pipeline_state", {})
        for flag in ("corpus_pipeline_completed", "advisory_scorecard_completed", "corpus_gate_closure_completed"):
            if flag in ps:
                ps[flag] = False
        print(f"      [STALE] re-completing stage {stage_key} invalidated: {staled}")
    return staled


def mark_stage_complete(checkpoint, checkpoint_path, stage_key, output_file=None, **stage_metadata):
    """Only ever call this on an ACTUAL PASSING verdict (CP-02 / constraint
    11). A stage whose own logic produced a failing/blocking verdict must
    call mark_stage_blocked() or mark_stage_failed() instead — never this
    function with a failure silently swallowed into stage_metadata."""
    _require_known_stage(stage_key)
    entry = {
        "status": "COMPLETED",
        "timestamp": _now(),
        "output_file": output_file,
        **stage_metadata,
    }
    _record_execution_provenance(checkpoint, entry)
    _mark_downstream_stale(checkpoint, stage_key)
    checkpoint["stage_completions"][stage_key] = entry
    checkpoint["pipeline_state"]["last_completed_stage"] = stage_key
    next_stage = _next_stage_after(stage_key)
    checkpoint["pipeline_state"]["next_stage_to_run"] = next_stage
    checkpoint["pipeline_state"]["pipeline_status"] = _pipeline_status_for(checkpoint, next_stage)
    if stage_key == "6":
        checkpoint["pipeline_state"]["corpus_pipeline_completed"] = True
    if stage_key == "7":
        checkpoint["pipeline_state"]["advisory_scorecard_completed"] = True
    if stage_key == "8":
        checkpoint["pipeline_state"]["corpus_gate_closure_completed"] = True
    save_checkpoint(checkpoint, checkpoint_path)
    print(f"Stage {stage_key} complete. Next: {next_stage}")


def mark_stage_blocked(checkpoint, checkpoint_path, stage_key, output_file=None, **stage_metadata):
    """A stage ran, reached a verdict, and that verdict is a hard-gate
    failure with a documented remediation path (splice-fix, re-tune, manual
    review) — distinct from mark_stage_failed(), where the run itself never
    produced a usable verdict at all. next_stage_to_run is deliberately left
    pointed at stage_key itself (not advanced) so resume logic re-attempts
    this stage, never treats it as done. should_run_stage() already returns
    True for any status other than "COMPLETED", so no change was needed
    there for this to work correctly."""
    _require_known_stage(stage_key)
    entry = {
        "status": "BLOCKED",
        "timestamp": _now(),
        "output_file": output_file,
        **stage_metadata,
    }
    _record_execution_provenance(checkpoint, entry)
    checkpoint["stage_completions"][stage_key] = entry
    checkpoint["pipeline_state"]["next_stage_to_run"] = stage_key
    checkpoint["pipeline_state"]["pipeline_status"] = "BLOCKED"
    save_checkpoint(checkpoint, checkpoint_path)
    print(f"Stage {stage_key} BLOCKED — fix and re-run before proceeding.")


def mark_stage_failed(checkpoint, checkpoint_path, stage_key, output_file=None, **stage_metadata):
    """The run itself did not produce a usable verdict (crash, missing
    required input, unparseable output) — nothing to review, the stage must
    be re-executed from scratch. Kept as a separate function from
    mark_stage_blocked() (rather than a status-string parameter on one
    function) so call sites read unambiguously at the point of use, matching
    mark_stage_complete's existing style."""
    _require_known_stage(stage_key)
    entry = {
        "status": "FAILED",
        "timestamp": _now(),
        "output_file": output_file,
        **stage_metadata,
    }
    _record_execution_provenance(checkpoint, entry)
    checkpoint["stage_completions"][stage_key] = entry
    checkpoint["pipeline_state"]["next_stage_to_run"] = stage_key
    checkpoint["pipeline_state"]["pipeline_status"] = "BLOCKED"
    save_checkpoint(checkpoint, checkpoint_path)
    print(f"Stage {stage_key} FAILED — re-run from scratch.")


def mark_stage_in_progress(checkpoint, checkpoint_path, stage_key, **stage_metadata):
    """Stage started but has not yet reached a verdict — used for Stage 4B's
    existing per-section bookkeeping pattern and now also for any stage
    whose acceptance condition requires a human-adjudication step before it
    can resolve (Stage 4.5d, Stage 4.6's manual path). should_run_stage()
    returns True for this status, same as BLOCKED/FAILED/absent — a stage
    left IN_PROGRESS is never mistaken for done."""
    _require_known_stage(stage_key)
    existing = checkpoint["stage_completions"].get(stage_key, {})
    entry = {
        **existing,
        "status": "IN_PROGRESS",
        "timestamp": _now(),
        **stage_metadata,
    }
    _record_execution_provenance(checkpoint, entry)
    checkpoint["stage_completions"][stage_key] = entry
    save_checkpoint(checkpoint, checkpoint_path)
    print(f"Stage {stage_key} IN_PROGRESS.")


def mark_section_complete(checkpoint, checkpoint_path, stage_key, section_id, **section_metadata):
    """Stage 4B processes files >2000 lines in 500-line sections (rule 7).
    Call this after each section is appended to chunks.md so a crash
    mid-chapter resumes at the next un-done section instead of section 1."""
    entry = checkpoint["stage_completions"].setdefault(
        stage_key, {"status": "IN_PROGRESS", "timestamp": _now(), "sections": {}}
    )
    entry.setdefault("sections", {})[section_id] = {
        "status": "COMPLETED",
        "timestamp": _now(),
        **section_metadata,
    }
    save_checkpoint(checkpoint, checkpoint_path)
    print(f"Section {section_id} complete.")


def record_manual_edit(checkpoint, checkpoint_path, stage_key, file_path, note):
    """Audit trail only — never a validity gate. This pipeline's own rules
    require hand-editing an already-COMPLETED stage's output file: Rule D
    (Stage 4.5 splice-fix a failed chunk directly into chunks.md, no subagent
    re-run) and Rule F (Stage 2 piracy sweep — restore swept clinical content
    directly into REPAIRED_S2.md). A hash-drift *gate* would treat every one
    of those sanctioned edits as corruption and force an unwanted rerun —
    so this function only ever appends a record of what changed and why;
    should_run_stage()/resume logic never reads it and nothing is blocked or
    rerun because of it. Call it immediately after making a Rule D/F-style
    manual edit, so the checkpoint keeps a readable history of hand
    intervention instead of silently going stale.
    """
    entry = checkpoint["stage_completions"].setdefault(
        stage_key, {"status": "COMPLETED", "timestamp": _now()}
    )
    entry.setdefault("manual_edits", []).append({
        "timestamp": _now(),
        "file": os.path.basename(file_path),
        "file_md5_after_edit": _md5(file_path),
        "note": note,
    })
    save_checkpoint(checkpoint, checkpoint_path)
    print(f"Manual edit to {os.path.basename(file_path)} recorded against stage {stage_key}: {note}")


def get_remaining_sections(checkpoint, stage_key, all_section_ids):
    entry = checkpoint["stage_completions"].get(stage_key, {})
    done = set(entry.get("sections", {}).keys())
    remaining = [s for s in all_section_ids if s not in done]
    if done:
        print(f"Stage {stage_key}: {len(done)}/{len(all_section_ids)} sections already done "
              f"-> running {len(remaining)} remaining")
    return remaining
