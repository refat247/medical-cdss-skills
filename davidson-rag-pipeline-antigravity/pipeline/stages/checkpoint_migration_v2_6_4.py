"""CP-08 — one-shot checkpoint migration for the v2.6.4 STAGE_ORDER append
("8" — Corpus Gate Closure — added after "7").

Same rewind problem CP-07 (pipeline/stages/checkpoint_migration.py) already solved
for the "4.5d" insertion, applied to an append instead: mark_stage_complete()
persists next_stage_to_run as a literal string snapshot computed from
STAGE_ORDER *at the moment each stage completed*. A chapter that finished
Stage 7 under the OLD STAGE_ORDER (no "8" in it) is sitting at whatever
next_stage_to_run it had at that time — this migration confirmed BOTH real
values that shape actually takes in this corpus:

  - Chapter 02's real checkpoint: next_stage_to_run == None (the ordinary
    terminal case — Stage 7 was the last stage in STAGE_ORDER when it ran).
  - Chapter 05's real checkpoint: next_stage_to_run == "7" even though "7"
    is ALREADY COMPLETED in stage_completions with a real overall_score —
    a genuine, pre-existing inconsistency from that chapter's multi-version
    manual-retrofit history (rerun_stage6_ch05.py updated stage "6"'s and
    "4.5d"'s entries without also correcting pipeline_state.next_stage_to_run/
    last_completed_stage to reflect that "7" had already run earlier). This
    migration does not try to "fix" that historical inconsistency in general
    — it only asks the one question CP-08 cares about ("has stage 7 actually
    completed"), which stage_completions answers reliably regardless of
    whatever pipeline_state.next_stage_to_run happens to say.

A chapter that starts fresh under v2.6.4+ (STAGE_ORDER already includes "8")
needs no migration at all — mark_stage_complete("7", ...) computes
next_stage_to_run="8" directly.

Same idempotence discipline as CP-07 (correction A): the "already migrated"
signal is an explicit migration ID in chapter_info.migrations_applied,
never `"8" in stage_completions` (which legitimately doesn't exist yet even
after migration, until Stage 8 itself actually runs for the chapter).
"""
import json
import os
import shutil
from datetime import datetime, timezone

from pipeline.checkpoint_utils import migrate_checkpoint_schema_to_v2

MIGRATION_ID = "v2.6.4-stage-8-append"
REACHED_MARKER_STAGE = "7"
REWIND_TARGET_STAGE = "8"
TERMINAL_STATUSES = (
    "COMPLETED", "CORPUS_PIPELINE_COMPLETED", "ADVISORY_SCORECARD_COMPLETED",
    "CORPUS_GATE_CLOSURE_COMPLETED",
)


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _backfill_missing_fields(checkpoint):
    """Same responsibility as CP-07's helper of the same name — delegates
    schema-shape migration to checkpoint_utils.migrate_checkpoint_schema_to_v2()
    (single source of truth) and backfills the new v2.6.4 milestone flag
    without assuming False for a chapter that may have already legitimately
    run Stage 8 under a dev build before this migration existed. Returns
    True if anything changed."""
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
    if "corpus_gate_closure_completed" not in ps:
        ps["corpus_gate_closure_completed"] = sc.get("8", {}).get("status") == "COMPLETED"
        changed = True
    return changed


def plan_migration(checkpoint):
    """Pure function — mirrors CP-07's plan_migration() exactly, targeting
    the "8" append instead of the "4.5d" insertion. Never mutates the
    caller's dict."""
    ci = checkpoint.get("chapter_info", {})
    already = MIGRATION_ID in ci.get("migrations_applied", [])
    sc = checkpoint.get("stage_completions", {})
    reached = sc.get(REACHED_MARKER_STAGE, {}).get("status") == "COMPLETED"
    has_8_entry = REWIND_TARGET_STAGE in sc

    plan = {
        "migration_id": MIGRATION_ID,
        "already_migrated": already,
        "reached_7": reached,
        "has_8_entry": has_8_entry,
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

    scratch = json.loads(json.dumps(checkpoint))
    plan["field_backfill_needed"] = _backfill_missing_fields(scratch)

    if has_8_entry:
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
    """Mutates `checkpoint` in place per an already-computed `plan`. Same
    always-record-the-marker discipline as CP-07's apply_migration()."""
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
    """End-to-end CP-08 entry point against a real file on disk. Same
    dry-run/backup/verify contract as CP-07's function of the same name."""
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
            f"CP-08 migration verification FAILED for {cp_path} — on-disk state after "
            f"write does not match the computed plan. Backup preserved at {backup_path}. "
            f"Do not trust this checkpoint until investigated."
        )
    return result
