"""v2.6.2 — checkpoint provenance fields (desired behavior, per correction B
established in the Phase 0/1 work: assert what SHOULD happen, not the bug).

Replaces the ambiguous single `chapter_info.pipeline_version` field with
explicit provenance: `checkpoint_created_with_pipeline_version` (when this
checkpoint first came into existence — never overwritten),
`last_processed_with_pipeline_version` (updated every time a real stage
actually runs under the current code), and `checkpoint_schema_version`
("2.0"). A legacy checkpoint's historical creation version must be
preserved, never overwritten with the installed version, and never
invented when genuinely unknown.
"""
import json
import copy

from pipeline.checkpoint_utils import (
    load_or_create_checkpoint, load_checkpoint, mark_stage_complete,
    migrate_checkpoint_schema_to_v2, check_version_compatibility,
    PIPELINE_VERSION, CHECKPOINT_SCHEMA_VERSION,
)


def test_newly_created_checkpoint_has_v2_provenance_fields(fresh_checkpoint):
    checkpoint, _ = fresh_checkpoint
    ci = checkpoint["chapter_info"]
    assert ci["checkpoint_created_with_pipeline_version"] == PIPELINE_VERSION
    assert ci["last_processed_with_pipeline_version"] == PIPELINE_VERSION
    assert ci["checkpoint_schema_version"] == CHECKPOINT_SCHEMA_VERSION
    assert "pipeline_version" not in ci  # old ambiguous field retired for new checkpoints


def test_newly_created_checkpoint_schema_version_is_2_0(fresh_checkpoint):
    checkpoint, _ = fresh_checkpoint
    assert checkpoint["chapter_info"]["checkpoint_schema_version"] == "2.0"


def test_stage_completion_records_executed_with_pipeline_version(fresh_checkpoint):
    checkpoint, checkpoint_path = fresh_checkpoint
    mark_stage_complete(checkpoint, checkpoint_path, "1")
    assert checkpoint["stage_completions"]["1"]["executed_with_pipeline_version"] == PIPELINE_VERSION


def test_mark_stage_complete_updates_last_processed_without_touching_created(fresh_checkpoint):
    checkpoint, checkpoint_path = fresh_checkpoint
    created_before = checkpoint["chapter_info"]["checkpoint_created_with_pipeline_version"]
    mark_stage_complete(checkpoint, checkpoint_path, "1")
    assert checkpoint["chapter_info"]["checkpoint_created_with_pipeline_version"] == created_before
    assert checkpoint["chapter_info"]["last_processed_with_pipeline_version"] == PIPELINE_VERSION


# --- Legacy checkpoint schema migration (Ch05-shaped: has old pipeline_version) ---

def _ch05_shaped_legacy_checkpoint():
    return {
        "chapter_info": {
            "chapter_num": "05", "chapter_slug": "Test", "prefix": "TestCh",
            "source_path": "x", "source_md5": "y", "output_dir": "z",
            "pipeline_version": "2.5.1",
        },
        "pipeline_state": {
            "last_completed_stage": "6", "next_stage_to_run": "7",
            "full_run_started": "t", "last_checkpoint_written": "t",
            "pipeline_status": "CORPUS_PIPELINE_COMPLETED",
            "corpus_pipeline_completed": True,
            "advisory_scorecard_completed": True,
            "rag_system_evaluation_completed": False,
        },
        "stage_completions": {"6": {"status": "COMPLETED", "timestamp": "t"}},
    }


def test_legacy_checkpoint_preserves_historical_creation_version():
    cp = _ch05_shaped_legacy_checkpoint()
    migrate_checkpoint_schema_to_v2(cp)
    assert cp["chapter_info"]["checkpoint_created_with_pipeline_version"] == "2.5.1"


def test_legacy_checkpoint_migration_does_not_overwrite_2_5_1_with_installed_version():
    """The exact failure mode named in the task: do not overwrite Chapter
    05's historical 2.5.1 value and falsely imply every stage ran under
    v2.6.2."""
    cp = _ch05_shaped_legacy_checkpoint()
    migrate_checkpoint_schema_to_v2(cp)
    assert cp["chapter_info"]["checkpoint_created_with_pipeline_version"] == "2.5.1"
    assert cp["chapter_info"]["checkpoint_created_with_pipeline_version"] != PIPELINE_VERSION


def test_legacy_checkpoint_gets_schema_version_2_0():
    cp = _ch05_shaped_legacy_checkpoint()
    migrate_checkpoint_schema_to_v2(cp)
    assert cp["chapter_info"]["checkpoint_schema_version"] == "2.0"


def test_legacy_checkpoint_old_pipeline_version_key_removed_after_migration():
    cp = _ch05_shaped_legacy_checkpoint()
    migrate_checkpoint_schema_to_v2(cp)
    assert "pipeline_version" not in cp["chapter_info"]


def test_legacy_checkpoint_migration_records_migration_log_entry():
    cp = _ch05_shaped_legacy_checkpoint()
    migrate_checkpoint_schema_to_v2(cp)
    log = cp["pipeline_state"].get("migration_log", [])
    assert any(e.get("migration_id") == "checkpoint-schema-v2.0" for e in log)


