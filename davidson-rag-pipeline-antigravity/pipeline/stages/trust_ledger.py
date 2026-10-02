"""v2.6.4 — deterministic corpus trust-ledger generator (Corpus-Scale Gate
Closure, MUST-FIX #3, part 2).

Before this module existed, `CORPUS_TRUST_STATUS.md` was a hand-maintained
document: a chapter's row was written (or, in practice, forgotten) by
whoever happened to finish processing it. The post-Chapter-02 generalization
audit confirmed this had already gone stale after only the SECOND canonical
chapter — Chapter 02 passed every gate `stages.corpus_trust.classify_trust()`
checks, but the committed ledger still listed only Chapter 05.

This module makes the ledger a PURE FUNCTION of repository evidence:
`build_corpus_trust_ledger()` scans the corpus, calls `classify_trust()` for
every chapter it finds (real checkpoint-driven chapters and legacy ad hoc
ones alike), and `render_corpus_trust_status()` turns that into the same
markdown shape `CORPUS_TRUST_STATUS.md` has always used. Regenerating the
ledger and diffing it against the committed file is how staleness becomes a
CI-visible test failure instead of a silent, discovered-months-later gap
(see tests/test_trust_ledger_staleness.py).

Discovery is directory-content-driven, not directory-NAME-driven — no
chapter number, slug, or prefix is ever hardcoded here, so a chapter that
hasn't been invented yet needs no code change to be picked up correctly the
day it's processed.
"""
import glob
import json
import os
from datetime import datetime, timezone

from pipeline import checkpoint_utils
from pipeline.stages import corpus_trust
from pipeline.stages.mutation_guard import read_protection_marker, sha256_of_file_or_none
from pipeline.stages.source_lines_precision import build_precision_summary


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _derive_prefix(output_dir):
    """Finds this chapter directory's `{PREFIX}` by looking for any file
    matching a known suffix, in priority order (checkpoint first — the most
    authoritative signal a chapter was processed at all; legacy evidence
    files after, for ad hoc pre-checkpoint chapters). Returns None if the
    directory has no recognizable pipeline output at all (an empty
    not-yet-processed placeholder, e.g. most of `01`-`32`).

    Deliberately glob-based, never a hardcoded chapter number/slug/name —
    this is what makes chapter discovery genuinely chapter-agnostic."""
    suffixes_in_priority_order = [
        "_CHECKPOINT.json",
        "_Stage6_Validation.md",
        "_L1L2_CoverageGaps.md",
        "_RAG_Optimised.md",
        "_RAG_Optimised.md.md",  # 25_AI_H's known double-extension ad hoc bug
    ]
    for suffix in suffixes_in_priority_order:
        matches = sorted(glob.glob(os.path.join(output_dir, f"*{suffix}")))
        if matches:
            basename = os.path.basename(matches[0])
            return basename[: -len(suffix)]
    return None


