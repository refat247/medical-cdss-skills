"""CP-07 — desired behavior: inserting "4.5d" into STAGE_ORDER must not
silently strand an already-terminal checkpoint (real fixture: chapter 05's
actual pre-migration checkpoint). Idempotence via an explicit migration ID
marker (correction A), plus dry-run/backup/verify behavior.
"""
import json
import os

from pipeline.stages.checkpoint_migration import (
    MIGRATION_ID, plan_migration, apply_migration, migrate_checkpoint_file,
)


def test_ch05_real_checkpoint_currently_stranded_without_migration(ch05_checkpoint_shape):
    """Confirms the bug this whole module exists to fix, against the REAL
    chapter 05 checkpoint, not a synthetic stand-in."""
    cp = ch05_checkpoint_shape
    assert cp["pipeline_state"]["next_stage_to_run"] is None
    assert "4.5d" not in cp["stage_completions"]
    assert cp["stage_completions"]["4.5c"]["status"] == "COMPLETED"
    # Per SKILL.md's own documented resume convention: null -> do not
    # auto-resume. Without CP-07, this chapter would never run 4.5d.


def test_plan_migration_rewinds_ch05_shape(ch05_checkpoint_shape):
    plan = plan_migration(ch05_checkpoint_shape)
    assert plan["action"] == "migrated"
    assert plan["rewind_needed"] is True
    assert plan["after"]["next_stage_to_run"] == "4.5d"
    assert plan["after"]["pipeline_status"] == "IN_PROGRESS"
    # plan_migration must not have mutated the caller's dict
    assert ch05_checkpoint_shape["pipeline_state"]["next_stage_to_run"] is None


def test_apply_migration_rewinds_and_records_migration_id(ch05_checkpoint_shape):
    plan = plan_migration(ch05_checkpoint_shape)
    apply_migration(ch05_checkpoint_shape, plan)
    assert ch05_checkpoint_shape["pipeline_state"]["next_stage_to_run"] == "4.5d"
    assert MIGRATION_ID in ch05_checkpoint_shape["chapter_info"]["migrations_applied"]
    # v2.6.2: apply_migration's _backfill_missing_fields also delegates to
    # migrate_checkpoint_schema_to_v2(), which logs its own entry -- so a
    # legacy checkpoint now picks up 2 log entries (schema rename +
    # stage-order rewind), not 1. Check the CP-07 entry specifically exists
    # rather than asserting an exact count coupled to that other migration.
    log = ch05_checkpoint_shape["pipeline_state"]["migration_log"]
    assert any(e["migration_id"] == MIGRATION_ID for e in log)
    assert any(e["migration_id"] == "checkpoint-schema-v2.0" for e in log)


def test_midpipeline_checkpoint_is_left_alone(midpipeline_checkpoint_shape):
    plan = plan_migration(midpipeline_checkpoint_shape)
    assert plan["action"] == "not-yet-reached"
    assert plan["after"]["next_stage_to_run"] == "4a"  # unchanged from before


def test_idempotence_via_explicit_marker_not_key_presence():
    """Correction A: the marker check must be the migrations_applied list,
    not `"4.5d" in stage_completions` -- that key legitimately doesn't
    exist yet even AFTER migration is correctly applied, until Stage 4.5d
    itself actually runs for the chapter. A key-presence check would report
    'not migrated' forever and re-apply on every call."""
    cp = {
        "chapter_info": {"migrations_applied": [MIGRATION_ID]},
        "pipeline_state": {"next_stage_to_run": None, "pipeline_status": "COMPLETED"},
        "stage_completions": {"4.5c": {"status": "COMPLETED"}},  # no "4.5d" key yet
    }
    plan = plan_migration(cp)
    assert plan["action"] == "already-migrated"
    assert plan["after"] == plan["before"]  # confirms no rewind attempted


def test_migrate_checkpoint_file_dry_run_writes_nothing(tmp_path, ch05_checkpoint_shape):
    cp_path = tmp_path / "CHECKPOINT.json"
    cp_path.write_text(json.dumps(ch05_checkpoint_shape), encoding="utf-8")
    before_bytes = cp_path.read_bytes()

    result = migrate_checkpoint_file(str(cp_path), dry_run=True)

    assert cp_path.read_bytes() == before_bytes
    assert result["plan"]["action"] == "migrated"
    assert result["backup_path"] is None
    assert result["verified"] is None


def test_migrate_checkpoint_file_apply_backs_up_writes_and_verifies(tmp_path, ch05_checkpoint_shape):
    cp_path = tmp_path / "CHECKPOINT.json"
    cp_path.write_text(json.dumps(ch05_checkpoint_shape), encoding="utf-8")

    result = migrate_checkpoint_file(str(cp_path), dry_run=False)

    assert result["verified"] is True
    assert os.path.exists(result["backup_path"])
    backup_content = json.loads(open(result["backup_path"], encoding="utf-8").read())
    assert backup_content["pipeline_state"]["next_stage_to_run"] is None  # backup is PRE-migration

    on_disk = json.loads(cp_path.read_text(encoding="utf-8"))
    assert on_disk["pipeline_state"]["next_stage_to_run"] == "4.5d"
    assert MIGRATION_ID in on_disk["chapter_info"]["migrations_applied"]


def test_migrate_checkpoint_file_apply_is_idempotent_on_second_run(tmp_path, ch05_checkpoint_shape):
    cp_path = tmp_path / "CHECKPOINT.json"
    cp_path.write_text(json.dumps(ch05_checkpoint_shape), encoding="utf-8")

    migrate_checkpoint_file(str(cp_path), dry_run=False)
    after_first = cp_path.read_text(encoding="utf-8")

    result2 = migrate_checkpoint_file(str(cp_path), dry_run=False)
    assert result2["plan"]["action"] == "already-migrated"
    assert cp_path.read_text(encoding="utf-8") == after_first  # no second mutation