def test_legacy_checkpoint_migration_is_idempotent():
    cp = _ch05_shaped_legacy_checkpoint()
    migrate_checkpoint_schema_to_v2(cp)
    after_first = copy.deepcopy(cp)
    migrate_checkpoint_schema_to_v2(cp)
    assert cp == after_first  # second call is a no-op


def test_load_checkpoint_also_migrates_schema_not_just_load_or_create(tmp_path):
    """Regression test for a real bug found during this release: a caller
    that reads via load_checkpoint() (not load_or_create_checkpoint()) and
    then calls mark_stage_complete() used to end up with a MIXED schema —
    the old ambiguous 'pipeline_version' field still present alongside the
    new 'last_processed_with_pipeline_version' field mark_stage_complete()
    writes. Confirmed on Chapter 05's real checkpoint via
    rerun_stage6_ch05.py. Fixed by making load_checkpoint() also run the
    schema migration defensively."""
    from pipeline.checkpoint_utils import _md5, checkpoint_path_for, save_checkpoint

    source = tmp_path / "source.md"
    source.write_text("text\n", encoding="utf-8")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    legacy = _ch05_shaped_legacy_checkpoint()
    legacy["chapter_info"]["source_path"] = str(source)
    legacy["chapter_info"]["source_md5"] = _md5(str(source))
    legacy["chapter_info"]["output_dir"] = str(out_dir)
    cp_path = checkpoint_path_for(str(out_dir), "TestCh")
    save_checkpoint(legacy, cp_path)

    checkpoint, checkpoint_path = load_checkpoint(str(out_dir), "TestCh")
    assert checkpoint["chapter_info"]["checkpoint_schema_version"] == "2.0"
    assert "pipeline_version" not in checkpoint["chapter_info"]

    mark_stage_complete(checkpoint, checkpoint_path, "7")
    reloaded, _ = load_checkpoint(str(out_dir), "TestCh")
    assert "pipeline_version" not in reloaded["chapter_info"]  # never resurrected
    assert reloaded["chapter_info"]["checkpoint_created_with_pipeline_version"] == "2.5.1"
    assert reloaded["chapter_info"]["last_processed_with_pipeline_version"] == PIPELINE_VERSION


def test_checkpoint_with_no_historical_version_gets_unknown_not_invented():
    """25_AI_H-shaped: chapter_info has no 'pipeline_version' key at all
    (predates v2.4.0's PIPELINE_VERSION tracking entirely). Must become
    the literal string 'UNKNOWN', never a guessed/invented value."""
    cp = _ch05_shaped_legacy_checkpoint()
    del cp["chapter_info"]["pipeline_version"]
    migrate_checkpoint_schema_to_v2(cp)
    assert cp["chapter_info"]["checkpoint_created_with_pipeline_version"] == "UNKNOWN"


def test_load_or_create_checkpoint_auto_migrates_legacy_schema_on_load(tmp_path):
    source = tmp_path / "source.md"
    source.write_text("text\n", encoding="utf-8")
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    # Simulate an existing legacy (pre-2.6.2-schema) checkpoint on disk.
    from pipeline.checkpoint_utils import _md5, checkpoint_path_for, save_checkpoint
    legacy = _ch05_shaped_legacy_checkpoint()
    legacy["chapter_info"]["source_path"] = str(source)
    legacy["chapter_info"]["source_md5"] = _md5(str(source))
    legacy["chapter_info"]["output_dir"] = str(out_dir)
    cp_path = checkpoint_path_for(str(out_dir), "TestCh")
    save_checkpoint(legacy, cp_path)

    checkpoint, _ = load_or_create_checkpoint(str(source), str(out_dir), "TestCh", "05", "Test")
    assert checkpoint["chapter_info"]["checkpoint_created_with_pipeline_version"] == "2.5.1"
    assert checkpoint["chapter_info"]["checkpoint_schema_version"] == "2.0"
    # MD5 matched -> this is a resume, not a fresh checkpoint -> last_processed
    # is NOT bumped to the installed version just by loading (only a real
    # stage execution should do that, per mark_stage_complete's behavior).
    assert checkpoint["chapter_info"]["last_processed_with_pipeline_version"] == "2.5.1"


# --- Version compatibility warning ---

def test_version_warning_distinguishes_created_processed_installed():
    cp = _ch05_shaped_legacy_checkpoint()
    migrate_checkpoint_schema_to_v2(cp)
    cp["chapter_info"]["last_processed_with_pipeline_version"] = "2.6.0"
    msg = check_version_compatibility(cp)
    assert "2.5.1" in msg
    assert "2.6.0" in msg
    assert PIPELINE_VERSION in msg


def test_version_warning_none_when_everything_matches_installed(fresh_checkpoint):
    checkpoint, _ = fresh_checkpoint
    assert check_version_compatibility(checkpoint) is None


def test_version_difference_does_not_itself_raise_or_block():
    """A version mismatch is informational, never treated as corruption."""
    cp = _ch05_shaped_legacy_checkpoint()
    migrate_checkpoint_schema_to_v2(cp)
    msg = check_version_compatibility(cp)  # must not raise
    assert isinstance(msg, str)