def _load_json_or_none(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


# v2.6.6 (Fail-Closed Finalization): Stage 8's "unresolved L2 findings"
# count has been recorded under at least three different field names across
# real production chapters' stage_completions["8"] -- 'unresolved_count'
# (Ch02/Ch11/Ch15), 'unresolved_l2_after_adjudication' (Ch10, alongside
# 'unresolved_before_adjudication' and 'unresolved_l1_l2_after_adjudication'),
# and 'l2_findings_unresolved' (Ch13). This is a ledger-only reconciliation
# of checkpoint SUMMARY-field naming -- it is NOT the authoritative source
# of Stage 8 evidence used for real trust classification (that authoritative
# source is always the actual `{PREFIX}_SourceLinesPrecision.json` "results"
# list, via build_precision_summary(), when that file exists -- see
# build_chapter_trust_record() below). This alias list only matters as a
# fallback for a chapter that genuinely has no SourceLinesPrecision.json on
# disk at all. Going forward, Stage 8 should standardize its checkpoint
# summary on 'unresolved_count' as the single canonical field name
# (documented as a known follow-up in
# V2_6_6_FAIL_CLOSED_FINALIZATION_REPORT.md) -- this does not change Stage
# 8's own precision-checking logic in any way.
_STAGE_8_UNRESOLVED_ALIASES = (
    "unresolved_count",
    "unresolved_l2_after_adjudication",
    "unresolved_l1_l2_after_adjudication",
    "l2_findings_unresolved",
)


def _extract_stage_8_unresolved_from_checkpoint(stage_8_entry):
    """Fallback-only extraction of Stage 8 tested/unresolved evidence
    directly from a checkpoint's own stage_completions["8"] summary dict,
    used only when no SourceLinesPrecision.json results file exists on disk
    for this chapter. Returns (tested: bool, unresolved_count: int|None).

    `tested` is True only when the entry is a non-empty dict AND contains at
    least one of the recognized alias keys above -- a non-empty dict with
    none of them (e.g. Chapter 06's real {"l1_unresolved_note": "..."}, or
    Chapter 14's real {} empty dict) is honestly reported as untested, not
    guessed at."""
    if not isinstance(stage_8_entry, dict) or not stage_8_entry:
        return False, None
    for key in _STAGE_8_UNRESOLVED_ALIASES:
        if key in stage_8_entry:
            value = stage_8_entry[key]
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                return True, value
            return True, value  # present but malformed -- classify_trust's _bad_count() will catch it
    return False, None


def marker_hash_mismatches(output_dir, prefix, marker):
    """F10 / 1.20: names of protected files whose current SHA-256 differs from the hash the protection marker
    recorded at finalize. A recorded hash of None means the file did not exist then and is not compared."""
    if not marker:
        return []
    files = {"rag_optimised_sha256": f"{prefix}_RAG_Optimised.md", "chunks_sha256": f"{prefix}_chunks.md",
             "clinical_fidelity_gate_sha256": f"{prefix}_ClinicalFidelityGate.json"}
    bad = []
    for key, name in files.items():
        recorded = marker.get(key)
        if recorded is not None and sha256_of_file_or_none(os.path.join(output_dir, name)) != recorded:
            bad.append(name)
    return bad


def build_chapter_trust_record(output_dir, chapter_dir_name, *, unresolved_completeness_clusters=None):
    """Builds one chapter's trust record from repository evidence in
    `output_dir`. Returns None if no recognizable pipeline output exists in
    this directory at all (a genuinely empty/not-yet-processed placeholder)
    -- such directories are silently excluded from the ledger, not listed
    with a fabricated classification.

    Read-only: every load in this function goes through the sanctioned
    read-only accessors (checkpoint_utils.read_checkpoint /
    corpus_trust.load_checkpoint_for_classification, read_protection_marker,
    plain json.load for gate/precision files) -- never load_checkpoint_for_run(),
    never any function that could migrate or mutate in memory, let alone on
    disk. Building a ledger must never be able to change what it's reporting on.

    v2.6.5: `stage_4_6_review_status` is auto-derived from the checkpoint's
    own `stage_completions["4.6"]["status"]` (no filesystem addition
    needed). `unresolved_completeness_clusters` (Stage 4.7 genuine-gap-vs-
    artifact triage count) has no structured on-disk representation yet as
    of this release — Stage 4.7's SKILL.md block computes SCATTERED/
    SUSPECTED_GAP but does not currently persist which SCATTERED entries
    were actually triaged vs left undetermined. Callers with that evidence
    (e.g. a chapter-specific reassessment) may pass it explicitly; omitting
    it means this classifier does not consider completeness-review status
    for that call, same "None = not evaluated" semantics as every other
    optional evidence parameter here. Documented as a known follow-up
    (Category C) in V2_6_5_EMERGENCY_INTEGRITY_FIX_REPORT.md — a future
    release should extend Stage 4.7's JSON output to track this natively.
    """
    prefix = _derive_prefix(output_dir)
    if prefix is None:
        return None

    checkpoint, _cp_path = corpus_trust.load_checkpoint_for_classification(output_dir, prefix)
    gate = _load_json_or_none(os.path.join(output_dir, f"{prefix}_ClinicalFidelityGate.json"))
    has_stage6 = os.path.exists(os.path.join(output_dir, f"{prefix}_Stage6_Validation.md"))
    has_coverage_gaps = os.path.exists(os.path.join(output_dir, f"{prefix}_L1L2_CoverageGaps.md"))

    precision_data = _load_json_or_none(os.path.join(output_dir, f"{prefix}_SourceLinesPrecision.json"))
    precision_summary = None
    if checkpoint is not None:
        # Only a canonical (checkpointed) chapter is expected to have run
        # Stage 8 at all -- for a legacy ad hoc chapter, precision status
        # genuinely doesn't apply and is left out of its classification
        # inputs, same as it was never asked to run Stage 4.5d either.
        if precision_data is not None and isinstance(precision_data.get("results"), list):
            precision_summary = build_precision_summary(precision_data["results"])
        else:
            # v2.6.6: no SourceLinesPrecision.json results file on disk --
            # fall back to the checkpoint's own stage_completions["8"]
            # summary dict (alias-resolved; see
            # _extract_stage_8_unresolved_from_checkpoint()) rather than
            # unconditionally reporting untested. Still honestly reports
            # untested when that summary itself has no recognized field.
            stage_8_entry = checkpoint.get("stage_completions", {}).get("8")
            tested, unresolved = _extract_stage_8_unresolved_from_checkpoint(stage_8_entry)
            precision_summary = {"tested": tested, "unresolved_count": unresolved,
                                  "chunks_checked": 0, "by_verdict": {}, "bullet_gap_only_count": 0,
                                  "unresolved_chunk_ids": []}

    protection_marker = read_protection_marker(output_dir)

    stage_4_6_review_status = None
    stage_4_6_chunks_reviewed = None
    stage_4_6_total_flagged = None
    if checkpoint is not None:
        stage_4_6_entry = checkpoint.get("stage_completions", {}).get("4.6")
        if stage_4_6_entry is not None:
            stage_4_6_review_status = stage_4_6_entry.get("status")
            # v2.6.6: explicit chunks_reviewed/total_flagged extraction --
            # .get() naturally returns None when a real chapter's checkpoint
            # is genuinely missing either key (e.g. Chapter 02/05 predating
            # this evidence convention); never fabricated or defaulted to 0.
            stage_4_6_chunks_reviewed = stage_4_6_entry.get("chunks_reviewed")
            stage_4_6_total_flagged = stage_4_6_entry.get("total_flagged")

    # Auto-derive from the checkpoint's own Stage 4.7 metadata when present
    # (a chapter reassessment records `unresolved_completeness_clusters` there
    # explicitly — see V2_6_5_EMERGENCY_INTEGRITY_FIX_REPORT.md Part 5); an
    # explicit caller-supplied override always takes priority over this.
    if unresolved_completeness_clusters is None and checkpoint is not None:
        stage_4_7_entry = checkpoint.get("stage_completions", {}).get("4.7")
        if stage_4_7_entry is not None and "unresolved_completeness_clusters" in stage_4_7_entry:
            unresolved_completeness_clusters = stage_4_7_entry["unresolved_completeness_clusters"]

    result = corpus_trust.classify_trust(
        checkpoint, clinical_fidelity_gate=gate,
        has_stage6_validation_file=has_stage6, has_coverage_gaps_file=has_coverage_gaps,
        source_lines_precision_summary=precision_summary, protection_marker=protection_marker,
        stage_4_6_review_status=stage_4_6_review_status,
        unresolved_completeness_clusters=unresolved_completeness_clusters,
        stage_4_6_chunks_reviewed=stage_4_6_chunks_reviewed,
        stage_4_6_total_flagged=stage_4_6_total_flagged,
    )

    changed = marker_hash_mismatches(output_dir, prefix, protection_marker)
    if changed:
        # edited after finalize: the marker no longer vouches for these files
        result = dict(result, classification="CORPUS_REVIEW_PENDING", trusted_for_downstream_use=False,
                      reasons=list(result["reasons"]) + [f"modified after protection marker was written: {', '.join(changed)}"],
                      required_action="Re-run Stage 6/8 and finalize_trusted_chapter.py for this chapter.")

    return {
        "chapter_dir": chapter_dir_name,
        "prefix": prefix,
        "checkpoint_exists": checkpoint is not None,
        "classification": result["classification"],
        "trusted_for_downstream_use": result["trusted_for_downstream_use"],
        "reasons": result["reasons"],
        "required_action": result["required_action"],
        "protection_marker_present": result["protection_marker_present"],
        "semantic_metadata_review_complete": result["semantic_metadata_review_complete"],
        "completeness_review_complete": result["completeness_review_complete"],
        "retrieval_ready": result["retrieval_ready"],
    }


def discover_chapter_dirs(corpus_root):
    """Immediate subdirectories of corpus_root, sorted for deterministic
    ordering. No filtering by name -- every subdirectory is a candidate;
    build_chapter_trust_record() itself decides (via _derive_prefix
    returning None) whether a given directory has anything to report."""
    entries = []
    for name in sorted(os.listdir(corpus_root)):
        full = os.path.join(corpus_root, name)
        if os.path.isdir(full) and not name.startswith("_") and not name.startswith("."):
            entries.append(name)
    return entries


def build_corpus_trust_ledger(corpus_root):
    """Pure(ish) scan+classify pass over the corpus -- the only filesystem
    access is read-only. Returns a ledger dict:
    {"schema_version", "pipeline_version", "generated_at", "chapters": [...]}
    with `chapters` sorted by chapter_dir for stable, reproducible ordering
    (idempotence requirement: rerunning against unchanged evidence produces
    byte-identical `chapters` content, differing only in `generated_at`).
    """
    chapters = []
    for chapter_dir in discover_chapter_dirs(corpus_root):
        output_dir = os.path.join(corpus_root, chapter_dir)
        record = build_chapter_trust_record(output_dir, chapter_dir)
        if record is not None:
            chapters.append(record)
    chapters.sort(key=lambda r: r["chapter_dir"])
    return {
        "schema_version": "1.0",
        "pipeline_version": checkpoint_utils.PIPELINE_VERSION,
        "generated_at": _now(),
        "chapters": chapters,
    }


_RULES_PREAMBLE = """# Corpus Trust Status

**This file is generated by `stages.trust_ledger.build_corpus_trust_ledger()` /
`render_corpus_trust_status()` (v2.6.4) — do not hand-edit.** Regenerate via
`python generate_corpus_trust_ledger.py <corpus_root> --write` after any
chapter's classification-relevant evidence changes (checkpoint, Stage 4.5d
gate, or source-lines precision review). A CI test
(`tests/test_trust_ledger_staleness.py`) regenerates this file in memory and
fails loudly if it no longer matches what's committed here — see that test
before assuming this file is current.

Records per-chapter trust classification per
`stages.corpus_trust.classify_trust()` — the single source of truth for
"which chapters may feed a trusted RAG index." Do not infer trust from a
chapter directory's mere presence of `RAG_Optimised.md`; every classification
below is derived from checkpoint/gate/precision evidence, never from that
file's existence alone.

**Protection markers are informational only.** A `protection_marker_present`
`True` value alongside a classification means only that a
`CORPUS_OUTPUT_PROTECTED.json` mutation-safety marker exists for that
chapter (see `pipeline/stages/mutation_guard.py`) — it is never itself evidence for
or against trust; the classification column is independent of it.

## Approved classification rules

1. No checkpoint is fabricated for a chapter that never had one.
2. A chapter with no checkpoint but with `Stage6_Validation.md` AND
   `L1L2_CoverageGaps.md` on disk is `LEGACY_UNCHECKPOINTED` — an ad hoc,
   non-checkpointed script run reached those stages, but with no verifiable
   checkpoint trail behind that claim.
3. A chapter with a checkpoint that predates Stage 4.5c (no `"4.5c"` key in
   `stage_completions`) is `LEGACY_STALE_CHECKPOINT` /
   `FULL_CANONICAL_RERUN_REQUIRED` — its historical `pipeline_status` (if the
   literal pre-v2.6.0 string `"COMPLETED"`) is NOT equivalent to the current
   `CORPUS_PIPELINE_COMPLETED` milestone and must never be read as such.
4. A chapter with no checkpoint and no Stage6_Validation.md/
   L1L2_CoverageGaps.md evidence is `LEGACY_UNGATED` /
   `INVALID_FOR_TRUSTED_DOWNSTREAM_USE` — ad hoc scripts never reached a
   gated stage at all.
5. **`CORPUS_REVIEW_PENDING`** (v2.6.4): a chapter that otherwise passed
   Stage 6 and the Stage 4.5d clinical fidelity gate, but whose source-lines
   precision review (Stage 8) is either untested or has unresolved findings.
   Requires completing that adjudication before the chapter can reach
   `CORPUS_TESTING_READY` — see `pipeline/stages/source_lines_precision.py`'s
   adjudication mechanism.
6. `CORPUS_TESTING_READY` requires: Stage 6 passed
   (`pipeline_state.corpus_pipeline_completed == True`), the Stage 4.5d
   `ClinicalFidelityGate.json` verdict `== PASS`, AND source-lines precision
   tested with zero unresolved findings.
7. All legacy outputs are preserved as-is for comparison — nothing in these
   directories is deleted or modified by generating this ledger. Legacy
   checkpoints are read via `read_checkpoint()` only — never migrated.
8. Checkpoints predating Stage 4.5c cannot be upgraded to corpus-certified
   status by metadata migration alone — they require a full canonical
   rerun.

## Per-chapter status

"""

_TABLE_HEADER = (
    "| Chapter | Checkpoint? | Classification | Trusted? | Protected? | Reasons |\n"
    "|---|---|---|---|---|---|\n"
)


def _escape_pipe(s):
    return str(s).replace("|", "\\|")


def render_corpus_trust_status(ledger):
    """Renders `ledger` (from build_corpus_trust_ledger()) into the same
    markdown shape CORPUS_TRUST_STATUS.md has always used. Deterministic
    given the same `chapters` list -- the only field that varies run-to-run
    with otherwise-unchanged evidence is `generated_at` in the header line
    below (tests/test_trust_ledger_staleness.py compares structural content,
    not this timestamp, for exactly this reason)."""
    lines = [_RULES_PREAMBLE.rstrip()]
    lines.append(f"\n_Generated {ledger['generated_at']} by pipeline v{ledger['pipeline_version']}._\n")
    lines.append(_TABLE_HEADER.rstrip())
    for r in ledger["chapters"]:
        reasons = "; ".join(r["reasons"])
        lines.append(
            f"| {_escape_pipe(r['chapter_dir'])} | {'Yes' if r['checkpoint_exists'] else 'No'} | "
            f"**{r['classification']}** | {'Yes' if r['trusted_for_downstream_use'] else 'No'} | "
            f"{'Yes' if r['protection_marker_present'] else 'No'} | {_escape_pipe(reasons)} |"
        )
    trusted = [r["chapter_dir"] for r in ledger["chapters"] if r["trusted_for_downstream_use"]]
    lines.append("")
    lines.append(
        f"**{len(trusted)} chapter(s) currently `CORPUS_TESTING_READY`**: "
        + (", ".join(trusted) if trusted else "none.")
    )
    return "\n".join(lines) + "\n"
