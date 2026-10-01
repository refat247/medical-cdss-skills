"""CP-08 — v2.6.4 STAGE_ORDER append ("8" — Corpus Gate Closure). Mirrors
CP-07's test structure (tests/test_cp07_migration.py) for the append case,
using the REAL Chapter 05 and Chapter 02 checkpoint shapes exactly as they
existed the moment before this migration was actually applied for real
against both chapters during this release (see
V2_6_4_CORPUS_SCALE_GATE_CLOSURE_REPORT.md). Loaded from the timestamped
`*.migration-backup-v2.6.4-stage-8-append-*` snapshots CP-08's own
`migrate_checkpoint_file(..., dry_run=False)` took automatically before
mutating either file, rather than the live checkpoint files — which have
since correctly advanced to Stage 8 COMPLETED and would no longer exercise
the "pre-migration, stale/terminal" shape this test module verifies.
"""
import copy
import glob
import json
import os

import pytest

from pipeline.stages.checkpoint_migration_v2_6_4 import (
    MIGRATION_ID, plan_migration, apply_migration, migrate_checkpoint_file,
)

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_real_checkpoint(chapter_dir, prefix):
    """Prefers the frozen pre-migration backup snapshot (see module
    docstring) if one exists; falls back to the live file for an
    environment where the real migration hasn't been applied yet."""
    chapter_path = os.path.join(REPO_DIR, "..", chapter_dir)
    backup_pattern = os.path.join(
        chapter_path, f"{prefix}_CHECKPOINT.json.migration-backup-{MIGRATION_ID}-*"
    )
    backups = sorted(glob.glob(backup_pattern))
    path = backups[0] if backups else os.path.join(chapter_path, f"{prefix}_CHECKPOINT.json")
    path = os.path.abspath(path)
    if not os.path.exists(path):
        pytest.skip(f"Real checkpoint not present at {path} in this environment")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def ch05_real_checkpoint():
    return _load_real_checkpoint("05", "Davidson_25_Ch05_Nutritional_factors_in_disease")


@pytest.fixture
def ch02_real_checkpoint():
    return _load_real_checkpoint("02", "Davidson_25_Ch02_Clinical_therapeutics_and_good_prescribing")


def test_ch05_real_checkpoint_has_stale_next_stage_despite_stage7_completed(ch05_real_checkpoint):
    """Confirms the specific real-world shape this migration must handle:
    Chapter 05's stage_completions already has "7" COMPLETED, but
    pipeline_state.next_stage_to_run is stale ("7", not None or "8") from
    its multi-version manual-retrofit history -- NOT the ordinary terminal
    shape CP-08 might naively assume."""
    cp = ch05_real_checkpoint
    assert cp["stage_completions"]["7"]["status"] == "COMPLETED"
    assert "8" not in cp["stage_completions"]


def test_ch02_real_checkpoint_has_ordinary_terminal_shape(ch02_real_checkpoint):
    cp = ch02_real_checkpoint
    assert cp["stage_completions"]["7"]["status"] == "COMPLETED"
    assert cp["pipeline_state"]["next_stage_to_run"] is None
    assert "8" not in cp["stage_completions"]


def test_plan_migration_rewinds_ch05_shape_to_stage_8(ch05_real_checkpoint):
    cp = copy.deepcopy(ch05_real_checkpoint)
    plan = plan_migration(cp)
    assert plan["action"] == "migrated"
    assert plan["rewind_needed"] is True
    assert plan["after"]["next_stage_to_run"] == "8"
    assert plan["after"]["pipeline_status"] == "IN_PROGRESS"
    # must not have mutated the caller's dict
    assert cp["pipeline_state"]["next_stage_to_run"] == ch05_real_checkpoint["pipeline_state"]["next_stage_to_run"]


def test_plan_migration_rewinds_ch02_shape_to_stage_8(ch02_real_checkpoint):
    cp = copy.deepcopy(ch02_real_checkpoint)
    plan = plan_migration(cp)
    assert plan["action"] == "migrated"
    assert plan["rewind_needed"] is True
    assert plan["after"]["next_stage_to_run"] == "8"


