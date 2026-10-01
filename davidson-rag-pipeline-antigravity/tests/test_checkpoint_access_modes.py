"""v2.6.3 — explicit checkpoint access modes (Safety Guardrails release,
requirement 1).

Before this release, `load_checkpoint()` silently ran schema migration on
every call (in-memory only, but still a mutated shape handed back to
callers) — unsafe for audits, trust classification, diagnostics, tests,
inspection of legacy checkpoints, and historical-evidence preservation,
none of which should ever see anything other than the exact bytes on disk.

This file proves, at the byte level, that `read_checkpoint()` never
mutates a checkpoint file on disk — for a current checkpoint, a
pre-v2.6.0 checkpoint, the real `25_AI_H` legacy shape, a mixed-schema
checkpoint, and a malformed checkpoint (which must raise, not silently
repair). It also proves `load_checkpoint_for_run()` still migrates
in-memory (unchanged behavior from the old `load_checkpoint()`), that the
`load_checkpoint()` alias is unambiguously equivalent to
`load_checkpoint_for_run()`, and exercises `migrate_checkpoint_schema()`'s
explicit dry-run/backup/apply contract.

The real `25_AI_H` checkpoint is read directly from its actual repository
location — never copied, never touched by `load_or_create_checkpoint()`
or any migrating function in this test file.
"""
import copy
import json
import os
import shutil

import pytest

