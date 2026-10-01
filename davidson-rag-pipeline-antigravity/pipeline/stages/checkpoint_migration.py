"""CP-07 — one-shot checkpoint migration for the v2.6.0 STAGE_ORDER insertion
("4.5d" added between "4.5c" and "4.5b").

Why this exists (not in the original evaluation guide, found while writing
IMPLEMENTATION_MAP.md): mark_stage_complete() persists next_stage_to_run as a
literal string snapshot computed from STAGE_ORDER *at the moment each stage
completed*. Inserting a stage into the middle of STAGE_ORDER does not
retroactively correct an already-persisted next_stage_to_run — a checkpoint
that finished under the OLD order and is sitting at a terminal state (e.g.
next_stage_to_run: null) will never pick up the newly inserted stage through
normal resume logic, because SKILL.md's own convention treats a terminal
checkpoint as "done, do not re-run automatically."

Idempotence (correction A): earlier drafts checked `"4.5d" in
stage_completions` as the "already migrated" signal — insufficient, because
before Stage 4.5d has ever actually run for a chapter, that key legitimately
does not exist yet regardless of whether the migration itself was already
applied. This version uses an explicit migration ID recorded in
chapter_info.migrations_applied, checked BEFORE any other logic runs.

Correction A also requires dry-run, backup, and verification behavior — all
implemented below. This module contains pure/testable logic; the CLI wrapper
(checkpoint_migrate_v2_6_0.py, repo root) is a thin argument-parsing shell
around migrate_checkpoint_file().
"""
import json
import os
import shutil
from datetime import datetime, timezone

from pipeline.checkpoint_utils import migrate_checkpoint_schema_to_v2

MIGRATION_ID = "v2.6.0-stage-4.5d-insert"
REACHED_MARKER_STAGE = "4.5c"
REWIND_TARGET_STAGE = "4.5d"
TERMINAL_STATUSES = ("COMPLETED", "CORPUS_PIPELINE_COMPLETED", "ADVISORY_SCORECARD_COMPLETED")


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _backfill_missing_fields(checkpoint):
    """Fields added by the v2.6.0/v2.6.2 checkpoint_utils.py changes that an
    older checkpoint (written before CP-01..CP-06, or before the v2.6.2
    provenance-field rename) won't have yet. Delegates the chapter_info
    provenance rename to checkpoint_utils.migrate_checkpoint_schema_to_v2()
    (single source of truth — v2.6.2 fixed a prior duplication risk here:
    this function used to backfill `migrations_applied` independently of
    that logic) and derives the monotonic milestone flags from
    stage_completions rather than assuming False, so a chapter that already
    legitimately passed Stage 6/7 under the old code doesn't lose that fact
    just because the flag field itself didn't exist yet. Returns True if
    anything changed."""
    changed = False
    ci = checkpoint.setdefault("chapter_info", {})
    if ci.get("checkpoint_schema_version") != "2.0":
        migrate_checkpoint_schema_to_v2(checkpoint)
        changed = True
    if "migrations_applied" not in ci:
        ci["migrations_applied"] = []
        changed = True

    ps = checkpoint.setdefault("pipeline_state", {})
    sc = checkpoint.get("stage_completions", {})
    if "corpus_pipeline_completed" not in ps:
        ps["corpus_pipeline_completed"] = sc.get("6", {}).get("status") == "COMPLETED"
        changed = True
    if "advisory_scorecard_completed" not in ps:
        ps["advisory_scorecard_completed"] = sc.get("7", {}).get("status") == "COMPLETED"
        changed = True
    if "rag_system_evaluation_completed" not in ps:
        ps["rag_system_evaluation_completed"] = False
        changed = True
    return changed