def test_apply_migration_rewinds_and_records_migration_id(ch02_real_checkpoint):
    cp = copy.deepcopy(ch02_real_checkpoint)
    plan = plan_migration(cp)
    apply_migration(cp, plan)
    assert cp["pipeline_state"]["next_stage_to_run"] == "8"
    assert MIGRATION_ID in cp["chapter_info"]["migrations_applied"]
    log = cp["pipeline_state"]["migration_log"]
    assert any(e["migration_id"] == MIGRATION_ID for e in log)


def test_midpipeline_checkpoint_not_yet_at_stage_7_is_left_alone():
    cp = {
        "chapter_info": {"migrations_applied": [], "checkpoint_schema_version": "2.0"},
        "pipeline_state": {"next_stage_to_run": "4a", "pipeline_status": "IN_PROGRESS"},
        "stage_completions": {"1": {"status": "COMPLETED"}, "2": {"status": "COMPLETED"},
                               "3": {"status": "COMPLETED"}},
    }
    plan = plan_migration(cp)
    assert plan["action"] == "not-yet-reached"
    assert plan["after"]["next_stage_to_run"] == "4a"


def test_checkpoint_that_already_has_stage_8_entry_needs_no_rewind():
    cp = {
        "chapter_info": {"migrations_applied": [], "checkpoint_schema_version": "2.0"},
        "pipeline_state": {"next_stage_to_run": None, "pipeline_status": "CORPUS_GATE_CLOSURE_COMPLETED"},
        "stage_completions": {"7": {"status": "COMPLETED"}, "8": {"status": "COMPLETED"}},
    }
    plan = plan_migration(cp)
    assert plan["action"] == "no-rewind-needed"
    assert plan["after"]["next_stage_to_run"] is None


def test_idempotence_via_explicit_marker_not_key_presence():
    cp = {
        "chapter_info": {"migrations_applied": [MIGRATION_ID]},
        "pipeline_state": {"next_stage_to_run": None, "pipeline_status": "COMPLETED"},
        "stage_completions": {"7": {"status": "COMPLETED"}},  # no "8" key yet
    }
    plan = plan_migration(cp)
    assert plan["action"] == "already-migrated"
    assert plan["after"] == plan["before"]


def test_migrate_checkpoint_file_dry_run_writes_nothing(tmp_path, ch02_real_checkpoint):
    cp_path = tmp_path / "CHECKPOINT.json"
    cp_path.write_text(json.dumps(ch02_real_checkpoint), encoding="utf-8")
    before_bytes = cp_path.read_bytes()

    result = migrate_checkpoint_file(str(cp_path), dry_run=True)

    assert cp_path.read_bytes() == before_bytes
    assert result["plan"]["action"] == "migrated"
    assert result["backup_path"] is None
    assert result["verified"] is None


def test_migrate_checkpoint_file_apply_backs_up_writes_and_verifies(tmp_path, ch02_real_checkpoint):
    cp_path = tmp_path / "CHECKPOINT.json"
    cp_path.write_text(json.dumps(ch02_real_checkpoint), encoding="utf-8")

    result = migrate_checkpoint_file(str(cp_path), dry_run=False)

    assert result["verified"] is True
    assert os.path.exists(result["backup_path"])
    backup_content = json.loads(open(result["backup_path"], encoding="utf-8").read())
    assert backup_content["pipeline_state"]["next_stage_to_run"] is None  # backup is PRE-migration

    on_disk = json.loads(cp_path.read_text(encoding="utf-8"))
    assert on_disk["pipeline_state"]["next_stage_to_run"] == "8"
    assert MIGRATION_ID in on_disk["chapter_info"]["migrations_applied"]


def test_migrate_checkpoint_file_apply_is_idempotent_on_second_run(tmp_path, ch02_real_checkpoint):
    cp_path = tmp_path / "CHECKPOINT.json"
    cp_path.write_text(json.dumps(ch02_real_checkpoint), encoding="utf-8")

    migrate_checkpoint_file(str(cp_path), dry_run=False)
    after_first = cp_path.read_text(encoding="utf-8")

    result2 = migrate_checkpoint_file(str(cp_path), dry_run=False)
    assert result2["plan"]["action"] == "already-migrated"
    assert cp_path.read_text(encoding="utf-8") == after_first