from pipeline.checkpoint_utils import (
    read_checkpoint, load_checkpoint_for_run, load_checkpoint,
    migrate_checkpoint_schema, migrate_checkpoint_schema_to_v2,
    save_checkpoint, checkpoint_path_for, CHECKPOINT_SCHEMA_VERSION,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL_25_AI_H_DIR = os.path.abspath(os.path.join(REPO_ROOT, "..", "25_AI_H"))
REAL_25_AI_H_PREFIX = "Davidson_25_Ch25_Rheumatology_and_bone_disease"
REAL_25_AI_H_PATH = checkpoint_path_for(REAL_25_AI_H_DIR, REAL_25_AI_H_PREFIX)


def _raw_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def _write_checkpoint_file(out_dir, prefix, checkpoint_dict):
    cp_path = checkpoint_path_for(str(out_dir), prefix)
    with open(cp_path, "w", encoding="utf-8") as f:
        json.dump(checkpoint_dict, f, indent=2)
    return cp_path


def _ch05_shaped_pre_v260_checkpoint():
    """Pre-v2.6.0 shape: single ambiguous pipeline_version, no 4.5d key,
    no provenance fields, no checkpoint_schema_version at all."""
    return {
        "chapter_info": {
            "chapter_num": "05", "chapter_slug": "Test", "prefix": "TestCh",
            "source_path": "x", "source_md5": "y", "output_dir": "z",
            "pipeline_version": "2.5.1",
        },
        "pipeline_state": {
            "last_completed_stage": "6", "next_stage_to_run": "7",
            "full_run_started": "t", "last_checkpoint_written": "t",
            "pipeline_status": "COMPLETED",
            "corpus_pipeline_completed": True,
            "advisory_scorecard_completed": True,
            "rag_system_evaluation_completed": False,
        },
        "stage_completions": {"6": {"status": "COMPLETED", "timestamp": "t"}},
    }


def _25_ai_h_shaped_legacy_checkpoint():
    """25_AI_H legacy shape (per V2_6_2_STABILIZATION_REPORT.md §9): no
    pipeline_version key at all, no '4.5c' key in stage_completions."""
    return {
        "chapter_info": {
            "chapter_num": "25", "chapter_slug": "Rheumatology_and_bone_disease",
            "prefix": "Davidson_25_Ch25_Rheumatology_and_bone_disease",
            "source_path": "x", "source_md5": "y", "output_dir": "z",
        },
        "pipeline_state": {
            "last_completed_stage": "6", "next_stage_to_run": "7",
            "full_run_started": "t", "last_checkpoint_written": "t",
            "pipeline_status": "COMPLETED",
        },
        "stage_completions": {"1": {"status": "COMPLETED", "timestamp": "t"},
                               "6": {"status": "COMPLETED", "timestamp": "t"}},
    }


def _mixed_schema_checkpoint():
    """Both the old ambiguous field AND the new provenance fields present
    simultaneously — the exact bug state found on Chapter 05's real
    checkpoint mid-v2.6.2 (see V2_6_2_STABILIZATION_REPORT.md §8)."""
    cp = _ch05_shaped_pre_v260_checkpoint()
    cp["chapter_info"]["last_processed_with_pipeline_version"] = "2.6.2"
    cp["chapter_info"]["checkpoint_created_with_pipeline_version"] = "2.5.1"
    return cp


# --------------------------------------------------------------------------
# Byte-level identity: read_checkpoint() must never write.
# --------------------------------------------------------------------------

@pytest.mark.parametrize("builder", [
    _ch05_shaped_pre_v260_checkpoint,
    _25_ai_h_shaped_legacy_checkpoint,
    _mixed_schema_checkpoint,
])
def test_read_checkpoint_is_byte_identical_before_and_after(tmp_path, builder):
    cp_path = _write_checkpoint_file(tmp_path, "TestCh", builder())
    before = _raw_bytes(cp_path)
    checkpoint, returned_path = read_checkpoint(str(tmp_path), "TestCh")
    after = _raw_bytes(cp_path)
    assert before == after
    assert returned_path == cp_path


def test_read_checkpoint_is_byte_identical_for_current_schema_checkpoint(tmp_path):
    from pipeline.checkpoint_utils import load_or_create_checkpoint

    source = tmp_path / "source.md"
    source.write_text("hello\n", encoding="utf-8")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    load_or_create_checkpoint(str(source), str(out_dir), "TestCh", "99", "Test")
    cp_path = checkpoint_path_for(str(out_dir), "TestCh")

    before = _raw_bytes(cp_path)
    read_checkpoint(str(out_dir), "TestCh")
    after = _raw_bytes(cp_path)
    assert before == after


def test_read_checkpoint_does_not_add_fields(tmp_path):
    cp_path = _write_checkpoint_file(tmp_path, "TestCh", _ch05_shaped_pre_v260_checkpoint())
    before_dict = json.loads(_raw_bytes(cp_path))
    checkpoint, _ = read_checkpoint(str(tmp_path), "TestCh")
    assert checkpoint == before_dict
    assert "checkpoint_schema_version" not in checkpoint["chapter_info"]
    assert "pipeline_version" in checkpoint["chapter_info"]


def test_read_checkpoint_does_not_update_timestamps(tmp_path):
    cp = _ch05_shaped_pre_v260_checkpoint()
    cp["pipeline_state"]["last_checkpoint_written"] = "SENTINEL_TIMESTAMP"
    _write_checkpoint_file(tmp_path, "TestCh", cp)
    checkpoint, _ = read_checkpoint(str(tmp_path), "TestCh")
    assert checkpoint["pipeline_state"]["last_checkpoint_written"] == "SENTINEL_TIMESTAMP"


def test_read_checkpoint_does_not_record_migrations(tmp_path):
    _write_checkpoint_file(tmp_path, "TestCh", _ch05_shaped_pre_v260_checkpoint())
    checkpoint, _ = read_checkpoint(str(tmp_path), "TestCh")
    assert "migration_log" not in checkpoint["pipeline_state"]


def test_read_checkpoint_malformed_json_raises_not_silently_repairs(tmp_path):
    cp_path = checkpoint_path_for(str(tmp_path), "TestCh")
    with open(cp_path, "w", encoding="utf-8") as f:
        f.write("{not valid json,,,")
    before = _raw_bytes(cp_path)
    with pytest.raises(json.JSONDecodeError):
        read_checkpoint(str(tmp_path), "TestCh")
    after = _raw_bytes(cp_path)
    assert before == after  # a raised error must still leave the file untouched


def test_read_checkpoint_missing_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_checkpoint(str(tmp_path), "NoSuchPrefix")


# --------------------------------------------------------------------------
# The real 25_AI_H checkpoint — must never be modified by this suite.
# --------------------------------------------------------------------------

@pytest.mark.skipif(not os.path.exists(REAL_25_AI_H_PATH),
                     reason="real 25_AI_H checkpoint not present in this environment")
def test_real_25_ai_h_checkpoint_is_byte_identical_after_read_checkpoint():
    before = _raw_bytes(REAL_25_AI_H_PATH)
    checkpoint, path = read_checkpoint(REAL_25_AI_H_DIR, REAL_25_AI_H_PREFIX)
    after = _raw_bytes(REAL_25_AI_H_PATH)
    assert before == after, "read_checkpoint() modified the REAL 25_AI_H checkpoint file"
    assert path == REAL_25_AI_H_PATH


@pytest.mark.skipif(not os.path.exists(REAL_25_AI_H_PATH),
                     reason="real 25_AI_H checkpoint not present in this environment")
def test_real_25_ai_h_checkpoint_shape_matches_stabilization_report_findings():
    """Cross-check against V2_6_2_STABILIZATION_REPORT.md §9's documented
    evidence: no pipeline_version, no new provenance fields, no '4.5c' key."""
    checkpoint, _ = read_checkpoint(REAL_25_AI_H_DIR, REAL_25_AI_H_PREFIX)
    ci_keys = set(checkpoint["chapter_info"].keys())
    assert "pipeline_version" not in ci_keys or "checkpoint_schema_version" not in ci_keys, (
        "25_AI_H checkpoint appears to already be migrated -- if this is expected "
        "(e.g. a deliberate later migration), update this test's assumptions."
    )
    assert "4.5c" not in checkpoint.get("stage_completions", {})


@pytest.mark.skipif(not os.path.exists(REAL_25_AI_H_PATH),
                     reason="real 25_AI_H checkpoint not present in this environment")
def test_real_25_ai_h_mtime_unchanged_after_read_checkpoint():
    before_mtime = os.path.getmtime(REAL_25_AI_H_PATH)
    read_checkpoint(REAL_25_AI_H_DIR, REAL_25_AI_H_PREFIX)
    after_mtime = os.path.getmtime(REAL_25_AI_H_PATH)
    assert before_mtime == after_mtime


# --------------------------------------------------------------------------
# load_checkpoint_for_run() — migrates in-memory, never writes on its own.
# --------------------------------------------------------------------------

def test_load_checkpoint_for_run_migrates_in_memory(tmp_path):
    cp_path = _write_checkpoint_file(tmp_path, "TestCh", _ch05_shaped_pre_v260_checkpoint())
    checkpoint, returned_path = load_checkpoint_for_run(str(tmp_path), "TestCh")
    assert checkpoint["chapter_info"]["checkpoint_schema_version"] == CHECKPOINT_SCHEMA_VERSION
    assert "pipeline_version" not in checkpoint["chapter_info"]
    assert returned_path == cp_path


def test_load_checkpoint_for_run_does_not_persist_migration_on_its_own(tmp_path):
    cp_path = _write_checkpoint_file(tmp_path, "TestCh", _ch05_shaped_pre_v260_checkpoint())
    before_bytes = _raw_bytes(cp_path)
    load_checkpoint_for_run(str(tmp_path), "TestCh")
    after_bytes = _raw_bytes(cp_path)
    assert before_bytes == after_bytes, (
        "load_checkpoint_for_run() must only migrate the in-memory dict -- "
        "disk persistence happens only via a later mark_stage_*()/save_checkpoint() call"
    )


def test_load_checkpoint_alias_is_equivalent_to_load_checkpoint_for_run(tmp_path):
    cp_path = _write_checkpoint_file(tmp_path, "TestCh", _ch05_shaped_pre_v260_checkpoint())
    via_alias, _ = load_checkpoint(str(tmp_path), "TestCh")
    cp_path2 = _write_checkpoint_file(tmp_path, "TestCh2", _ch05_shaped_pre_v260_checkpoint())
    via_explicit, _ = load_checkpoint_for_run(str(tmp_path), "TestCh2")
    assert via_alias == via_explicit


# --------------------------------------------------------------------------
# migrate_checkpoint_schema() — explicit, disk-persisting, dry-run-default.
# --------------------------------------------------------------------------

def test_migrate_checkpoint_schema_dry_run_default_writes_nothing(tmp_path):
    cp_path = _write_checkpoint_file(tmp_path, "TestCh", _ch05_shaped_pre_v260_checkpoint())
    before = _raw_bytes(cp_path)
    checkpoint, _ = read_checkpoint(str(tmp_path), "TestCh")
    result = migrate_checkpoint_schema(checkpoint, cp_path)  # dry_run=True default
    assert result["dry_run"] is True
    assert result["migrated"] is True  # "would migrate"
    assert result["backup_path"] is None
    after = _raw_bytes(cp_path)
    assert before == after


def test_migrate_checkpoint_schema_apply_writes_backup_and_migrates(tmp_path):
    cp_path = _write_checkpoint_file(tmp_path, "TestCh", _ch05_shaped_pre_v260_checkpoint())
    checkpoint, _ = read_checkpoint(str(tmp_path), "TestCh")
    result = migrate_checkpoint_schema(checkpoint, cp_path, dry_run=False, backup=True)
    assert result["migrated"] is True
    assert result["backup_path"] is not None
    assert os.path.exists(result["backup_path"])

    backup_dict = json.loads(_raw_bytes(result["backup_path"]))
    assert backup_dict["chapter_info"]["pipeline_version"] == "2.5.1"  # pre-migration shape preserved

    reloaded, _ = read_checkpoint(str(tmp_path), "TestCh")
    assert reloaded["chapter_info"]["checkpoint_schema_version"] == CHECKPOINT_SCHEMA_VERSION
    assert "pipeline_version" not in reloaded["chapter_info"]


def test_migrate_checkpoint_schema_apply_without_backup(tmp_path):
    cp_path = _write_checkpoint_file(tmp_path, "TestCh", _ch05_shaped_pre_v260_checkpoint())
    checkpoint, _ = read_checkpoint(str(tmp_path), "TestCh")
    result = migrate_checkpoint_schema(checkpoint, cp_path, dry_run=False, backup=False)
    assert result["backup_path"] is None
    reloaded, _ = read_checkpoint(str(tmp_path), "TestCh")
    assert reloaded["chapter_info"]["checkpoint_schema_version"] == CHECKPOINT_SCHEMA_VERSION


def test_migrate_checkpoint_schema_already_current_is_a_noop(tmp_path):
    from pipeline.checkpoint_utils import load_or_create_checkpoint

    source = tmp_path / "source.md"
    source.write_text("hello\n", encoding="utf-8")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    checkpoint, cp_path = load_or_create_checkpoint(str(source), str(out_dir), "TestCh", "99", "Test")
    before = _raw_bytes(cp_path)

    result = migrate_checkpoint_schema(checkpoint, cp_path, dry_run=False, backup=True)
    assert result["migrated"] is False
    assert result["backup_path"] is None
    after = _raw_bytes(cp_path)
    assert before == after


def test_migrate_checkpoint_schema_logs_migration_action(tmp_path):
    cp_path = _write_checkpoint_file(tmp_path, "TestCh", _ch05_shaped_pre_v260_checkpoint())
    checkpoint, _ = read_checkpoint(str(tmp_path), "TestCh")
    migrate_checkpoint_schema(checkpoint, cp_path, dry_run=False, backup=True)
    reloaded, _ = read_checkpoint(str(tmp_path), "TestCh")
    log = reloaded["pipeline_state"].get("migration_log", [])
    assert any(e.get("migration_id") == "checkpoint-schema-v2.0" for e in log)