def plan_migration(checkpoint):
    """Pure function: given a loaded checkpoint dict, decide what CP-07
    would do WITHOUT mutating it. Returns a dict describing the plan —
    used identically by dry-run and real-run so the two paths can never
    diverge in what they decide, only in whether they write it."""
    ci = checkpoint.get("chapter_info", {})
    already = MIGRATION_ID in ci.get("migrations_applied", [])
    sc = checkpoint.get("stage_completions", {})
    reached = sc.get(REACHED_MARKER_STAGE, {}).get("status") == "COMPLETED"
    has_4_5d_entry = REWIND_TARGET_STAGE in sc

    plan = {
        "migration_id": MIGRATION_ID,
        "already_migrated": already,
        "reached_4_5c": reached,
        "has_4_5d_entry": has_4_5d_entry,
        "field_backfill_needed": False,
        "rewind_needed": False,
        "action": None,
        "before": {
            "next_stage_to_run": checkpoint.get("pipeline_state", {}).get("next_stage_to_run"),
            "pipeline_status": checkpoint.get("pipeline_state", {}).get("pipeline_status"),
        },
        "after": None,
    }

    if already:
        plan["action"] = "already-migrated"
        plan["after"] = dict(plan["before"])
        return plan

    scratch = json.loads(json.dumps(checkpoint))  # deep copy, never mutate the caller's dict
    plan["field_backfill_needed"] = _backfill_missing_fields(scratch)

    if has_4_5d_entry:
        plan["action"] = "no-rewind-needed"
    elif not reached:
        plan["action"] = "not-yet-reached"
    else:
        plan["rewind_needed"] = True
        plan["action"] = "migrated"
        scratch["pipeline_state"]["next_stage_to_run"] = REWIND_TARGET_STAGE
        if scratch["pipeline_state"].get("pipeline_status") in TERMINAL_STATUSES:
            scratch["pipeline_state"]["pipeline_status"] = "IN_PROGRESS"

    plan["after"] = {
        "next_stage_to_run": scratch["pipeline_state"].get("next_stage_to_run"),
        "pipeline_status": scratch["pipeline_state"].get("pipeline_status"),
    }
    return plan


def apply_migration(checkpoint, plan):
    """Mutates `checkpoint` in place per an already-computed `plan` (from
    plan_migration). Always records the migration ID + a migration_log
    entry, even for not-yet-reached/no-rewind-needed outcomes, so a second
    call is unambiguously idempotent via the marker check alone — not by
    re-deriving whether a rewind was needed, which could drift if the
    chapter's stage_completions changed between calls."""
    if plan["already_migrated"]:
        return checkpoint

    _backfill_missing_fields(checkpoint)

    if plan["rewind_needed"]:
        checkpoint["pipeline_state"]["next_stage_to_run"] = REWIND_TARGET_STAGE
        if checkpoint["pipeline_state"].get("pipeline_status") in TERMINAL_STATUSES:
            checkpoint["pipeline_state"]["pipeline_status"] = "IN_PROGRESS"

    checkpoint["chapter_info"].setdefault("migrations_applied", []).append(MIGRATION_ID)
    checkpoint["pipeline_state"].setdefault("migration_log", []).append({
        "migration_id": MIGRATION_ID,
        "action": plan["action"],
        "before": plan["before"],
        "after": plan["after"],
        "timestamp": _now(),
    })
    return checkpoint


def migrate_checkpoint_file(cp_path, dry_run=True, backup_dir=None):
    """End-to-end CP-07 entry point against a real file on disk.

    dry_run=True (default): computes and returns the plan, writes NOTHING —
    safe to call repeatedly to inspect what would happen.
    dry_run=False: backs up the checkpoint file first (always, even if the
    plan turns out to be a no-op — cheap insurance), applies the migration,
    writes it back, then reloads the written file from disk and verifies
    the on-disk result matches the plan before returning. Raises
    RuntimeError if verification fails rather than returning a
    partially-trusted result.
    """
    with open(cp_path, encoding="utf-8") as f:
        checkpoint = json.load(f)

    plan = plan_migration(checkpoint)
    result = {"path": cp_path, "plan": plan, "dry_run": dry_run,
              "backup_path": None, "verified": None}

    if dry_run:
        return result

    backup_dir = backup_dir or os.path.dirname(cp_path)
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = os.path.join(
        backup_dir, f"{os.path.basename(cp_path)}.migration-backup-{MIGRATION_ID}-{ts}"
    )
    shutil.copyfile(cp_path, backup_path)
    result["backup_path"] = backup_path

    apply_migration(checkpoint, plan)
    tmp_path = cp_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)
    os.replace(tmp_path, cp_path)

    with open(cp_path, encoding="utf-8") as f:
        reloaded = json.load(f)
    verified = (
        MIGRATION_ID in reloaded.get("chapter_info", {}).get("migrations_applied", [])
        and reloaded["pipeline_state"].get("next_stage_to_run") == plan["after"]["next_stage_to_run"]
        and reloaded["pipeline_state"].get("pipeline_status") == plan["after"]["pipeline_status"]
    )
    result["verified"] = verified
    if not verified:
        raise RuntimeError(
            f"CP-07 migration verification FAILED for {cp_path} — on-disk state after "
            f"write does not match the computed plan. Backup preserved at {backup_path}. "
            f"Do not trust this checkpoint until investigated."
        )
    return result
