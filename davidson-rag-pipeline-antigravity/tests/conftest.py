import sys
import os
import json
import copy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture
def fresh_checkpoint(tmp_path):
    """A brand-new checkpoint via the real load_or_create_checkpoint(), so
    tests exercise the actual creation path rather than a hand-built dict
    that could drift from what the function really produces."""
    from pipeline.checkpoint_utils import load_or_create_checkpoint

    source = tmp_path / "source.md"
    source.write_text("hello world\n", encoding="utf-8")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    checkpoint, checkpoint_path = load_or_create_checkpoint(
        source_path=str(source), output_dir=str(out_dir),
        prefix="TestCh", ch_num="99", ch_slug="Test_Chapter",
    )
    return checkpoint, checkpoint_path


@pytest.fixture
def ch05_checkpoint_shape():
    """A copy of the REAL chapter 05 checkpoint (as it existed before any
    Phase 0/1 migration), loaded from the on-disk backup this session took
    before making any code changes. This is the one chapter where CP-07's
    bug is live, not a synthetic stand-in for it."""
    backup_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "..", "05", "_checkpoint_backup_20260729", "CHECKPOINT.json.bak",
    )
    backup_path = os.path.abspath(backup_path)
    if not os.path.exists(backup_path):
        pytest.skip("Chapter 05 external backup directory not present in standalone repository")
    with open(backup_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def midpipeline_checkpoint_shape(ch05_checkpoint_shape):
    """A synthetic checkpoint stopped at Stage 3 -- used to confirm CP-07's
    migration leaves chapters that haven't reached 4.5c yet alone."""
    cp = copy.deepcopy(ch05_checkpoint_shape)
    cp["stage_completions"] = {
        "1": cp["stage_completions"]["1"],
        "2": cp["stage_completions"]["2"],
        "3": cp["stage_completions"]["3"],
    }
    cp["pipeline_state"]["last_completed_stage"] = "3"
    cp["pipeline_state"]["next_stage_to_run"] = "4a"
    cp["pipeline_state"]["pipeline_status"] = "IN_PROGRESS"
    return cp


def make_chunk_block(chunk_id, level, body, topic="Test topic", disease_focus="test_disease",
                      source_lines=None, extra_fields=""):
    src_line = f'source_lines: "{source_lines}"\n' if source_lines else ""
    return (
        f"---\nchunk_id: {chunk_id}\nchunk_level: {level}\n"
        f"semantic_type: clinical_feature\ndisease_focus: {disease_focus}\n"
        f"topic: {topic}\n{src_line}{extra_fields}---\n\n{body}"
    )
